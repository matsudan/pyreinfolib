from collections.abc import Sequence
from types import TracebackType
from typing import Any, Literal, Self
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from pyreinfolib import enums, exceptions
from pyreinfolib.types import (
    AppraisalReportsResponse,
    CityPlanningAreasAndAreaClassificationResponse,
    CityPlanningRoadsResponse,
    DenselyInhabitedDistrictsResponse,
    DesignatedEmergencyEvacuationSitesResponse,
    DisasterHistoryResponse,
    DisasterRiskAreasResponse,
    DistrictPlansResponse,
    ElementarySchoolDistrictsResponse,
    ExpectedFloodInundationAreasAtMaximumScaleResponse,
    ExpectedStormSurgeInundationAreasResponse,
    ExpectedTsunamiInundationResponse,
    FirePreventionDistrictsAndQuasiFirePreventionDistrictsResponse,
    HighLevelUseDistrictsResponse,
    JuniorHighSchoolDistrictsResponse,
    LandMarketValuePublicationAndResearchPointResponse,
    LandslidePreventionDistrictsResponse,
    LargeScaleDevelopedEmbankmentsResponse,
    LibrariesResponse,
    LiquefactionTendencyBasedOnTopographicalClassificationResponse,
    LocationNormalizationPlansResponse,
    MedicalInstitutionsResponse,
    MunicipalitiesResponse,
    MunicipalOfficesAndMeetingFacilitiesEtcResponse,
    NaturalParkAreasResponse,
    NumberOfPassengersPerStationResponse,
    NurserySchoolsAndKindergartensEtcResponse,
    PopulationProjectionsIn250mGridSquaresResponse,
    RealEstatePricesPointResponse,
    RealEstatePricesResponse,
    SchoolsResponse,
    SedimentDisasterAlertAreasResponse,
    SteepSlopeFailureHazardAreasResponse,
    UseDistrictsResponse,
    WelfareFacilitiesResponse,
)

DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3

# Statuses worth another attempt. 429 is the one the API documents: it publishes no request
# ceiling and instead asks that calls be spaced out, so being throttled is an expected
# outcome rather than a fault. See section 3, Q.3 of
# https://www.reinfolib.mlit.go.jp/help/apiManual/
#
# 404 is deliberately absent. It means the query matched no data, so retrying it would only
# wait to be told the same thing again.
_RETRY_STATUSES = (429, 500, 502, 503, 504)

# Zoom levels a tile endpoint accepts, as data rather than as a type. Most take this range;
# each endpoint that does not passes its own to `_get_tile`.
#
# A range and not a `Literal`: the levels have to be checkable against a value that arrives
# computed. `pyreinfolib.tiles` hands back a `Tile` whose `z` is an `int`, and a `Literal`
# parameter rejects every one of them, which made the documented `client.get_...(*tile)` fail
# to type check while doing nothing about an out-of-range level held in a variable.
_DEFAULT_ZOOM_LEVELS = range(11, 16)

# Statuses whose meaning the API documents. Anything else falls back to `APIError`, which
# still carries the body, so the caller can read the API's own explanation.
#
# 403 is deliberately absent. The API manual does not mention it, and the gateway in front
# of this API uses 401 for a missing or invalid subscription key while reserving 403 for an
# exhausted call quota. Calling it an authentication failure would send the caller off to
# check a key that is fine.
_STATUS_TO_EXCEPTION: dict[int, type[exceptions.APIError]] = {
    401: exceptions.AuthenticationError,
    404: exceptions.NoResultsError,
    429: exceptions.RateLimitError,
}


def _join_codes(codes: Sequence[str] | str | None) -> str | None:
    """Serialize one or more codes into the comma separated form the API expects.

    A bare string (a `StrEnum` member included) is passed through unchanged. Without this,
    forgetting to wrap a single code in a list would silently send `0,7` instead of `07`,
    because `",".join()` treats the string as a sequence of characters.

    Passes `None` through so that an omitted argument can be handed to `_compact` like any
    other. An empty sequence becomes an empty string, which `_compact` then refuses: a caller
    whose list of codes filtered down to nothing is not asking for every code.
    """
    if codes is None:
        return None
    if isinstance(codes, str):
        return codes
    return ",".join(codes)


def _join_unpadded_codes(name: str, codes: Sequence[str] | str | None) -> str | None:
    """Serialize codes the API documents without a leading zero, and refuse padded ones.

    XKT019 asks for `9` where the price endpoints ask for `09` for the same prefecture: its
    manual says to take the code from the published list and strip a leading zero. `09` is
    therefore outside the documented format, and it is refused here rather than sent, because
    a code the API does not recognise comes back as a tile with no features. That reads as
    "no natural parks in this tile" rather than as an argument the API threw away.

    Refused on the manual's word, not on observed behaviour, which is also how `z` is checked.
    """
    joined = _join_codes(codes)
    if joined is None:
        return None

    padded = sorted({code for code in joined.split(",") if len(code) > 1 and code.startswith("0")})
    if padded:
        listed = ", ".join(padded)
        raise ValueError(
            f"`{name}` is written without a leading zero, so {listed} is not a code it takes. "
            f"Drop the zero. Note that `area` on the other endpoints keeps it."
        )

    return joined


def _compact(params: dict[str, Any]) -> dict[str, Any]:
    """Drop the arguments the caller left out, and refuse the ones left blank.

    `None` is how an argument is omitted, and omitting a filter is a supported request: most
    endpoints require nothing beyond a period or a tile, so leaving a filter out widens the
    query on purpose. Which arguments an endpoint cannot do without is its own method's
    business; XIT001, for one, needs at least one of `area`, `city` and `station`.

    A blank value is not another way to omit an argument. It used to be dropped as though it
    were `None`, which meant `city=""` quietly widened a query, a blank required argument
    disappeared from the request altogether, and an empty list of codes read as no filter at
    all. None of the three announced itself.

    Values are compared against `""` rather than tested for truthiness. `x=0` is a valid tile
    coordinate, and a future parameter whose valid values include `0` would otherwise vanish
    from the request with nothing to show why.
    """
    blank = sorted(key for key, value in params.items() if value == "")
    if blank:
        listed = ", ".join(blank)
        raise ValueError(f"Blank value for {listed}. Leave the argument out, or pass `None`, to omit it.")

    return {key: value for key, value in params.items() if value is not None}


class Client:
    def __init__(
        self,
        api_key: str,
        timeout: float | tuple[float, float] = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """
        :param api_key: API key issued for the Real Estate Information Library.
        :param timeout: Request timeout in seconds, passed straight to `requests`.
          A single value applies to both connect and read, or pass a `(connect, read)` tuple.
          It bounds each attempt, not the sequence of retries.
        :param max_retries: How many further attempts a throttled or briefly failing request
          gets. Pass 0 to retry nothing. Waits between attempts grow exponentially, and a
          `Retry-After` header from the API takes precedence over that.
        :raises ValueError: If `api_key` is empty, or `max_retries` is negative.
        """
        # Reject it here rather than on the first request, where an empty or missing key
        # surfaces as a 401 that gives no hint about the actual cause.
        if not api_key:
            raise ValueError("`api_key` must be a non-empty string.")
        if max_retries < 0:
            raise ValueError("`max_retries` must not be negative.")

        self.api_key = api_key
        self.base_url = "https://www.reinfolib.mlit.go.jp/ex-api/external/"
        self.timeout = timeout

        # One session for the whole client, so that a caller walking a tile grid reuses the
        # connection instead of completing a TLS handshake per tile.
        self._session = requests.Session()
        self._session.headers["Ocp-Apim-Subscription-Key"] = api_key
        adapter = HTTPAdapter(
            max_retries=Retry(
                total=max_retries,
                status_forcelist=_RETRY_STATUSES,
                backoff_factor=1.0,
                # Hand the exhausted response back rather than raising, so that `_get` can
                # translate it. urllib3 would otherwise raise, requests would wrap that in
                # `RetryError`, and a request throttled to the last attempt would reach the
                # caller as `TransportError` instead of `RateLimitError`.
                raise_on_status=False,
            )
        )
        # Both schemes, although the API is https only. `base_url` is a public attribute, so
        # pointing a client at a local double over http is possible, and retrying is a
        # property of the client rather than of the scheme it happens to be talking over.
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

    def close(self) -> None:
        """Release the connection pool.

        Not needed for correctness, but a client left open holds its sockets until it is
        garbage collected, which surfaces as a `ResourceWarning`.
        """
        self._session.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Issue a GET against `endpoint` and return the decoded JSON body.

        `Any`, deliberately, and it is the public method's annotation that says what the body
        is. `r.json()` returns `Any` and nothing here inspects the result, so a `dict[str, Any]`
        here would be a claim this method has not checked, and every caller would then need a
        `cast` to say the same thing again. The narrowing belongs where the endpoint is known.

        Note that the types in `pyreinfolib.types` are a static claim either way: no response
        is validated against them.

        :raises TransportError: If no response was obtained.
        :raises AuthenticationError: If the API key was missing or rejected.
        :raises NoResultsError: If the query matched no data.
        :raises RateLimitError: If the API key sent too many requests.
        :raises InvalidResponseError: If the body was not valid JSON.
        :raises APIError: For any other error status.
        """
        api_url = urljoin(self.base_url, endpoint)

        # Each failure mode gets its own `try`. Wrapping the whole exchange in one block
        # would have to re-derive which stage failed from the exception type, which is how
        # the previous version came to dereference a `response` that connection errors and
        # timeouts do not have.
        try:
            r = self._session.get(api_url, params=params, timeout=self.timeout)
        except requests.RequestException as e:
            raise exceptions.TransportError(f"Request to {api_url} failed: {e}") from e

        if not r.ok:
            error = _STATUS_TO_EXCEPTION.get(r.status_code, exceptions.APIError)
            raise error(
                f"{r.status_code} {r.reason} for {r.url}: {r.text}",
                status_code=r.status_code,
                response_body=r.text,
                url=r.url,
            )

        try:
            return r.json()
        except requests.exceptions.JSONDecodeError as e:
            raise exceptions.InvalidResponseError(
                f"Response from {r.url} was not valid JSON: {e}",
                status_code=r.status_code,
                response_body=r.text,
                url=r.url,
            ) from e

    def _get_tile(
        self,
        endpoint: str,
        z: int,
        x: int,
        y: int,
        params: dict[str, Any] | None = None,
        *,
        zoom_levels: range = _DEFAULT_ZOOM_LEVELS,
    ) -> Any:
        """Issue a GET against an endpoint addressed by XYZ tile coordinates.

        Most of the published API is addressed this way: `response_format`, `z`, `x` and `y`
        are all these endpoints have in common, and many accept nothing else. Keeping the
        shared part here leaves each public method as its docstring plus the handful of
        parameters that are actually its own.

        `params` is passed as a dict rather than as keyword arguments because two of the
        keys the API expects, `from` and `to`, are Python keywords.

        The zoom level is checked here rather than in each public method. 32 of the API's 35
        endpoints are addressed by tile, and a check that lives in the shared helper cannot be
        left out of one of them.

        :param endpoint: Endpoint id, e.g. `XKT015`.
        :param z: Zoom level (scale).
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param params: Any further query parameters, keyed as the API expects them.
        :param zoom_levels: The levels this endpoint accepts.
        :return: The decoded JSON body.
        :raises ValueError: If `z` is not a level the endpoint accepts.
        """
        if z not in zoom_levels:
            raise ValueError(f"`z` must be between {zoom_levels.start} and {zoom_levels[-1]} for {endpoint}, got {z}.")

        # GeoJson rather than PBF: PBF would need a decoder, and a binary vector tile is not
        # what a Python caller expecting a dict is after.
        tile_params: dict[str, Any] = {"response_format": "geojson", "z": z, "x": x, "y": y}

        # Merged so that the shared keys win. A caller has no reason to override them -- it
        # already passes the coordinates as arguments -- so a collision means a typo in the
        # `params` dict, and silently honouring it would request the wrong tile.
        return self._get(endpoint, _compact((params or {}) | tile_params))

    def get_real_estate_prices(
        self,
        year: int,
        price_classification: enums.PriceClassification | None = None,
        quarter: Literal[1, 2, 3, 4] | None = None,
        area: str | None = None,
        city: str | None = None,
        station: str | None = None,
        language: Literal["ja", "en"] | None = None,
    ) -> RealEstatePricesResponse:
        """Get real estate prices.

        Takes a place as well as a period: at least one of `area`, `city` and `station` is
        required. There is no whole-country query.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi4 for details.
        :param price_classification: Price classification.
          If not specified, both real estate transaction prices and contract prices.
        :param year: Transaction period (Year).
        :param quarter: Transaction period (Quarter). 1: Jan.~Mar. 2: Apr.~Jun. 3: Jul.~Sep. 4: Oct.~Dec.
        :param area: Prefecture code. See https://nlftp.mlit.go.jp/ksj/gml/codelist/PrefCd.html
        :param city: Municipality code.
        :param station: Station code. See https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-v3_1.html
        :param language: `ja` or `en`. If not specified, `ja`.
        :return: Real estate prices.
        :raises ValueError: If `area`, `city` and `station` are all omitted, or an argument is
          blank. Leave an argument out instead, to omit it.
        :raises NoResultsError: If no transaction matches the given period and area.
        """
        params = _compact(
            {
                "year": year,
                "priceClassification": price_classification,
                "quarter": quarter,
                "area": area,
                "city": city,
                "station": station,
                "language": language,
            }
        )

        # Refused on the manual's word, as `z` and a padded code are. Its parameter table marks
        # all three of these required unless one of the other two is given, and says nothing
        # about what a query carrying none of them returns.
        #
        # After `_compact`, so that `city=""` is reported as the blank it is. A key is present
        # here only if the caller passed a non-`None` value for it.
        if not {"area", "city", "station"} & params.keys():
            raise ValueError(
                "At least one of `area`, `city` and `station` is required. XIT001 takes no "
                "query for the whole country, so `year` on its own is not one it documents."
            )

        return self._get("XIT001", params)

    def get_municipalities(self, area: str, language: Literal["ja", "en"] | None = None) -> MunicipalitiesResponse:
        """Get municipality (city/ward/town/village) list.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi5 for details.
        :param area: Prefecture code. See https://nlftp.mlit.go.jp/ksj/gml/codelist/PrefCd.html
        :param language: `ja` or `en`. If not specified, `ja`.
        :return: Municipality list.
        :raises ValueError: If `area` is blank.
        :raises NoResultsError: If the prefecture code matches no municipality.
        """
        params = _compact({"area": area, "language": language})

        return self._get("XIT002", params)

    def get_appraisal_reports(self, year: int, area: str, division: enums.UseDivision) -> AppraisalReportsResponse:
        """Get real estate appraisal reports.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi6 for details.
        :param year: Date of value.
        :param area: Prefecture code.
        :param division: Use division.
        :return: Real estate appraisal reports.
        :raises ValueError: If `area` is blank.
        :raises NoResultsError: If no appraisal report matches the given year and area.
        """
        # Through `_compact` although nothing here is optional, so that a blank `area` is
        # refused rather than sent as `area=`, which is what this method did on its own.
        params = _compact({"year": year, "area": area, "division": division})

        return self._get("XCT001", params)

    def get_real_estate_prices_point(
        self,
        z: int,
        x: int,
        y: int,
        period_from: int,
        period_to: int,
        price_classification: enums.PriceClassification | None = None,
        land_type_code: Sequence[enums.LandTypeCode] | enums.LandTypeCode | None = None,
    ) -> RealEstatePricesPointResponse:
        """Get real estate prices point.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi7 for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param period_from: Transaction period from. Format: YYYYN. e.g. 20241
        :param period_to: Transaction period to. Format: YYYYN. e.g. 20242
        :param price_classification: Price classification.
          If not specified, both real estate transaction prices and contract prices.
        :param land_type_code: One land type code, or a sequence of them.
          See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi7
        :return: Real estate prices point. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15, or `land_type_code` is empty.
        """
        return self._get_tile(
            "XPT001",
            z,
            x,
            y,
            {
                "from": period_from,
                "to": period_to,
                "priceClassification": price_classification,
                "landTypeCode": _join_codes(land_type_code),
            },
        )

    def get_land_market_value_publication_and_research_point(
        self,
        z: int,
        x: int,
        y: int,
        year: int,
        price_classification: enums.LandPriceClassification | None = None,
        use_category_code: Sequence[enums.UseDivision] | enums.UseDivision | None = None,
    ) -> LandMarketValuePublicationAndResearchPointResponse:
        """Get land market value publication (地価公示) and land market value research
        (地価調査) point.

        Both surveys are published on this endpoint. `price_classification` selects one, or
        leave it unset for both. The publication values market values of standard sites; the
        research values the standard sites published by prefectural governments.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi8 for details.
        :param z: Zoom level (scale). 13 ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param year: target year.
        :param price_classification: Land price classification. Note that this is
          `LandPriceClassification`, a different code table from the `PriceClassification`
          the real estate price endpoints take. If not specified, both the publication and
          the prefectural research.
        :param use_category_code: One use division code, or a sequence of them.
          See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi8
        :return: Land market value publication and land market value research point.
          (Response format: GeoJson)
        :raises ValueError: If `z` is not between 13 and 15, or `use_category_code` is empty.
        """
        return self._get_tile(
            "XPT002",
            z,
            x,
            y,
            {
                "year": year,
                "priceClassification": price_classification,
                "useCategoryCode": _join_codes(use_category_code),
            },
            # Narrower than the other tile endpoints, which start at 11.
            zoom_levels=range(13, 16),
        )

    def get_city_planning_areas_and_area_classification(
        self, z: int, x: int, y: int
    ) -> CityPlanningAreasAndAreaClassificationResponse:
        """Get city planning areas (都市計画区域) and area classification (区域区分).

        Area classification is the division of a city planning area into an urbanization
        promotion area and an urbanization control area.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt001/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: City planning areas and area classification. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT001", z, x, y)

    def get_use_districts(self, z: int, x: int, y: int) -> UseDistrictsResponse:
        """Get use districts (用途地域).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt002/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Use districts. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT002", z, x, y)

    def get_location_normalization_plans(self, z: int, x: int, y: int) -> LocationNormalizationPlansResponse:
        """Get location normalization plans (立地適正化計画).

        A municipality's plan under the Act on Special Measures Concerning Urban Renaissance
        for guiding housing and urban services into designated areas, so that the city stays
        serviceable as its population falls. The response carries the plan area, and the
        residence and urban function areas it guides into.

        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt003/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Location normalization plans. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT003", z, x, y)

    def get_elementary_school_districts(
        self,
        z: int,
        x: int,
        y: int,
        administrative_area_code: Sequence[str] | str | None = None,
    ) -> ElementarySchoolDistrictsResponse:
        """Get elementary school districts (小学校区).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt004/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param administrative_area_code: One municipality code, or a sequence of them.
          Format: NNNNN. The same code table the price endpoints spell `city`.
          See https://nlftp.mlit.go.jp/ksj/gml/codelist/AdminiBoundary_CD.xlsx
          If not specified, the whole tile.
        :return: Elementary school districts. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15, or `administrative_area_code`
          is empty.
        """
        return self._get_tile(
            "XKT004",
            z,
            x,
            y,
            {"administrativeAreaCode": _join_codes(administrative_area_code)},
        )

    def get_junior_high_school_districts(
        self,
        z: int,
        x: int,
        y: int,
        administrative_area_code: Sequence[str] | str | None = None,
    ) -> JuniorHighSchoolDistrictsResponse:
        """Get junior high school districts (中学校区).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt005/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param administrative_area_code: One municipality code, or a sequence of them.
          Format: NNNNN. The same code table the price endpoints spell `city`.
          See https://nlftp.mlit.go.jp/ksj/gml/codelist/AdminiBoundary_CD.xlsx
          If not specified, the whole tile.
        :return: Junior high school districts. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15, or `administrative_area_code`
          is empty.
        """
        return self._get_tile(
            "XKT005",
            z,
            x,
            y,
            {"administrativeAreaCode": _join_codes(administrative_area_code)},
        )

    def get_schools(self, z: int, x: int, y: int) -> SchoolsResponse:
        """Get schools (学校).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt006/ for details.
        :param z: Zoom level (scale). 13 ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Schools. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 13 and 15.
        """
        return self._get_tile("XKT006", z, x, y, zoom_levels=range(13, 16))

    def get_nursery_schools_and_kindergartens_etc(
        self, z: int, x: int, y: int
    ) -> NurserySchoolsAndKindergartensEtcResponse:
        """Get nursery schools and kindergartens etc. (保育園・幼稚園等).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt007/ for details.
        :param z: Zoom level (scale). 13 ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Nursery schools and kindergartens etc. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 13 and 15.
        """
        return self._get_tile("XKT007", z, x, y, zoom_levels=range(13, 16))

    def get_medical_institutions(self, z: int, x: int, y: int) -> MedicalInstitutionsResponse:
        """Get medical institutions (医療機関).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt010/ for details.
        :param z: Zoom level (scale). 13 ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Medical institutions. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 13 and 15.
        """
        return self._get_tile("XKT010", z, x, y, zoom_levels=range(13, 16))

    def get_welfare_facilities(
        self,
        z: int,
        x: int,
        y: int,
        administrative_area_code: Sequence[str] | str | None = None,
        welfare_facility_class_code: Sequence[str] | str | None = None,
        welfare_facility_middle_class_code: Sequence[str] | str | None = None,
        welfare_facility_minor_class_code: Sequence[str] | str | None = None,
    ) -> WelfareFacilitiesResponse:
        """Get welfare facilities (福祉施設).

        The three class codes are one nested classification at three levels of detail, and
        they are `str` rather than enums. Two of the seven major classes have no published
        English name -- 身体障害者社会参加支援施設 and 母子・父子福祉施設 rest on the two
        welfare acts that the Japanese Law Translation database does not carry -- and an enum
        naming five of seven would leave the caller mixing members with bare strings for the
        same argument. `area` and `city` are `str` for the same reason.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt011/ for details.
        :param z: Zoom level (scale). 13 ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param administrative_area_code: One municipality code, or a sequence of them.
          Format: NNNNN. The same code table the price endpoints spell `city`.
          See https://nlftp.mlit.go.jp/ksj/gml/codelist/AdminiBoundary_CD.xlsx
          If not specified, the whole tile.
        :param welfare_facility_class_code: One major class code, or a sequence of them.
          Format: NN. See
          https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMajorClassificationCode.html
          If not specified, every class.
        :param welfare_facility_middle_class_code: One middle class code, or a sequence of
          them. Format: NNNN. See
          https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMiddleClassificationCode.html
          If not specified, every class.
        :param welfare_facility_minor_class_code: One minor class code, or a sequence of
          them. Format: NNNNNN. See
          https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMinorClassificationCode.html
          If not specified, every class.
        :return: Welfare facilities. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 13 and 15, or a code argument is empty.
        """
        return self._get_tile(
            "XKT011",
            z,
            x,
            y,
            {
                "administrativeAreaCode": _join_codes(administrative_area_code),
                "welfareFacilityClassCode": _join_codes(welfare_facility_class_code),
                "welfareFacilityMiddleClassCode": _join_codes(welfare_facility_middle_class_code),
                "welfareFacilityMinorClassCode": _join_codes(welfare_facility_minor_class_code),
            },
            zoom_levels=range(13, 16),
        )

    def get_population_projections_in_250m_grid_squares(
        self, z: int, x: int, y: int
    ) -> PopulationProjectionsIn250mGridSquaresResponse:
        """Get future population estimates by 250m mesh (将来推計人口250mメッシュ).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt013/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Future population estimates by 250m mesh. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT013", z, x, y)

    def get_fire_prevention_districts_and_quasi_fire_prevention_districts(
        self, z: int, x: int, y: int
    ) -> FirePreventionDistrictsAndQuasiFirePreventionDistrictsResponse:
        """Get fire prevention districts and quasi-fire prevention districts (防火・準防火地域).

        Districts a city plan designates, within which the Building Standards Act restricts
        how a building may be constructed so that fire does not spread. A fire prevention
        district is the stricter of the two.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt014/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Fire prevention districts and quasi-fire prevention districts.
          (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT014", z, x, y)

    def get_number_of_passengers_per_station(
        self,
        z: int,
        x: int,
        y: int,
    ) -> NumberOfPassengersPerStationResponse:
        """Get number of passengers per station.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt015/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Number of passengers per station. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT015", z, x, y)

    def get_disaster_risk_areas(
        self,
        z: int,
        x: int,
        y: int,
        administrative_area_code: Sequence[str] | str | None = None,
    ) -> DisasterRiskAreasResponse:
        """Get disaster risk areas (災害危険区域).

        A disaster risk area is one a local government has designated by ordinance as
        frequently endangered by tidal waves, high tide or flooding, and where it therefore
        restricts building.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt016/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param administrative_area_code: One municipality code, or a sequence of them.
          Format: NNNNN. The same code table the price endpoints spell `city`.
          Note that this endpoint documents it as the *representative* municipality of an
          area, so an area spanning several municipalities carries only one of them.
          See https://nlftp.mlit.go.jp/ksj/gml/codelist/AdminiBoundary_CD.xlsx
          If not specified, the whole tile.
        :return: Disaster risk areas. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15, or `administrative_area_code`
          is empty.
        """
        return self._get_tile(
            "XKT016",
            z,
            x,
            y,
            {"administrativeAreaCode": _join_codes(administrative_area_code)},
        )

    def get_libraries(
        self,
        z: int,
        x: int,
        y: int,
        administrative_area_code: Sequence[str] | str | None = None,
    ) -> LibrariesResponse:
        """Get libraries (図書館).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt017/ for details.
        :param z: Zoom level (scale). 13 ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param administrative_area_code: One municipality code, or a sequence of them.
          Format: NNNNN. The same code table the price endpoints spell `city`.
          See https://nlftp.mlit.go.jp/ksj/gml/codelist/AdminiBoundary_CD.xlsx
          If not specified, the whole tile.
        :return: Libraries. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 13 and 15, or `administrative_area_code`
          is empty.
        """
        return self._get_tile(
            "XKT017",
            z,
            x,
            y,
            {"administrativeAreaCode": _join_codes(administrative_area_code)},
            zoom_levels=range(13, 16),
        )

    def get_municipal_offices_and_meeting_facilities_etc(
        self, z: int, x: int, y: int
    ) -> MunicipalOfficesAndMeetingFacilitiesEtcResponse:
        """Get municipal offices and public meeting facilities etc. (市区町村役場及び集会施設等).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt018/ for details.
        :param z: Zoom level (scale). 13 ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Municipal offices and public meeting facilities etc. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 13 and 15.
        """
        return self._get_tile("XKT018", z, x, y, zoom_levels=range(13, 16))

    def get_natural_park_areas(
        self,
        z: int,
        x: int,
        y: int,
        prefecture_code: Sequence[str] | str | None = None,
        district_code: Sequence[str] | str | None = None,
    ) -> NaturalParkAreasResponse:
        """Get natural park areas (自然公園地域).

        Natural parks are national parks, quasi-national parks and prefectural natural parks,
        each divided into special areas and ordinary areas.

        Both filters here are written without a leading zero, unlike `area` elsewhere: this
        endpoint asks for `9`, not `09`. A padded code raises `ValueError`.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt019/ for details.
        :param z: Zoom level (scale). 9 (prefecture) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param prefecture_code: One prefecture code, or a sequence of them. 1 (Hokkaido) ~
          47 (Okinawa), with no leading zero. See
          https://nlftp.mlit.go.jp/ksj/gml/codelist/PrefCd.html
          If not specified, the whole tile.
        :param district_code: One subprefecture code, or a sequence of them, with no leading
          zero. See https://nlftp.mlit.go.jp/ksj/gml/codelist/SubprefectureNameCd.html
          If not specified, the whole tile.
        :return: Natural park areas. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 9 and 15, or a code argument is empty or
          carries a leading zero.
        """
        return self._get_tile(
            "XKT019",
            z,
            x,
            y,
            {
                "prefectureCode": _join_unpadded_codes("prefecture_code", prefecture_code),
                "districtCode": _join_unpadded_codes("district_code", district_code),
            },
            # Wider than the rest, which start at 11.
            zoom_levels=range(9, 16),
        )

    def get_landslide_prevention_districts(
        self,
        z: int,
        x: int,
        y: int,
        prefecture_code: Sequence[str] | str | None = None,
        administrative_area_code: Sequence[str] | str | None = None,
    ) -> LandslidePreventionDistrictsResponse:
        """Get landslide prevention districts (地すべり防止地区).

        An area where the Landslide Prevention Act restricts work that could induce a
        landslide. The Act calls it a 地すべり防止区域, `landslide prevention area`, while this
        method follows the API's dataset name, 地すべり防止地区.

        Note that `prefecture_code` here keeps its leading zero -- `09`, not the `9` that
        XKT019 asks for. The two endpoints document the same code table differently.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt021/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param prefecture_code: One prefecture code, or a sequence of them. Format: NN, so
          `09` rather than `9`. See https://nlftp.mlit.go.jp/ksj/gml/codelist/PrefCd.html
          If not specified, the whole tile.
        :param administrative_area_code: One municipality code, or a sequence of them.
          Format: NNNNN. The same code table the price endpoints spell `city`.
          See https://nlftp.mlit.go.jp/ksj/gml/codelist/AdminiBoundary_CD.xlsx
          If not specified, the whole tile.
        :return: Landslide prevention districts. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15, or a code argument is empty.
        """
        return self._get_tile(
            "XKT021",
            z,
            x,
            y,
            {
                "prefectureCode": _join_codes(prefecture_code),
                "administrativeAreaCode": _join_codes(administrative_area_code),
            },
        )

    def get_large_scale_developed_embankments(self, z: int, x: int, y: int) -> LargeScaleDevelopedEmbankmentsResponse:
        """Get large-scale developed embankments (大規模盛土造成地).

        Land built up by filling on a scale that could slide in an earthquake, which
        municipalities survey and publish. A feature's 盛土区分 says whether it is a filled
        valley or a fill added to a slope.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt020/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Large-scale developed embankments. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT020", z, x, y)

    def get_steep_slope_failure_hazard_areas(
        self,
        z: int,
        x: int,
        y: int,
        prefecture_code: Sequence[str] | str | None = None,
        administrative_area_code: Sequence[str] | str | None = None,
    ) -> SteepSlopeFailureHazardAreasResponse:
        """Get steep slope failure hazard areas (急傾斜地崩壊危険区域).

        An area a prefecture has designated around a steep slope that could collapse, within
        which work liable to induce a collapse is restricted.

        Note that `prefecture_code` here keeps its leading zero -- `09`, not the `9` that
        XKT019 asks for.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt022/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param prefecture_code: One prefecture code, or a sequence of them. Format: NN, so
          `09` rather than `9`. See https://nlftp.mlit.go.jp/ksj/gml/codelist/PrefCd.html
          If not specified, the whole tile.
        :param administrative_area_code: One municipality code, or a sequence of them.
          Format: NNNNN. The same code table the price endpoints spell `city`.
          See https://nlftp.mlit.go.jp/ksj/gml/codelist/AdminiBoundary_CD.xlsx
          If not specified, the whole tile.
        :return: Steep slope failure hazard areas. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15, or a code argument is empty.
        """
        return self._get_tile(
            "XKT022",
            z,
            x,
            y,
            {
                "prefectureCode": _join_codes(prefecture_code),
                "administrativeAreaCode": _join_codes(administrative_area_code),
            },
        )

    def get_district_plans(self, z: int, x: int, y: int) -> DistrictPlansResponse:
        """Get district plans (地区計画).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt023/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: District plans. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT023", z, x, y)

    def get_high_level_use_districts(self, z: int, x: int, y: int) -> HighLevelUseDistrictsResponse:
        """Get high-level use districts (高度利用地区).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt024/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: High-level use districts. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT024", z, x, y)

    def get_expected_flood_inundation_areas_at_maximum_scale(
        self, z: int, x: int, y: int
    ) -> ExpectedFloodInundationAreasAtMaximumScaleResponse:
        """Get expected flood inundation areas at maximum scale (洪水浸水想定区域（想定最大規模）).

        Where a river is expected to inundate under the largest rainfall that can be
        envisaged for the area, designated under the Flood Prevention Act.

        Only 想定最大規模. 国土数値情報 publishes four 洪水浸水想定区域 categories and this
        endpoint serves that one. 計画規模, the rainfall a river is engineered for, covers a
        smaller area and is not available here.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt026/ for details.
        :param z: Zoom level (scale). 14 (block) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Expected flood inundation areas at maximum scale. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 14 and 15.
        """
        # The narrowest range of any endpoint, along with XKT028.
        return self._get_tile("XKT026", z, x, y, zoom_levels=range(14, 16))

    def get_expected_storm_surge_inundation_areas(
        self, z: int, x: int, y: int
    ) -> ExpectedStormSurgeInundationAreasResponse:
        """Get expected storm surge inundation areas (高潮浸水想定区域).

        Where a storm surge is expected to inundate, designated under the Flood Prevention
        Act. Unlike XKT026 the manual names no scale, so the whole dataset is returned.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt027/ for details.
        :param z: Zoom level (scale). 13 ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Expected storm surge inundation areas. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 13 and 15.
        """
        return self._get_tile("XKT027", z, x, y, zoom_levels=range(13, 16))

    def get_expected_tsunami_inundation(self, z: int, x: int, y: int) -> ExpectedTsunamiInundationResponse:
        """Get expected tsunami inundation (津波浸水想定).

        The inundation a prefecture has set as expected from a tsunami, under the Act on
        Regional Development for Tsunami Disaster Prevention. The response carries one
        feature per depth band.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt028/ for details.
        :param z: Zoom level (scale). 14 (block) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Expected tsunami inundation. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 14 and 15.
        """
        return self._get_tile("XKT028", z, x, y, zoom_levels=range(14, 16))

    def get_liquefaction_tendency_based_on_topographical_classification(
        self, z: int, x: int, y: int
    ) -> LiquefactionTendencyBasedOnTopographicalClassificationResponse:
        """Get liquefaction tendency based on topographical classification (地形区分に基づく液状化の発生傾向図).

        How liable the ground is to liquefy, graded on six levels over a 250m grid, by reading
        the liquefaction observed in past earthquakes against the landform each mesh sits on.
        It is not a survey of the ground beneath a particular site.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt025/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Liquefaction tendency based on topographical classification.
          (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT025", z, x, y)

    def get_sediment_disaster_alert_areas(self, z: int, x: int, y: int) -> SedimentDisasterAlertAreasResponse:
        """Get sediment disaster alert areas (土砂災害警戒区域).

        An area where a sediment disaster could harm residents, designated by a prefecture so
        that warnings and evacuation can be organised for it. The stricter 土砂災害特別警戒区域,
        `sediment disaster special alert area`, is designated within one; a feature's 区域区分
        says which it is.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt029/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Sediment disaster alert areas. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT029", z, x, y)

    def get_city_planning_roads(self, z: int, x: int, y: int) -> CityPlanningRoadsResponse:
        """Get city planning roads (都市計画道路).

        Roads a city plan has determined as city planning facilities, with their route and
        width fixed in advance. Building within one is restricted whether or not the road has
        been constructed yet, so a planned road still bears on a parcel it crosses.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt030/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: City planning roads. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT030", z, x, y)

    def get_densely_inhabited_districts(
        self,
        z: int,
        x: int,
        y: int,
        administrative_area_code: Sequence[str] | str | None = None,
    ) -> DenselyInhabitedDistrictsResponse:
        """Get densely inhabited districts (人口集中地区).

        A densely inhabited district, or DID, is a statistical area set by the population
        census: contiguous basic unit blocks each holding about 4,000 inhabitants or more per
        square kilometre, totalling over 5,000 people.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt031/ for details.
        :param z: Zoom level (scale). 9 (prefecture) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param administrative_area_code: One municipality code, or a sequence of them.
          Format: NNNNN. The same code table the price endpoints spell `city`.
          See https://nlftp.mlit.go.jp/ksj/gml/codelist/AdminiBoundary_CD.xlsx
          If not specified, the whole tile.
        :return: Densely inhabited districts. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 9 and 15, or `administrative_area_code`
          is empty.
        """
        return self._get_tile(
            "XKT031",
            z,
            x,
            y,
            {"administrativeAreaCode": _join_codes(administrative_area_code)},
            # Wider than the rest, which start at 11. XKT019 is the other one.
            zoom_levels=range(9, 16),
        )

    def get_designated_emergency_evacuation_sites(
        self, z: int, x: int, y: int
    ) -> DesignatedEmergencyEvacuationSitesResponse:
        """Get designated emergency evacuation sites (指定緊急避難場所).

        A designated emergency evacuation site is somewhere a municipality has designated for
        people to withdraw to while a disaster is occurring or about to. It is not the same as
        a designated shelter (指定避難所), which is where they stay afterwards.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xgt001/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Designated emergency evacuation sites. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XGT001", z, x, y)

    def get_disaster_history(
        self,
        z: int,
        x: int,
        y: int,
        disastertype_code: Sequence[str] | str | None = None,
    ) -> DisasterHistoryResponse:
        """Get disaster history (災害履歴).

        Where past disasters are recorded as having struck, compiled by the national land
        survey from historical documents. A feature carries the date and the document it came
        from, so what is here reflects what was recorded rather than everything that happened.

        Singular because 災害履歴 names the record rather than a countable area.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xst001/ for details.
        :param z: Zoom level (scale). 9 (prefecture) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param disastertype_code: One disaster classification code, or a sequence of them.
          Format: NN. Spelled as the API spells it, with no underscore after `disaster`.
          `11` 浸水域等, `12` 堤防決壊箇所等, `13` 高潮浸水域等, `14` 高潮破堤箇所等,
          `21` がけ崩れ等, `22` 地すべり等, `23` 河道閉塞箇所等, `24` 土石流等, `33` 液状化,
          `34` 地震土砂災害, `37` 津波高, `38` 津波浸水域.
          Not an enum: four of the twelve have no published English name.
          If not specified, every classification.
        :return: Disaster history. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 9 and 15, or `disastertype_code` is empty.
        """
        return self._get_tile(
            "XST001",
            z,
            x,
            y,
            {"disastertype_code": _join_codes(disastertype_code)},
            # As wide as XKT019 and XKT031.
            zoom_levels=range(9, 16),
        )
