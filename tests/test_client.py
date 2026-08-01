from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest
import requests
import responses
from helpers import params_of
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from pyreinfolib import Client, tiles
from pyreinfolib.enums import LandPriceClassification, LandTypeCode, PriceClassification, UseDivision
from pyreinfolib.exceptions import (
    APIError,
    AuthenticationError,
    InvalidResponseError,
    NoResultsError,
    RateLimitError,
    ReinfolibError,
    TransportError,
)

BASE_URL = "https://www.reinfolib.mlit.go.jp/ex-api/external/"
API_KEY = "dummy"
DUMMY_RESPONSE = {"status": "OK", "data": []}
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
THROTTLED = {"json": {"message": "slow down"}, "status": 429}

# Each tile endpoint, the arguments it needs beyond the coordinates, and the zoom levels its
# docstring documents. XPT002 is the one that does not start at 11, which is why the check has
# to be per endpoint rather than one shared range.
TILE_ENDPOINTS = [
    ("get_real_estate_prices_point", "XPT001", {"period_from": 20241, "period_to": 20241}, range(11, 16)),
    ("get_land_market_value_publication_and_research_point", "XPT002", {"year": 2020}, range(13, 16)),
    ("get_number_of_passengers_per_station", "XKT015", {}, range(11, 16)),
]
TILE_ENDPOINT_IDS = ["XPT001", "XPT002", "XKT015"]


@dataclass
class RequestCase:
    """Table-driven case describing how method arguments map onto the outgoing request.

    `expected_params` is compared for equality with the whole query string, so optional
    arguments that were not passed are asserted to be absent from the request.
    """

    id: str
    args: dict[str, Any]
    expected_params: dict[str, str]


@pytest.fixture
def mock_api():
    """Intercept requests at the transport level.

    On exit `RequestsMock` asserts every registered response was actually requested,
    so each test also proves the client issued a call to the expected endpoint.
    """
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def client():
    # Closed on teardown: the client now owns a connection pool, and leaving one open per
    # test would leak sockets across the suite.
    with Client(api_key=API_KEY) as client:
        yield client


def retries_of(client: Client) -> Retry:
    """The retry policy the client actually mounted, as the transport sees it."""
    adapter = client._session.get_adapter(BASE_URL)
    # `get_adapter` is typed as returning the `BaseAdapter` interface, which carries no
    # retry policy. Narrowing to the concrete adapter is what makes `max_retries` reachable.
    assert isinstance(adapter, HTTPAdapter)
    assert isinstance(adapter.max_retries, Retry)
    return adapter.max_retries


def assert_request(mock_api: responses.RequestsMock, method: Callable, endpoint: str, case: RequestCase) -> None:
    """Call `method` with the case arguments and assert the request it produced."""
    url = f"{BASE_URL}{endpoint}"
    mock_api.get(url, json=DUMMY_RESPONSE)

    assert method(**case.args) == DUMMY_RESPONSE

    assert len(mock_api.calls) == 1
    request = mock_api.calls[0].request
    assert request.url is not None
    assert request.url.split("?")[0] == url
    assert request.headers["Ocp-Apim-Subscription-Key"] == API_KEY
    assert params_of(request) == case.expected_params


class TestClient:
    def test_init(self):
        with Client(api_key="dummy") as client:
            assert client.api_key == "dummy"
            assert client.base_url == BASE_URL
            assert client.timeout == DEFAULT_TIMEOUT
            assert retries_of(client).total == DEFAULT_MAX_RETRIES

    def test_init_accepts_custom_timeout(self):
        with Client(api_key="dummy", timeout=5) as client:
            assert client.timeout == 5
        with Client(api_key="dummy", timeout=(3.0, 10.0)) as client:
            assert client.timeout == (3.0, 10.0)

    @pytest.mark.parametrize("max_retries", [0, 1, 10], ids=["disabled", "one", "many"])
    def test_init_accepts_custom_max_retries(self, max_retries):
        with Client(api_key="dummy", max_retries=max_retries) as client:
            assert retries_of(client).total == max_retries

    def test_init_mounts_a_retry_policy_that_matches_the_documented_behaviour(self):
        """Asserted here because the effect is otherwise only visible in wall-clock time."""
        with Client(api_key="dummy") as client:
            retry = retries_of(client)

            assert set(retry.status_forcelist) == {429, 500, 502, 503, 504}
            # 404 means the query matched no data, so another attempt only waits to be told
            # the same thing.
            assert 404 not in retry.status_forcelist
            assert retry.backoff_factor > 0
            # A `Retry-After` from the API wins over the computed backoff.
            assert retry.respect_retry_after_header is True
            # See `test__get_maps_an_exhausted_retry_sequence_to_the_status_it_ended_on`.
            assert retry.raise_on_status is False

    @pytest.mark.parametrize("api_key", ["", None], ids=["empty string", "None"])
    def test_init_rejects_an_empty_api_key(self, api_key):
        """`None` covers `Client(os.getenv("TYPO"))`, which would otherwise only fail as a 401."""
        with pytest.raises(ValueError, match="api_key"):
            Client(api_key=api_key)

    @pytest.mark.parametrize("max_retries", [-1, -10])
    def test_init_rejects_negative_max_retries(self, max_retries):
        """`Retry(total=-1)` means something else entirely, so it must not be reachable."""
        with pytest.raises(ValueError, match="max_retries"):
            Client(api_key="dummy", max_retries=max_retries)

    def test_close_is_idempotent(self):
        """Calling `close` and then leaving a `with` block must not be an error."""
        client = Client(api_key="dummy")

        client.close()
        client.close()

    def test_used_as_a_context_manager_it_yields_itself_and_closes_on_exit(self, mock_api, monkeypatch):
        """Spied rather than observed: `Session.close` empties its connection pools without
        leaving anything on the session to assert against.
        """
        mock_api.get(f"{BASE_URL}TEST001", json=DUMMY_RESPONSE)
        client = Client(api_key=API_KEY)
        closed: list[bool] = []
        monkeypatch.setattr(client._session, "close", lambda: closed.append(True))

        with client as entered:
            assert entered is client
            assert entered._get("TEST001") == DUMMY_RESPONSE
            assert closed == []

        assert closed == [True]

    def test__get(self, mock_api, client):
        expected = {"status": "OK", "data": [{"test": "value"}]}
        mock_api.get(f"{BASE_URL}TEST001", json=expected)

        actual = client._get("TEST001", {"param1": "value1"})

        assert actual == expected
        request = mock_api.calls[0].request
        assert request.url == f"{BASE_URL}TEST001?param1=value1"
        assert request.headers["Ocp-Apim-Subscription-Key"] == API_KEY

    def test__get_relative_endpoint_does_not_escape_base_path(self, mock_api, client):
        """`urljoin` keeps the `/ex-api/external/` prefix as long as the endpoint is relative."""
        mock_api.get(f"{BASE_URL}XIT001", json=DUMMY_RESPONSE)

        client._get("XIT001")

        assert mock_api.calls[0].request.url == f"{BASE_URL}XIT001"

    @pytest.mark.parametrize("timeout", [None, 5, (3.0, 10.0)], ids=["default", "scalar", "connect/read tuple"])
    def test__get_passes_timeout_to_transport(self, mock_api, timeout):
        """Without a timeout an unresponsive server would block the caller forever."""
        mock_api.get(f"{BASE_URL}TEST001", json=DUMMY_RESPONSE)
        client = Client(api_key=API_KEY) if timeout is None else Client(api_key=API_KEY, timeout=timeout)

        client._get("TEST001")

        expected = DEFAULT_TIMEOUT if timeout is None else timeout
        assert mock_api.calls[0].request.req_kwargs["timeout"] == expected

    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (400, APIError),
            (401, AuthenticationError),
            # Not AuthenticationError: the gateway uses 403 for an exhausted call quota,
            # and the API manual documents no meaning for it either way.
            (403, APIError),
            (404, NoResultsError),
            (429, RateLimitError),
            (500, APIError),
            (503, APIError),
        ],
    )
    def test__get_maps_error_status_to_a_specific_exception(self, mock_api, client, status, expected):
        mock_api.get(f"{BASE_URL}TEST999", json={"message": "error"}, status=status)

        with pytest.raises(expected) as exc_info:
            client._get("TEST999", {"param1": "value1"})

        # `pytest.raises(expected)` would also accept a subclass, so pin the exact type:
        # mapping 500 onto `NoResultsError`, say, would otherwise pass as an `APIError`.
        assert type(exc_info.value) is expected
        assert exc_info.value.status_code == status

    def test__get_error_carries_the_response_body(self, mock_api, client):
        """The API explains itself in the body; discarding it leaves nothing to debug.

        Registered as a raw body rather than `json=`, which would escape the non-ASCII
        characters and no longer match what the API actually returns.
        """
        mock_api.get(
            f"{BASE_URL}TEST999",
            body='{"message":"検索結果がありません。"}',
            content_type="application/json",
            status=404,
        )

        with pytest.raises(NoResultsError) as exc_info:
            client._get("TEST999")

        error = exc_info.value
        assert error.response_body == '{"message":"検索結果がありません。"}'
        assert error.url == f"{BASE_URL}TEST999"
        assert "検索結果がありません。" in str(error)

    @pytest.mark.parametrize(
        "raised",
        [
            requests.ConnectionError("connection refused"),
            requests.Timeout("timed out"),
        ],
        ids=lambda exc: type(exc).__name__,
    )
    def test__get_wraps_failures_that_carry_no_response(self, mock_api, client, raised):
        """These never produced a response, so they cannot become an `APIError`.

        An earlier version dereferenced `e.response.text` unconditionally and replaced the
        real cause with `AttributeError: 'NoneType' object has no attribute 'text'`, which
        is exactly the case one needs to debug.
        """
        mock_api.get(f"{BASE_URL}TEST001", body=raised)

        with pytest.raises(TransportError) as exc_info:
            client._get("TEST001")

        # The original exception stays reachable for anyone who needs the transport detail.
        assert exc_info.value.__cause__ is raised
        assert str(raised) in str(exc_info.value)

    def test__get_rejects_a_success_response_that_is_not_json(self, mock_api, client):
        """A maintenance page served with HTTP 200 must not surface as a `requests` error."""
        mock_api.get(f"{BASE_URL}TEST001", body="<html>maintenance</html>", content_type="text/html")

        with pytest.raises(InvalidResponseError) as exc_info:
            client._get("TEST001")

        error = exc_info.value
        assert error.status_code == 200
        assert error.response_body == "<html>maintenance</html>"

    @pytest.mark.parametrize("status", [404, 500])
    def test__get_does_not_leak_requests_exceptions(self, mock_api, client, status):
        """Catching `ReinfolibError` alone must be enough, with no import of `requests`."""
        mock_api.get(f"{BASE_URL}TEST999", json={"message": "error"}, status=status)

        with pytest.raises(ReinfolibError):
            client._get("TEST999")

    def test__get_goes_through_the_session(self, mock_api, client, monkeypatch):
        """Connection reuse leaves no trace in a response, so guard the call path instead.

        Going back to the module-level `requests.get` would open a fresh connection for
        every tile and still pass every other test in this file.
        """

        def fail(*args: object, **kwargs: object) -> None:
            raise AssertionError("requests.get was called instead of the client's session")

        monkeypatch.setattr(requests, "get", fail)
        mock_api.get(f"{BASE_URL}TEST001", json=DUMMY_RESPONSE)

        assert client._get("TEST001") == DUMMY_RESPONSE

    def test__get_retries_a_throttled_request(self, mock_api):
        """Being throttled is expected rather than exceptional: the API sets no explicit
        request ceiling and asks that calls be spaced out.
        """
        mock_api.get(f"{BASE_URL}TEST001", **THROTTLED)
        mock_api.get(f"{BASE_URL}TEST001", json=DUMMY_RESPONSE)

        with Client(api_key=API_KEY, max_retries=1) as client:
            assert client._get("TEST001") == DUMMY_RESPONSE

        assert len(mock_api.calls) == 2

    def test__get_maps_an_exhausted_retry_sequence_to_the_status_it_ended_on(self, mock_api):
        """The reason `raise_on_status` is False.

        Left at the urllib3 default, an exhausted sequence raises inside urllib3, requests
        wraps that in `RetryError`, and the handler in `_get` would translate it to
        `TransportError` -- turning a request that was throttled all the way to the last
        attempt into something indistinguishable from a connection failure.
        """
        mock_api.get(f"{BASE_URL}TEST001", **THROTTLED)
        mock_api.get(f"{BASE_URL}TEST001", **THROTTLED)

        with Client(api_key=API_KEY, max_retries=1) as client, pytest.raises(RateLimitError) as exc_info:
            client._get("TEST001")

        assert exc_info.value.status_code == 429
        assert len(mock_api.calls) == 2

    def test__get_does_not_retry_a_query_that_matched_no_data(self, mock_api):
        """404 is a normal answer here, so retrying it only delays the same result."""
        mock_api.get(f"{BASE_URL}TEST001", json={"message": "検索結果がありません。"}, status=404)

        with Client(api_key=API_KEY) as client, pytest.raises(NoResultsError):
            client._get("TEST001")

        assert len(mock_api.calls) == 1

    def test__get_makes_a_single_attempt_when_retries_are_disabled(self, mock_api):
        mock_api.get(f"{BASE_URL}TEST001", **THROTTLED)

        with Client(api_key=API_KEY, max_retries=0) as client, pytest.raises(RateLimitError):
            client._get("TEST001")

        assert len(mock_api.calls) == 1

    @pytest.mark.parametrize(
        "case",
        [
            RequestCase(
                id="all params",
                args={
                    "year": 2025,
                    "price_classification": PriceClassification.REAL_ESTATE_TRANSACTION_PRICE,
                    "quarter": 1,
                    "area": "13",
                    "city": "13109",
                    "station": "003785",
                    "language": "ja",
                },
                expected_params={
                    "year": "2025",
                    "priceClassification": "01",
                    "quarter": "1",
                    "area": "13",
                    "city": "13109",
                    "station": "003785",
                    "language": "ja",
                },
            ),
            RequestCase(
                id="only required param",
                args={"year": 2025},
                expected_params={"year": "2025"},
            ),
            RequestCase(
                # Omitting the filters is a supported request, not a mistake: `year` is the
                # only required argument, so this asks for the whole country deliberately.
                id="omitted optional params are absent from the query",
                args={"year": 2025, "price_classification": None, "quarter": None, "city": None},
                expected_params={"year": "2025"},
            ),
        ],
        ids=lambda case: case.id,
    )
    def test_get_real_estate_prices(self, mock_api, client, case):
        assert_request(mock_api, client.get_real_estate_prices, "XIT001", case)

    @pytest.mark.parametrize(
        "case",
        [
            RequestCase(
                id="all params",
                args={"area": "13", "language": "en"},
                expected_params={"area": "13", "language": "en"},
            ),
            RequestCase(
                id="without language",
                args={"area": "13"},
                expected_params={"area": "13"},
            ),
        ],
        ids=lambda case: case.id,
    )
    def test_get_municipalities(self, mock_api, client, case):
        assert_request(mock_api, client.get_municipalities, "XIT002", case)

    @pytest.mark.parametrize(
        "case",
        [
            RequestCase(
                id="use division is serialized to its code",
                args={"year": 2024, "area": "13", "division": UseDivision.INDUSTRIAL_LAND},
                expected_params={"year": "2024", "area": "13", "division": "09"},
            ),
        ],
        ids=lambda case: case.id,
    )
    def test_get_appraisal_reports(self, mock_api, client, case):
        assert_request(mock_api, client.get_appraisal_reports, "XCT001", case)

    @pytest.mark.parametrize(
        "case",
        [
            RequestCase(
                id="period is renamed to from/to and land types are joined",
                args={
                    "z": 11,
                    "x": 1819,
                    "y": 806,
                    "period_from": 20241,
                    "period_to": 20242,
                    "price_classification": PriceClassification.REAL_ESTATE_TRANSACTION_PRICE,
                    "land_type_code": [LandTypeCode.LAND, LandTypeCode.FOREST_LAND],
                },
                expected_params={
                    "response_format": "geojson",
                    "z": "11",
                    "x": "1819",
                    "y": "806",
                    "from": "20241",
                    "to": "20242",
                    "priceClassification": "01",
                    "landTypeCode": "01,11",
                },
            ),
            RequestCase(
                id="single land type in a list is not comma separated",
                args={
                    "z": 15,
                    "x": 1819,
                    "y": 806,
                    "period_from": 20241,
                    "period_to": 20241,
                    "land_type_code": [LandTypeCode.PRE_OWNED_CONDOMINIUMS_ETC],
                },
                expected_params={
                    "response_format": "geojson",
                    "z": "15",
                    "x": "1819",
                    "y": "806",
                    "from": "20241",
                    "to": "20241",
                    "landTypeCode": "07",
                },
            ),
            RequestCase(
                # A bare StrEnum is a str, so joining it used to yield "0,7" with no error.
                id="bare land type enum is not split into characters",
                args={
                    "z": 15,
                    "x": 1819,
                    "y": 806,
                    "period_from": 20241,
                    "period_to": 20241,
                    "land_type_code": LandTypeCode.PRE_OWNED_CONDOMINIUMS_ETC,
                },
                expected_params={
                    "response_format": "geojson",
                    "z": "15",
                    "x": "1819",
                    "y": "806",
                    "from": "20241",
                    "to": "20241",
                    "landTypeCode": "07",
                },
            ),
            RequestCase(
                id="only required params",
                args={"z": 11, "x": 1819, "y": 806, "period_from": 20241, "period_to": 20241},
                expected_params={
                    "response_format": "geojson",
                    "z": "11",
                    "x": "1819",
                    "y": "806",
                    "from": "20241",
                    "to": "20241",
                },
            ),
            RequestCase(
                # Filtering the query on truthiness rather than on `None` would drop both
                # coordinates here and silently request a different tile.
                id="a zero tile coordinate is still sent",
                args={"z": 11, "x": 0, "y": 0, "period_from": 20241, "period_to": 20241},
                expected_params={
                    "response_format": "geojson",
                    "z": "11",
                    "x": "0",
                    "y": "0",
                    "from": "20241",
                    "to": "20241",
                },
            ),
            RequestCase(
                id="land types omitted entirely",
                args={
                    "z": 15,
                    "x": 1819,
                    "y": 806,
                    "period_from": 20241,
                    "period_to": 20241,
                    "land_type_code": None,
                },
                expected_params={
                    "response_format": "geojson",
                    "z": "15",
                    "x": "1819",
                    "y": "806",
                    "from": "20241",
                    "to": "20241",
                },
            ),
        ],
        ids=lambda case: case.id,
    )
    def test_get_real_estate_prices_point(self, mock_api, client, case):
        assert_request(mock_api, client.get_real_estate_prices_point, "XPT001", case)

    @pytest.mark.parametrize(
        "case",
        [
            RequestCase(
                id="use categories are joined",
                args={
                    "z": 13,
                    "x": 7312,
                    "y": 3008,
                    "year": 2020,
                    "price_classification": LandPriceClassification.LAND_MARKET_VALUE_PUBLICATION,
                    "use_category_code": [UseDivision.RESIDENTIAL_LAND, UseDivision.COMMERCIAL_LAND],
                },
                expected_params={
                    "response_format": "geojson",
                    "z": "13",
                    "x": "7312",
                    "y": "3008",
                    "year": "2020",
                    "priceClassification": "0",
                    "useCategoryCode": "00,05",
                },
            ),
            RequestCase(
                id="bare use category enum is not split into characters",
                args={
                    "z": 13,
                    "x": 7312,
                    "y": 3008,
                    "year": 2020,
                    "use_category_code": UseDivision.INDUSTRIAL_LAND,
                },
                expected_params={
                    "response_format": "geojson",
                    "z": "13",
                    "x": "7312",
                    "y": "3008",
                    "year": "2020",
                    "useCategoryCode": "09",
                },
            ),
            RequestCase(
                id="only required params",
                args={"z": 15, "x": 7312, "y": 3008, "year": 2020},
                expected_params={
                    "response_format": "geojson",
                    "z": "15",
                    "x": "7312",
                    "y": "3008",
                    "year": "2020",
                },
            ),
        ],
        ids=lambda case: case.id,
    )
    def test_get_land_market_value_publication_and_research_point(self, mock_api, client, case):
        assert_request(mock_api, client.get_land_market_value_publication_and_research_point, "XPT002", case)

    @pytest.mark.parametrize(
        "case",
        [
            RequestCase(
                id="tile coordinates only",
                args={"z": 11, "x": 1819, "y": 806},
                expected_params={"response_format": "geojson", "z": "11", "x": "1819", "y": "806"},
            ),
        ],
        ids=lambda case: case.id,
    )
    def test_get_number_of_passengers_per_station(self, mock_api, client, case):
        assert_request(mock_api, client.get_number_of_passengers_per_station, "XKT015", case)

    @pytest.mark.parametrize(
        ("method_name", "endpoint", "args"),
        [
            (
                "get_real_estate_prices_point",
                "XPT001",
                {"z": 11, "x": 1819, "y": 806, "period_from": 20241, "period_to": 20241},
            ),
            (
                "get_land_market_value_publication_and_research_point",
                "XPT002",
                {"z": 13, "x": 7312, "y": 3008, "year": 2020},
            ),
            (
                "get_number_of_passengers_per_station",
                "XKT015",
                {"z": 11, "x": 1819, "y": 806},
            ),
        ],
        ids=["XPT001", "XPT002", "XKT015"],
    )
    def test_tile_endpoints_all_send_the_shared_parameters(self, mock_api, client, method_name, endpoint, args):
        """Asserted across methods rather than per method, because the keys now come from
        one place. Most of the API is addressed by tile, so a mistake in `_get_tile` would
        otherwise have to be caught separately for every endpoint added on top of it.
        """
        mock_api.get(f"{BASE_URL}{endpoint}", json=DUMMY_RESPONSE)

        getattr(client, method_name)(**args)

        params = params_of(mock_api.calls[0].request)
        assert params["response_format"] == "geojson"
        assert params["z"] == str(args["z"])
        assert params["x"] == str(args["x"])
        assert params["y"] == str(args["y"])

    @pytest.mark.parametrize(("method_name", "endpoint", "extra", "zoom_levels"), TILE_ENDPOINTS, ids=TILE_ENDPOINT_IDS)
    def test_tile_endpoints_accept_a_zoom_level_held_in_a_variable(
        self, mock_api, client, method_name, endpoint, extra, zoom_levels
    ):
        """`z` is annotated `int`, not a `Literal`, and this is why.

        A `Literal` only constrains a call site that writes the number out. Every documented
        way of obtaining a zoom level here produces an `int` -- `tiles.containing` and
        `tiles.covering` both do -- so the `Literal` rejected the intended usage while
        catching nothing about an out-of-range level that arrived computed.
        """
        for _ in zoom_levels:
            mock_api.get(f"{BASE_URL}{endpoint}", json=DUMMY_RESPONSE)

        for z in zoom_levels:
            getattr(client, method_name)(z=z, x=1, y=1, **extra)

        assert len(mock_api.calls) == len(zoom_levels)

    @pytest.mark.parametrize(("method_name", "endpoint", "extra", "zoom_levels"), TILE_ENDPOINTS, ids=TILE_ENDPOINT_IDS)
    def test_tile_endpoints_reject_a_zoom_level_they_do_not_document(
        self, mock_api, client, method_name, endpoint, extra, zoom_levels
    ):
        """Nothing is registered on `mock_api`, so a level that slips through the check would
        fail as an unmatched request rather than reaching the real API.
        """
        for z in (zoom_levels.start - 1, zoom_levels[-1] + 1, 0, -1, 99):
            with pytest.raises(ValueError, match=endpoint):
                getattr(client, method_name)(z=z, x=1, y=1, **extra)

    @pytest.mark.parametrize("z", [11, 12])
    def test_the_land_price_endpoint_rejects_levels_the_others_accept(self, mock_api, client, z):
        """XPT002 starts at 13 where the rest start at 11.

        One shared range would quietly send 11 to an endpoint that does not serve it, and the
        API answers a tile it has no data for with an empty feature list rather than an error.
        """
        with pytest.raises(ValueError, match="XPT002"):
            client.get_land_market_value_publication_and_research_point(z=z, x=7312, y=3008, year=2020)

    def test_the_rejection_names_the_endpoint_and_the_range(self, mock_api, client):
        """With 33 tile endpoints and more than one range among them, "z must be 11 to 15" on
        its own does not tell the caller which endpoint disagreed.
        """
        with pytest.raises(ValueError) as exc_info:
            client.get_land_market_value_publication_and_research_point(z=11, x=7312, y=3008, year=2020)

        message = str(exc_info.value)
        assert "XPT002" in message
        assert "13" in message
        assert "15" in message
        assert "11" in message


class TestExceptions:
    """The shape of the hierarchy is public API: callers catch these instead of `requests`."""

    @pytest.mark.parametrize(
        "exc",
        [APIError, AuthenticationError, InvalidResponseError, NoResultsError, RateLimitError, TransportError],
        ids=lambda exc: exc.__name__,
    )
    def test_every_exception_derives_from_reinfolib_error(self, exc):
        assert issubclass(exc, ReinfolibError)

    @pytest.mark.parametrize(
        "exc",
        [AuthenticationError, InvalidResponseError, NoResultsError, RateLimitError],
        ids=lambda exc: exc.__name__,
    )
    def test_response_bearing_exceptions_are_catchable_as_api_error(self, exc):
        """One `except APIError` has to cover every failure that came back with a status."""
        assert issubclass(exc, APIError)

    def test_transport_error_is_not_an_api_error(self):
        """It has no status code, so code that reads `status_code` must not catch it."""
        assert not issubclass(TransportError, APIError)


class TestEnums:
    def test_the_two_price_classification_tables_stay_distinct(self):
        """XPT002 numbers its codes from `0`, XIT001 and XPT001 from `01`.

        The API spells the parameter `priceClassification` in all three, which invites
        folding the two tables into one enum. Sending `01` where `0` is expected is answered
        with a filtered or empty result rather than an error, so the mistake would not
        surface at the call site.
        """
        price_codes = {member.value for member in PriceClassification}
        land_price_codes = {member.value for member in LandPriceClassification}

        assert price_codes == {"01", "02"}
        assert land_price_codes == {"0", "1"}
        assert not price_codes & land_price_codes


class TestBlankArguments:
    """A blank argument used to be treated as an omitted one, in three different ways.

    `city=""` widened a query to the whole country, a blank required argument disappeared from
    the request, and `land_type_code=[]` read as no filter. None of the three said anything, so
    a caller who thought they had filtered got a wider answer and no indication of it.

    Omitting a filter is still supported and still means the whole country. It is spelled by
    leaving the argument out, or passing `None`, which `test_get_real_estate_prices` covers.
    """

    @pytest.mark.parametrize("argument", ["area", "city", "station", "language"])
    def test_a_blank_optional_filter_is_refused(self, mock_api, client, argument):
        """Nothing is registered on `mock_api`, so a blank that slipped through would fail as
        an unmatched request rather than quietly fetching the whole country.
        """
        with pytest.raises(ValueError, match=argument):
            client.get_real_estate_prices(year=2024, **{argument: ""})

    @pytest.mark.parametrize(
        ("method_name", "args"),
        [
            ("get_real_estate_prices", {"year": 2024, "area": ""}),
            ("get_municipalities", {"area": ""}),
            ("get_appraisal_reports", {"year": 2024, "area": "", "division": UseDivision.INDUSTRIAL_LAND}),
        ],
        ids=["XIT001", "XIT002", "XCT001"],
    )
    def test_a_blank_area_is_refused_by_every_method_that_takes_one(self, mock_api, client, method_name, args):
        """Uniform across the three, which it was not.

        `get_municipalities` dropped a blank `area` even though it is required, producing a
        request with no query string at all. `get_appraisal_reports` did not go through
        `_compact` and sent `area=` instead. Same argument, same blank, two behaviours.
        """
        with pytest.raises(ValueError, match="area"):
            getattr(client, method_name)(**args)

    @pytest.mark.parametrize(
        ("method_name", "args", "expected"),
        [
            (
                "get_real_estate_prices_point",
                {"z": 15, "x": 1819, "y": 806, "period_from": 20241, "period_to": 20241, "land_type_code": []},
                "landTypeCode",
            ),
            (
                "get_land_market_value_publication_and_research_point",
                {"z": 13, "x": 7312, "y": 3008, "year": 2020, "use_category_code": []},
                "useCategoryCode",
            ),
        ],
        ids=["land_type_code", "use_category_code"],
    )
    def test_an_empty_sequence_of_codes_is_refused(self, mock_api, client, method_name, args, expected):
        """A list that filtered down to nothing is not a request for every code."""
        with pytest.raises(ValueError, match=expected):
            getattr(client, method_name)(**args)

    def test_the_refusal_names_every_blank_argument_and_says_what_to_do(self, mock_api, client):
        """Naming one of three would send the caller back for another round."""
        with pytest.raises(ValueError) as exc_info:
            client.get_real_estate_prices(year=2024, area="", city="", station="")

        message = str(exc_info.value)
        assert "area" in message
        assert "city" in message
        assert "station" in message
        assert "None" in message

    def test_zero_is_not_treated_as_blank(self, mock_api, client):
        """`x=0` is a valid tile coordinate, so the check compares against `""` rather than
        testing truthiness.
        """
        mock_api.get(f"{BASE_URL}XKT015", json=DUMMY_RESPONSE)

        client.get_number_of_passengers_per_station(z=11, x=0, y=0)

        assert params_of(mock_api.calls[0].request)["x"] == "0"


# Endpoints that take nothing but the tile coordinates, with the zoom levels their manual page
# documents. The zoom range is the only thing that varies between them, and it is the only
# thing about them that can be got wrong without the request failing outright: too low or too
# high is refused locally, but a range that is wrong in the other direction would refuse a
# level the API serves.
TILE_ONLY_ENDPOINTS = [
    ("get_city_planning_areas_and_area_classification", "XKT001", range(11, 16)),
    ("get_use_districts", "XKT002", range(11, 16)),
    ("get_schools", "XKT006", range(13, 16)),
    ("get_nursery_schools_and_kindergartens_etc", "XKT007", range(13, 16)),
    ("get_medical_institutions", "XKT010", range(13, 16)),
    ("get_future_population_estimates_by_250m_mesh", "XKT013", range(11, 16)),
    ("get_fire_prevention_districts_and_quasi_fire_prevention_districts", "XKT014", range(11, 16)),
    ("get_number_of_passengers_per_station", "XKT015", range(11, 16)),
    ("get_municipal_offices_and_public_meeting_facilities_etc", "XKT018", range(13, 16)),
    ("get_district_plans", "XKT023", range(11, 16)),
    ("get_high_level_use_districts", "XKT024", range(11, 16)),
]
TILE_ONLY_ENDPOINT_IDS = [endpoint for _, endpoint, _ in TILE_ONLY_ENDPOINTS]


class TestTileOnlyEndpoints:
    @pytest.mark.parametrize(
        ("method_name", "endpoint", "zoom_levels"), TILE_ONLY_ENDPOINTS, ids=TILE_ONLY_ENDPOINT_IDS
    )
    def test_it_requests_its_own_endpoint_with_the_shared_parameters(
        self, mock_api, client, method_name, endpoint, zoom_levels
    ):
        """The endpoint id is the one thing a copied method body gets wrong silently.

        Every one of these has the same shape, so a paste that kept the previous id would
        return plausible GeoJson from the wrong dataset.
        """
        mock_api.get(f"{BASE_URL}{endpoint}", json=DUMMY_RESPONSE)

        assert getattr(client, method_name)(z=zoom_levels[0], x=1819, y=806) == DUMMY_RESPONSE

        request = mock_api.calls[0].request
        assert request.url.split("?")[0] == f"{BASE_URL}{endpoint}"
        assert request.headers["Ocp-Apim-Subscription-Key"] == API_KEY
        assert params_of(request) == {
            "response_format": "geojson",
            "z": str(zoom_levels[0]),
            "x": "1819",
            "y": "806",
        }

    @pytest.mark.parametrize(
        ("method_name", "endpoint", "zoom_levels"), TILE_ONLY_ENDPOINTS, ids=TILE_ONLY_ENDPOINT_IDS
    )
    def test_it_accepts_every_zoom_level_its_manual_page_documents(
        self, mock_api, client, method_name, endpoint, zoom_levels
    ):
        for _ in zoom_levels:
            mock_api.get(f"{BASE_URL}{endpoint}", json=DUMMY_RESPONSE)

        for z in zoom_levels:
            getattr(client, method_name)(z=z, x=1819, y=806)

        assert len(mock_api.calls) == len(zoom_levels)

    @pytest.mark.parametrize(
        ("method_name", "endpoint", "zoom_levels"), TILE_ONLY_ENDPOINTS, ids=TILE_ONLY_ENDPOINT_IDS
    )
    def test_it_refuses_a_zoom_level_outside_that_range(self, mock_api, client, method_name, endpoint, zoom_levels):
        for z in (zoom_levels.start - 1, zoom_levels[-1] + 1):
            with pytest.raises(ValueError, match=endpoint):
                getattr(client, method_name)(z=z, x=1819, y=806)

    def test_the_endpoints_taking_thirteen_and_up_are_the_documented_ones(self, client):
        """Pinned as a set so that a range copied from the neighbouring method is visible.

        These four differ from the rest, and nothing about a wrong range shows up in a
        response: the request simply never leaves.
        """
        narrower = {endpoint for _, endpoint, levels in TILE_ONLY_ENDPOINTS if levels.start == 13}

        assert narrower == {"XKT006", "XKT007", "XKT010", "XKT018"}

    def test_a_tile_from_the_helpers_reaches_every_one_of_them(self, mock_api, client):
        """`*tile` has to keep working as endpoints are added, not just for the first three."""
        tile = tiles.containing(lon=139.7016, lat=35.6580, z=15)

        for _, endpoint, _ in TILE_ONLY_ENDPOINTS:
            mock_api.get(f"{BASE_URL}{endpoint}", json=DUMMY_RESPONSE)

        for method_name, _, _ in TILE_ONLY_ENDPOINTS:
            getattr(client, method_name)(*tile)

        assert len(mock_api.calls) == len(TILE_ONLY_ENDPOINTS)
