import logging
from urllib.parse import urljoin

import requests

from pyreinfolib import enums

logger = logging.getLogger(__name__)

class Client:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.reinfolib.mlit.go.jp/ex-api/external"

    def _get(self, endpoint: str, params: dict = None) -> dict:

        api_url = urljoin(self.base_url, endpoint)
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        try:
            r = requests.get(api_url, headers=headers, params=params)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            logger.error(f"Request failed for {api_url} with error: {e.response.text}")
            raise

    def get_real_estate_prices(
        self,
        year: int,
        price_classification: str = None,
        quarter: int = None,
        area: str = None,
        city: str = None,
        station: str = None,
        language: str = None
    ) -> dict:
        """Get real estate prices. See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi4 for details.
        :param price_classification: Price classification code.
          01: Real estate transaction price information, 02: Contract price information,
          Unspecified: Both transaction price information and contract price information.
        :param year: Transaction period (Year).
        :param quarter: Transaction period (Quarter). 1 ~ 4
        :param area: Prefecture code. See https://nlftp.mlit.go.jp/ksj/gml/codelist/PrefCd.html
        :param city: Municipality code.
        :param station: Station code. See https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-N02-v3_1.html
        :param language: `ja` or `en`. If not specified, `ja`.
        :return: Real estate prices.
        """
        params = {"year": year}
        if price_classification:
            params["priceClassification"] = price_classification
        if quarter:
            params["quarter"] = quarter
        if area:
            params["area"] = area
        if city:
            params["city"] = city
        if station:
            params["station"] = station
        if language:
            params["language"] = language

        return self.__get("XIT001", params)

    def get_municipalities(self, area: str, language: str = None) -> dict:
        """Get municipality (city/ward/town/village) list.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi5 for details.
        :param area: Prefecture code. See https://nlftp.mlit.go.jp/ksj/gml/codelist/PrefCd.html
        :param language: `ja` or `en`. If not specified, `ja`.
        :return: Municipality list.
        """
        params = {"area": area}
        if language:
            params.update(language=language)

        return self.__get("XIT002", params)

    def get_appraisal_reports(self, year: int, area: str, division: enums.UseDivision):
        """Get real estate appraisal reports.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi6 for details.
        :param year: Date of value.
        :param area: Prefecture code.
        :param division: Use division.
        :return: Real estate appraisal reports.
        """
        params = {"year": year, "area": area, "division": division}

        return self.__get("XCT001", params)
