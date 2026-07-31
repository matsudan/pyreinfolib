import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest
import requests
import responses

from pyreinfolib import Client
from pyreinfolib.enums import LandTypeCode, UseDivision

BASE_URL = "https://www.reinfolib.mlit.go.jp/ex-api/external/"
API_KEY = "dummy"
DUMMY_RESPONSE = {"status": "OK", "data": []}
DEFAULT_TIMEOUT = 30.0


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
    return Client(api_key=API_KEY)


def assert_request(mock_api: responses.RequestsMock, method: Callable, endpoint: str, case: RequestCase) -> None:
    """Call `method` with the case arguments and assert the request it produced."""
    url = f"{BASE_URL}{endpoint}"
    mock_api.get(url, json=DUMMY_RESPONSE)

    assert method(**case.args) == DUMMY_RESPONSE

    assert len(mock_api.calls) == 1
    request = mock_api.calls[0].request
    assert request.url.split("?")[0] == url
    assert request.headers["Ocp-Apim-Subscription-Key"] == API_KEY
    assert request.params == case.expected_params


class TestClient:
    def test_init(self):
        client = Client(api_key="dummy")
        assert client.api_key == "dummy"
        assert client.base_url == BASE_URL
        assert client.timeout == DEFAULT_TIMEOUT

    def test_init_accepts_custom_timeout(self):
        assert Client(api_key="dummy", timeout=5).timeout == 5
        assert Client(api_key="dummy", timeout=(3.0, 10.0)).timeout == (3.0, 10.0)

    @pytest.mark.parametrize("api_key", ["", None], ids=["empty string", "None"])
    def test_init_rejects_an_empty_api_key(self, api_key):
        """`None` covers `Client(os.getenv("TYPO"))`, which would otherwise only fail as a 401."""
        with pytest.raises(ValueError, match="api_key"):
            Client(api_key=api_key)

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

    @pytest.mark.parametrize("status", [400, 404, 500])
    def test__get_raises_on_error_status(self, mock_api, client, status):
        mock_api.get(f"{BASE_URL}TEST999", json={"message": "検索結果がありません。"}, status=status)

        with pytest.raises(requests.RequestException):
            client._get("TEST999", {"param1": "value1"})

    def test__get_logs_response_body_on_error_status(self, mock_api, client, caplog):
        # Registered as a raw body rather than `json=`, which would escape the non-ASCII
        # characters and no longer match what the API actually returns.
        mock_api.get(
            f"{BASE_URL}TEST999",
            body='{"message":"検索結果がありません。"}',
            content_type="application/json",
            status=400,
        )

        with caplog.at_level(logging.ERROR, logger="pyreinfolib.client"), pytest.raises(requests.RequestException):
            client._get("TEST999")

        assert "検索結果がありません。" in caplog.text

    @pytest.mark.parametrize(
        "raised",
        [
            requests.ConnectionError("connection refused"),
            requests.Timeout("timed out"),
        ],
        ids=lambda exc: type(exc).__name__,
    )
    def test__get_propagates_errors_that_carry_no_response(self, mock_api, client, caplog, raised):
        """`e.response` is None here, so the handler must not dereference it.

        Dereferencing it replaced the real cause with `AttributeError: 'NoneType' object
        has no attribute 'text'`, which is exactly the case one needs to debug.
        """
        mock_api.get(f"{BASE_URL}TEST001", body=raised)

        with caplog.at_level(logging.ERROR, logger="pyreinfolib.client"), pytest.raises(type(raised)) as exc_info:
            client._get("TEST001")

        assert exc_info.value.response is None
        assert str(raised) in caplog.text

    def test__get_propagates_json_decode_error(self, mock_api, client, caplog):
        """A 200 response with a non-JSON body (a maintenance page, say) also has no `response`."""
        mock_api.get(f"{BASE_URL}TEST001", body="<html>maintenance</html>", content_type="text/html")

        with caplog.at_level(logging.ERROR, logger="pyreinfolib.client"):
            with pytest.raises(requests.exceptions.JSONDecodeError):
                client._get("TEST001")

        assert f"Request failed for {BASE_URL}TEST001" in caplog.text

    @pytest.mark.parametrize(
        "case",
        [
            RequestCase(
                id="all params",
                args={
                    "year": 2025,
                    "price_classification": "01",
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
                id="optional params are omitted when falsy",
                args={"year": 2025, "price_classification": None, "quarter": None, "city": ""},
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
                    "price_classification": "01",
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
                    "price_classification": "0",
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
    def test_get_land_price_public_notices_and_surveys_point(self, mock_api, client, case):
        assert_request(mock_api, client.get_land_price_public_notices_and_surveys_point, "XPT002", case)

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
