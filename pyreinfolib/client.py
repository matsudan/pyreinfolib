from collections.abc import Sequence
from typing import Any, Literal
from urllib.parse import urljoin

import requests

from pyreinfolib import enums, exceptions

DEFAULT_TIMEOUT = 30.0

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
    other. An empty sequence becomes an empty string, which `_compact` then drops.
    """
    if codes is None:
        return None
    if isinstance(codes, str):
        return codes
    return ",".join(codes)


def _compact(params: dict[str, Any]) -> dict[str, Any]:
    """Drop the entries the API should not receive at all.

    `None` marks an argument the caller left out. An empty string is dropped too, which
    keeps `city=""` out of the query the way the per-argument `if` checks used to.

    Deliberately not a truthiness test. `x=0` is already a valid tile coordinate, and a
    future parameter whose valid values include `0` would otherwise vanish from the request
    with nothing to show why.
    """
    return {key: value for key, value in params.items() if value is not None and value != ""}


class Client:
    def __init__(self, api_key: str, timeout: float | tuple[float, float] = DEFAULT_TIMEOUT) -> None:
        """
        :param api_key: API key issued for the Real Estate Information Library.
        :param timeout: Request timeout in seconds, passed straight to `requests`.
          A single value applies to both connect and read, or pass a `(connect, read)` tuple.
        :raises ValueError: If `api_key` is empty.
        """
        # Reject it here rather than on the first request, where an empty or missing key
        # surfaces as a 401 that gives no hint about the actual cause.
        if not api_key:
            raise ValueError("`api_key` must be a non-empty string.")

        self.api_key = api_key
        self.base_url = "https://www.reinfolib.mlit.go.jp/ex-api/external/"
        self.timeout = timeout

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
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}

        # Each failure mode gets its own `try`. Wrapping the whole exchange in one block
        # would have to re-derive which stage failed from the exception type, which is how
        # the previous version came to dereference a `response` that connection errors and
        # timeouts do not have.
        try:
            r = requests.get(api_url, headers=headers, params=params, timeout=self.timeout)
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
    ) -> dict[str, Any]:
        """Issue a GET against an endpoint addressed by XYZ tile coordinates.

        Most of the published API is addressed this way: `response_format`, `z`, `x` and `y`
        are all these endpoints have in common, and many accept nothing else. Keeping the
        shared part here leaves each public method as its docstring plus the handful of
        parameters that are actually its own.

        `params` is passed as a dict rather than as keyword arguments because two of the
        keys the API expects, `from` and `to`, are Python keywords.

        `z` is a plain `int` here. The zoom levels each endpoint accepts differ, so the
        narrow `Literal` belongs on the public method that documents them.

        :param endpoint: Endpoint id, e.g. `XKT015`.
        :param z: Zoom level (scale).
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param params: Any further query parameters, keyed as the API expects them.
        :return: The decoded JSON body.
        """
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
        price_classification: Literal["01", "02"] | None = None,
        quarter: Literal[1, 2, 3, 4] | None = None,
        area: str | None = None,
        city: str | None = None,
        station: str | None = None,
        language: Literal["ja", "en"] | None = None,
    ) -> dict[str, Any]:
        """Get real estate prices. See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi4 for details.
        :param price_classification: Price classification code.
          01: Real estate transaction price information, 02: Contract price information,
          Unspecified: Both transaction price information and contract price information.
        :param year: Transaction period (Year).
        :param quarter: Transaction period (Quarter). 1: Jan.~Mar. 2: Apr.~Jun. 3: Jul.~Sep. 4: Oct.~Dec.
        :param area: Prefecture code. See https://nlftp.mlit.go.jp/ksj/gml/codelist/PrefCd.html
        :param city: Municipality code.
        :param station: Station code. See https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-v3_1.html
        :param language: `ja` or `en`. If not specified, `ja`.
        :return: Real estate prices.
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
        :raises NoResultsError: If no appraisal report matches the given year and area.
        """
        params: dict[str, Any] = {"year": year, "area": area, "division": division}

        return self._get("XCT001", params)

    def get_real_estate_prices_point(
        self,
        z: Literal[11, 12, 13, 14, 15],
        x: int,
        y: int,
        period_from: int,
        period_to: int,
        price_classification: Literal["01", "02"] | None = None,
        land_type_code: Sequence[enums.LandTypeCode] | enums.LandTypeCode | None = None,
    ) -> dict[str, Any]:
        """Get real estate prices point.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi7 for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param period_from: Transaction period from. Format: YYYYN. e.g. 20241
        :param period_to: Transaction period to. Format: YYYYN. e.g. 20242
        :param price_classification: Price classification code.
          01: Real estate transaction price information, 02: Contract price information,
          Unspecified: Both transaction price information and contract price information.
        :param land_type_code: One land type code, or a sequence of them.
          See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi7
        :return: Real estate prices point. (Response format: GeoJson)
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

    def get_land_price_public_notices_and_surveys_point(
        self,
        z: Literal[13, 14, 15],
        x: int,
        y: int,
        year: int,
        price_classification: Literal["0", "1"] | None = None,
        use_category_code: Sequence[enums.UseDivision] | enums.UseDivision | None = None,
    ) -> dict[str, Any]:
        """Get land price public notices (standard land prices) and
        prefectural land price surveys (benchmark land prices) point.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi8 for details.
        :param z: Zoom level (scale). 13 ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param year: target year.
        :param price_classification: Land price classification code.
          0: Land price public notices, 1: Prefectural land price surveys, Unspecified: Both 0 and 1.
        :param use_category_code: One use division code, or a sequence of them.
          See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi8
        :return: land price public notices (standard land prices) and
        prefectural land price surveys (benchmark land prices) point. (Response format: GeoJson)
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
        )

    def get_number_of_passengers_per_station(
        self,
        z: Literal[11, 12, 13, 14, 15],
        x: int,
        y: int,
    ) -> dict[str, Any]:
        """Get number of passengers per station.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi20 for details.
        :param z: Zoom level (scale). 11 (city) ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :return: Number of passengers per station. (Response format: GeoJson)
        """
        return self._get_tile("XKT015", z, x, y)
