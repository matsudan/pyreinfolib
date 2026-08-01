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

`Client` はコネクションを再利用します。タイル系APIを複数タイル分呼ぶような使い方では、TLSハンドシェイクが1回で済みます。使い終わったら `close()` するか、`with` を使ってください。

```python
with Client(api_key=os.environ["REINFOLIB_API_KEY"]) as client:
    client.get_municipalities(area="13")
```

### リトライ

スロットリング（HTTP 429）と一時的なサーバエラー（500、502、503、504）は自動で再試行します。APIはリクエスト数の明確な上限を公開しておらず、間隔を空けて実行するよう案内しているため、429 は障害ではなく想定される応答です。

待ち時間は指数的に伸びます。既定の `max_retries=3` では 0秒、2秒、4秒の順に待ち、4回目で諦めて `RateLimitError` を送出します。APIが `Retry-After` を返した場合はそちらが優先されます。

```python
# 再試行しない
client = Client(api_key=..., max_retries=0)
```

検索結果0件（HTTP 404）は再試行しません。`timeout` は各試行を制限するもので、再試行の全体を制限するものではありません。

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

## タイル座標

公開APIの多くは場所ではなく XYZ タイル座標で引きます。緯度経度から変換するために `pyreinfolib.tiles` を用意しています。ネットワークもAPIキーも不要な純粋関数です。

```python
from pyreinfolib import tiles

tile = tiles.containing(lon=139.7016, lat=35.6580, z=15)
# Tile(z=15, x=29099, y=12905)

client.get_number_of_passengers_per_station(*tile)
```

`Tile` は `z, x, y` の順なので、タイル系メソッドにそのまま展開して渡せます。

受け付けるズームレベルはエンドポイントごとに違います（多くは11〜15、`get_land_price_public_notices_and_surveys_point` は13〜15）。範囲外を渡すと、どのエンドポイントが何を期待しているかを含む `ValueError` になります。`tiles` 側はエンドポイントを知らないので、そこでは検証しません。

引数はキーワード専用です。GeoJSON や地図系ライブラリは経度を先に置きますが、日本の利用者は緯度経度の順で考えるため、順序を記憶に頼らせない形にしています。

### 範囲を覆う

1点1タイルでは足りない場合が普通です。ズーム15ではタイル1枚が約1km四方なので、区一つで30枚になります。

```python
box = {"west": 139.665, "south": 35.640, "east": 139.724, "north": 35.679}

print(tiles.count_covering(**box, z=15))  # 30

for tile in tiles.covering(**box, z=15):
    client.get_real_estate_prices_point(*tile, period_from=20241, period_to=20242)
```

`covering()` はイテレータを返します。1タイルが1リクエストであり、APIは間隔を空けた呼び出しを求めているため、呼び出し側がペースを制御したり途中で止められる形にしています。

タイル数は急激に増えます。着手前に `count_covering()` で確認してください。

| 範囲 | z=11 | z=13 | z=15 |
|---|---|---|---|
| 渋谷区 | 1 | 4 | 30 |
| 東京23区 | 9 | 90 | 1155 |
| 東京都（本土） | 28 | 288 | 4186 |

### タイルの範囲を得る

```python
tiles.bounds(tile)
# Bounds(west=139.691162109375, south=35.65729624809628, east=139.7021484375, north=35.66622234103478)
```

`Bounds` は GeoJSON の bbox と同じ west, south, east, north の順です。

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
