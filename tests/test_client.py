from dataclasses import dataclass
from unittest.mock import Mock, patch

import pytest
import requests

from pyreinfolib import Client
from pyreinfolib.enums import UseDivision


@dataclass
class BaseTestCase[E, X]:
    id: str
    args: dict
    expected: E | None = None
    error: X | None = None


class TestClient:
    def test_init(self):
        client = Client(api_key="dummy")
        assert client.api_key == "dummy"

    @patch("requests.get")
    @pytest.mark.parametrize(
        "test_case",
        [
            pytest.param(
                BaseTestCase(
                    id="Normal case",
                    args={
                        "endpoint": "TEST001",
                        "params": {"param1": "value1"},
                    },
                    expected={"status": "OK", "data": [{"test": "value"}]},
                    error=None,
                ),
            ),
            pytest.param(
                BaseTestCase(
                    id="Negative case",
                    args={
                        "endpoint": "TEST999",
                        "params": {"param1": "value1"},
                    },
                    expected=None,
                    error=requests.RequestException,
                ),
            ),
        ],
    )
    def test__get(self, mock_requests_get, test_case):
        client = Client(api_key="dummy")

        if test_case.error:
            mock_response = Mock()
            mock_response.text = '{"message":"検索結果がありません。"}'
            mock_requests_get.side_effect = test_case.error(response=mock_response)

            with pytest.raises(test_case.error):
                client._get(test_case.args["endpoint"], test_case.args["params"])

        else:
            expected = test_case.expected
            mock_response = Mock()
            mock_response.json.return_value = expected
            mock_requests_get.return_value = mock_response

            actual = client._get(test_case.args["endpoint"], test_case.args["params"])
            assert actual == expected
            mock_requests_get.assert_called_once_with(
                "https://www.reinfolib.mlit.go.jp/ex-api/external/TEST001",
                headers={"Ocp-Apim-Subscription-Key": "dummy"},
                params=test_case.args["params"],
            )

    @patch("pyreinfolib.client.Client._get")
    @pytest.mark.parametrize(
        "test_case",
        [
            pytest.param(
                BaseTestCase(
                    id="Normal case",
                    args={
                        "year": 2025,
                        "price_classification": "01",
                        "quarter": 1,
                        "city": "13109",
                        "language": "ja",
                    },
                    expected={
                        "status": "OK",
                        "data": [{"PriceCategory": "不動産取引価格情報", "Type": "中古マンション等"}]
                    },
                )
            )
        ],
    )
    def test_get_real_estate_prices(self, mock_get, test_case):
        mock_get.return_value = test_case.expected
        client = Client(api_key="dummy")
        actual = client.get_real_estate_prices(
            year=test_case.args["year"],
            price_classification=test_case.args["price_classification"],
            quarter=test_case.args["quarter"],
            city=test_case.args["city"],
            language=test_case.args["language"],
        )
        assert actual == test_case.expected

    @patch("pyreinfolib.client.Client._get")
    @pytest.mark.parametrize(
        "test_case",
        [
            pytest.param(
                BaseTestCase(
                    id="Normal case",
                    args={
                        "area": "13",
                        "language": "ja",
                    },
                    expected={"status": "OK", "data": [{"id": "13101", "name": "千代田区"}]},
                ),
            )
        ],
    )
    def test_get_municipalities(self, mock_get, test_case):
        mock_get.return_value = test_case.expected
        client = Client(api_key="dummy")
        actual = client.get_municipalities(test_case.args["area"], test_case.args["language"])
        assert actual == test_case.expected

    @patch("pyreinfolib.client.Client._get")
    @pytest.mark.parametrize(
        "test_case",
        [
            pytest.param(
                BaseTestCase(
                    id="normal_jp",
                    args={
                        "year": 2024,
                        "area": "13",
                        "division": UseDivision.INDUSTRIAL_LAND,
                    },
                    expected={"status": "OK", "data": [{"価格時点": "2024", "査定価格": "314000"}]},
                ),
            )
        ],
    )
    def test_get_appraisal_reports(self, mock_get, test_case):
        mock_get.return_value = test_case.expected
        client = Client(api_key="dummy")
        actual = client.get_appraisal_reports(
            test_case.args["year"], test_case.args["area"], test_case.args["division"]
        )
        assert actual == test_case.expected
