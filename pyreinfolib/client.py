from collections.abc import Sequence
from types import TracebackType
from typing import Any, Literal, Self
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from pyreinfolib import enums, exceptions

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


def _compact(params: dict[str, Any]) -> dict[str, Any]:
    """Drop the arguments the caller left out, and refuse the ones left blank.

    `None` is how an argument is omitted, and omitting a filter is a supported request: the
    only required argument of most endpoints is the period, so leaving `city` out asks for the
    whole country on purpose.

    A blank value is not another way to say that. It used to be dropped as though it were
    `None`, which meant `city=""` quietly widened a query to the whole country, a blank
    required argument disappeared from the request altogether, and an empty list of codes read
    as no filter at all. None of the three announced itself.

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

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Issue a GET against `endpoint` and return the decoded JSON body.

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
    ) -> dict[str, Any]:
        """Issue a GET against an endpoint addressed by XYZ tile coordinates.

        Most of the published API is addressed this way: `response_format`, `z`, `x` and `y`
        are all these endpoints have in common, and many accept nothing else. Keeping the
        shared part here leaves each public method as its docstring plus the handful of
        parameters that are actually its own.

        `params` is passed as a dict rather than as keyword arguments because two of the
        keys the API expects, `from` and `to`, are Python keywords.

        The zoom level is checked here rather than in each public method. There are 33 tile
        endpoints to add, and a check that lives in the shared helper cannot be left out of
        one of them.

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
    ) -> dict[str, Any]:
        """Get real estate prices. See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi4 for details.
        :param price_classification: Price classification.
          If not specified, both real estate transaction prices and contract prices.
        :param year: Transaction period (Year).
        :param quarter: Transaction period (Quarter). 1: Jan.~Mar. 2: Apr.~Jun. 3: Jul.~Sep. 4: Oct.~Dec.
        :param area: Prefecture code. See https://nlftp.mlit.go.jp/ksj/gml/codelist/PrefCd.html
        :param city: Municipality code.
        :param station: Station code. See https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-v3_1.html
        :param language: `ja` or `en`. If not specified, `ja`.
        :return: Real estate prices.
        :raises ValueError: If an argument is blank. Leave it out instead, to omit it.
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

        return self._get("XIT001", params)

    def get_municipalities(self, area: str, language: Literal["ja", "en"] | None = None) -> dict[str, Any]:
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

    def get_appraisal_reports(self, year: int, area: str, division: enums.UseDivision) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
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

    def get_city_planning_areas_and_area_classification(self, z: int, x: int, y: int) -> dict[str, Any]:
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

    def get_use_districts(self, z: int, x: int, y: int) -> dict[str, Any]:
        """Get use districts (用途地域).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt002/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Use districts. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT002", z, x, y)

    def get_schools(self, z: int, x: int, y: int) -> dict[str, Any]:
        """Get schools (学校).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt006/ for details.
        :param z: Zoom level (scale). 13 ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Schools. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 13 and 15.
        """
        return self._get_tile("XKT006", z, x, y, zoom_levels=range(13, 16))

    def get_nursery_schools_and_kindergartens_etc(self, z: int, x: int, y: int) -> dict[str, Any]:
        """Get nursery schools and kindergartens etc. (保育園・幼稚園等).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt007/ for details.
        :param z: Zoom level (scale). 13 ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Nursery schools and kindergartens etc. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 13 and 15.
        """
        return self._get_tile("XKT007", z, x, y, zoom_levels=range(13, 16))

    def get_medical_institutions(self, z: int, x: int, y: int) -> dict[str, Any]:
        """Get medical institutions (医療機関).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt010/ for details.
        :param z: Zoom level (scale). 13 ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Medical institutions. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 13 and 15.
        """
        return self._get_tile("XKT010", z, x, y, zoom_levels=range(13, 16))

    def get_future_population_estimates_by_250m_mesh(self, z: int, x: int, y: int) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
        """Get fire prevention districts and quasi-fire prevention districts (防火・準防火地域).

        `districts` twice, although the Japanese writes 地域 once. That is how the Building
        Standards Act translation renders the pair, and it keeps `Fire Prevention District`
        intact as the term the Act defines.
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
    ) -> dict[str, Any]:
        """Get number of passengers per station.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt015/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Number of passengers per station. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT015", z, x, y)

    def get_municipal_offices_and_public_meeting_facilities_etc(self, z: int, x: int, y: int) -> dict[str, Any]:
        """Get municipal offices and public meeting facilities etc. (市区町村役場及び集会施設等).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt018/ for details.
        :param z: Zoom level (scale). 13 ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Municipal offices and public meeting facilities etc. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 13 and 15.
        """
        return self._get_tile("XKT018", z, x, y, zoom_levels=range(13, 16))

    def get_district_plans(self, z: int, x: int, y: int) -> dict[str, Any]:
        """Get district plans (地区計画).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt023/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: District plans. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT023", z, x, y)

    def get_high_level_use_districts(self, z: int, x: int, y: int) -> dict[str, Any]:
        """Get high-level use districts (高度利用地区).
        See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt024/ for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: High-level use districts. (Response format: GeoJson)
        :raises ValueError: If `z` is not between 11 and 15.
        """
        return self._get_tile("XKT024", z, x, y)
