import os

import requests


class Client:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.reinfolib.mlit.go.jp/ex-api/external"

    def __get(self, endpoint: str, params: dict = None) -> dict:

        api_url = os.path.join(self.base_url, endpoint)
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        try:
            r = requests.get(api_url, headers=headers, params=params)
            r.raise_for_status()
        except requests.RequestException as e:
            raise SystemExit(e)

        return r.json()

    def get_municipalities(self, area: int, language: str = None) -> dict:
        """Get municipality (city/ward/town/village) list.
        See https://www.reinfolib.mlit.go.jp/help/apiManual/#titleApi5 for details.
        :param area: Prefecture code. See https://nlftp.mlit.go.jp/ksj/gml/codelist/PrefCd.html
        :param language: `ja` or `en`. If not specified, `ja`.
        :return:
        """
        params = {"area": area}
        if language:
            params.update(language=language)

        return self.__get("XIT002", params)
