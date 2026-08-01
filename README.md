# pyreinfolib

[![PyPI](https://img.shields.io/pypi/v/pyreinfolib)](https://pypi.org/project/pyreinfolib/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyreinfolib)](https://pypi.org/project/pyreinfolib/)
[![ci](https://github.com/matsudan/pyreinfolib/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/matsudan/pyreinfolib/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/pypi/l/pyreinfolib)](https://github.com/matsudan/pyreinfolib/blob/main/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

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

引数を省略する、または `None` を渡すと、その絞り込みを行いません。`get_real_estate_prices(year=2024)` は全国が対象になります。

空文字を渡した場合は `ValueError` になります。省略と同じ扱いにはしません。`city=""` を絞り込みのつもりで渡したときに、黙って全国が返ることを避けるためです。フォームや環境変数の値をそのまま渡す場合は `city=value or None` としてください。同様に、コードのリストが空（`land_type_code=[]`）の場合も `ValueError` です。絞り込んだ結果が0件になったことは、全種類を要求することとは違うためです。

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

### タイル座標だけで引くAPI

タイル座標のみを取る13本は、引数が `z`, `x`, `y` だけです。

| メソッド | ID | データ | ズーム |
|---|---|---|---|
| `get_city_planning_areas_and_area_classification` | XKT001 | 都市計画区域/区域区分 | 11〜15 |
| `get_use_districts` | XKT002 | 用途地域 | 11〜15 |
| `get_schools` | XKT006 | 学校 | 13〜15 |
| `get_nursery_schools_and_kindergartens_etc` | XKT007 | 保育園・幼稚園等 | 13〜15 |
| `get_medical_institutions` | XKT010 | 医療機関 | 13〜15 |
| `get_future_population_estimates_by_250m_mesh` | XKT013 | 将来推計人口250mメッシュ | 11〜15 |
| `get_fire_prevention_districts_and_quasi_fire_prevention_districts` | XKT014 | 防火・準防火地域 | 11〜15 |
| `get_number_of_passengers_per_station` | XKT015 | 駅別乗降客数 | 11〜15 |
| `get_municipal_offices_and_public_meeting_facilities_etc` | XKT018 | 市区町村役場及び集会施設等 | 13〜15 |
| `get_district_plans` | XKT023 | 地区計画 | 11〜15 |
| `get_high_level_use_districts` | XKT024 | 高度利用地区 | 11〜15 |
| `get_city_planning_roads` | XKT030 | 都市計画道路 | 11〜15 |
| `get_designated_emergency_evacuation_sites` | XGT001 | 指定緊急避難場所 | 11〜15 |

```python
from pyreinfolib import tiles

client.get_use_districts(*tiles.containing(lon=139.7016, lat=35.6580, z=15))
```

### 行政区域コードで絞り込めるAPI

次の6本はタイル座標に加えて `administrative_area_code`（行政区域コード、5桁）を取ります。**任意**なので、省略すればタイル全体が返ります。

| メソッド | ID | データ | ズーム |
|---|---|---|---|
| `get_elementary_school_districts` | XKT004 | 小学校区 | 11〜15 |
| `get_junior_high_school_districts` | XKT005 | 中学校区 | 11〜15 |
| `get_welfare_facilities` | XKT011 | 福祉施設 | 13〜15 |
| `get_disaster_risk_areas` | XKT016 | 災害危険区域 | 11〜15 |
| `get_libraries` | XKT017 | 図書館 | 13〜15 |
| `get_densely_inhabited_districts` | XKT031 | 人口集中地区 | 9〜15 |

`get_disaster_risk_areas` のコードは**代表**行政コードです。複数の市区町村にまたがる区域には、そのうち1つのコードしか付きません。

```python
client.get_libraries(*tiles.containing(lon=139.7016, lat=35.6580, z=15))

# 1つでも、複数でも渡せます
client.get_elementary_school_districts(z=11, x=1819, y=806, administrative_area_code="13102")
client.get_elementary_school_districts(z=11, x=1819, y=806, administrative_area_code=["01101", "13102"])
```

不動産取引価格情報の `city` と同じ市区町村コードですが、APIが `administrativeAreaCode` と綴っているため引数名も分けています。

`get_welfare_facilities` は施設種別でも絞り込めます。大分類・中分類・小分類の3階層で、いずれも任意です。

```python
client.get_welfare_facilities(
    z=13,
    x=7312,
    y=3008,
    welfare_facility_class_code=["02", "05"],  # 老人福祉施設、児童福祉施設等
)
```

コード表は[大分類](https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMajorClassificationCode.html)、[中分類](https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMiddleClassificationCode.html)、[小分類](https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMinorClassificationCode.html)にあります。enum ではなく `str` です。中分類62件・小分類122件という規模に加えて、大分類7件のうち2件に公表された英訳がないためです（[CONTRIBUTING.md](CONTRIBUTING.md#enum-にするか-str-にするか)）。

### 自然公園地域

`get_natural_park_areas`（XKT019）はズーム9〜15で、都道府県コードと地区コード（振興局区域）で絞り込めます。どちらも任意です。

```python
client.get_natural_park_areas(z=9, x=227, y=100, prefecture_code=["9", "11"])
```

**このAPIのコードは先頭の0を付けません。** 栃木県は `"9"` で、`"09"` ではありません。不動産取引価格情報の `area` は `"09"` の形式なので、同じ都道府県コードでも綴りが違います。マニュアルが定めている形式なので、`"09"` を渡すと `ValueError` になります。API に送ると認識されないコードとして空のタイルが返り、自然公園がないタイルと区別が付かなくなるためです。

## タイル座標

公開APIの多くは場所ではなく XYZ タイル座標で引きます。緯度経度から変換するために `pyreinfolib.tiles` を用意しています。ネットワークもAPIキーも不要な純粋関数です。

```python
from pyreinfolib import tiles

tile = tiles.containing(lon=139.7016, lat=35.6580, z=15)
# Tile(z=15, x=29099, y=12905)

client.get_number_of_passengers_per_station(*tile)
```

`Tile` は `z, x, y` の順なので、タイル系メソッドにそのまま展開して渡せます。

受け付けるズームレベルはエンドポイントごとに違います（多くは11〜15、`get_land_market_value_publication_and_research_point` は13〜15）。範囲外を渡すと、どのエンドポイントが何を期待しているかを含む `ValueError` になります。`tiles` 側はエンドポイントを知らないので、そこでは検証しません。

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
| `LandPriceClassification` | 地価公示・地価調査（XPT002） | `0` 地価公示 = `LAND_MARKET_VALUE_PUBLICATION` / `1` 都道府県地価調査 = `PREFECTURAL_LAND_MARKET_VALUE_RESEARCH` |

別の型にしてあるので、取り違えは型チェックで検出されます。誤ったコードを送った場合、API はエラーではなく絞り込まれた結果や空の結果を返すため、実行時には気づきにくい種類の間違いです。

## Contributing

メソッド名や enum メンバー名は、API 操作説明の API 名から機械的に導出しています。導出手順と訳語の用語集は [CONTRIBUTING.md](CONTRIBUTING.md) にあります。

## Author

@matsudan (daaamatsun@gmail.com)
