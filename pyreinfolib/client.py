import logging
from typing import Literal
from urllib.parse import urljoin

import requests

from pyreinfolib import enums

logger = logging.getLogger(__name__)

class Client:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.reinfolib.mlit.go.jp/ex-api/external/"

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
        price_classification: Literal["01", "02"] = None,
        quarter: Literal[1, 2, 3, 4] = None,
        area: str = None,
        city: str = None,
        station: str = None,
        language: Literal["ja", "en"] = None
    ) -> dict:
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

        return self._get("XIT001", params)

    def get_municipalities(self, area: str, language: Literal["ja", "en"] = None) -> dict:
        """Get municipality (city/ward/town/village) list.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi5 for details.
        :param area: Prefecture code. See https://nlftp.mlit.go.jp/ksj/gml/codelist/PrefCd.html
        :param language: `ja` or `en`. If not specified, `ja`.
        :return: Municipality list.
        """
        params = {"area": area}
        if language:
            params.update(language=language)

        return self._get("XIT002", params)

    def get_appraisal_reports(self, year: int, area: str, division: enums.UseDivision):
        """Get real estate appraisal reports.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi6 for details.
        :param year: Date of value.
        :param area: Prefecture code.
        :param division: Use division.
        :return: Real estate appraisal reports.
        """
        params = {"year": year, "area": area, "division": division}

        return self._get("XCT001", params)

    def get_real_estate_prices_point(
        self,
        z: int,
        x: int,
        y: int,
        period_from: int,
        period_to: int,
        price_classification: Literal["01", "02"] = None,
        land_type_code: list[enums.LandTypeCode] = None,
    ) -> dict:
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
        :param land_type_code: Land type code. See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi7
        :return: Real estate prices point. (Response format: GeoJson)
        """
        params = {"response_format": "geojson", "z": z, "x": x, "y": y, "from": period_from, "to": period_to}
        if price_classification:
            params["priceClassification"] = price_classification
        if land_type_code:
            params["landTypeCode"] = ",".join(land_type_code)

        return self._get("XPT001", params)

    def get_land_price_public_notices_and_surveys_point(
        self,
        z: Literal[13,14,15],
        x: int,
        y: int,
        year: int,
        price_classification: Literal["0", "1"] = None,
        use_category_code: list[enums.UseDivision] = None,
    ) -> dict:
        """Get land price public notices (standard land prices) and
        prefectural land price surveys (benchmark land prices) point.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi8 for details.
        :param z: Zoom level (scale). 13 ~ 15 (detail)
        :param x: x value of tile coordinates.
        :param y: y value of tile coordinates.
        :param year: target year.
        :param price_classification: Land price classification code.
          0: Land price public notices, 1: Prefectural land price surveys, Unspecified: Both 0 and 1.
        :param use_category_code: Use division code. See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi8
        :return: land price public notices (standard land prices) and
        prefectural land price surveys (benchmark land prices) point. (Response format: GeoJson)
        """
        params = {"response_format": "geojson", "z": z, "x": x, "y": y, "year": year}
        if price_classification:
            params["priceClassification"] = price_classification
        if use_category_code:
            params["useCategoryCode"] = ",".join(use_category_code)

        return self._get("XPT002", params)
