# pyreinfolib

国土交通省[不動産情報ライブラリ](https://www.reinfolib.mlit.go.jp/)APIサービスのPythonクライアントです。API仕様についての詳細は[API操作説明ページ](https://www.reinfolib.mlit.go.jp/help/apiManual/)をご参照ください。

## Installation

```shell
pip install pyreinfolib
```

### Supported Python Versions

Python >= 3.11

## Usage

```python
import os

from pyreinfolib import Client

client = Client(api_key=os.environ["REINFOLIB_API_KEY"])
```


## Example

### 不動産価格（取引価格・成約価格）情報

```python
from pyreinfolib.enums import PriceClassification

client.get_real_estate_prices(
    year=2024,
    quarter=1,
    price_classification=PriceClassification.REAL_ESTATE_TRANSACTION_PRICE,
    city="13109",
)
```

### 鑑定評価書情報

```python
from pyreinfolib.enums import UseDivision

client.get_appraisal_reports(year=2024, area="13", division=UseDivision.INDUSTRIAL_LAND)
```

## Error handling

このライブラリが送出する例外はすべて `ReinfolibError` を継承しています。`requests` を import せずに捕捉できます。

```
ReinfolibError
├── TransportError          レスポンスを得られなかった（接続失敗・タイムアウト）
└── APIError                レスポンスは返ったが利用できない（status_code / response_body / url を持つ）
    ├── AuthenticationError APIキーが未指定または拒否された（401）
    ├── NoResultsError      検索結果が0件（404）
    ├── RateLimitError      同一APIキーからのリクエストが多すぎる（429）
    └── InvalidResponseError レスポンスがJSONではなかった
```

### 検索結果が0件のとき

タイル座標を取らない3つのAPI（`get_real_estate_prices`、`get_municipalities`、`get_appraisal_reports`）は、条件に合致するデータが無い場合に空の結果ではなく **HTTP 404** を返します（[API操作説明](https://www.reinfolib.mlit.go.jp/help/apiManual/)の3章 Q.8）。このライブラリではこれを `NoResultsError` として送出します。

```python
from pyreinfolib import Client, NoResultsError

client = Client(api_key=...)
try:
    prices = client.get_real_estate_prices(year=2024, city="13109")
except NoResultsError:
    prices = {"data": []}
```

タイル座標を取るAPIは0件でも200と空のフィーチャ一覧を返すため、`NoResultsError` は発生しません。

### 失敗の詳細を見る

`APIError` とそのサブクラスは、APIが返した本文を保持しています。

```python
from pyreinfolib import APIError

try:
    client.get_municipalities(area="99")
except APIError as e:
    print(e.status_code, e.response_body, e.url)
```

## Typing

型情報を同梱しています（[PEP 561](https://peps.python.org/pep-0561/)）。

`price_classification`、`division`、`land_type_code`、`use_category_code` には `pyreinfolib.enums` の enum メンバーを渡してください。`StrEnum` なので実行時は文字列でも動きますが、型チェックでは拒否されます。単一のコードはリストに包む必要はありません。

`price_classification` は API 上どのエンドポイントでも `priceClassification` という同じ名前ですが、コード体系は2つに分かれています。

| enum | 対象 | コード |
|---|---|---|
| `PriceClassification` | 不動産価格（XIT001、XPT001） | `01` 不動産取引価格情報 / `02` 成約価格情報 |
| `LandPriceClassification` | 地価公示・地価調査（XPT002） | `0` 地価公示 / `1` 都道府県地価調査 |

別の型にしてあるので、取り違えは型チェックで検出されます。誤ったコードを送った場合、API はエラーではなく絞り込まれた結果や空の結果を返すため、実行時には気づきにくい種類の間違いです。

## Contributing

メソッド名や enum メンバー名は、API 操作説明の API 名から機械的に導出しています。導出手順と訳語の用語集は [CONTRIBUTING.md](CONTRIBUTING.md) にあります。

## Author

@matsudan (daaamatsun@gmail.com)
