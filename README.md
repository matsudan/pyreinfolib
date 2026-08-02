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

## Usage

```python
import os

from pyreinfolib import Client

client = Client(api_key=os.environ["REINFOLIB_API_KEY"])
```

引数を省略または `None` を渡すと、その絞り込みを行いません。例えば `get_real_estate_prices(year=2024)` は全国のデータが対象になります。

空文字を渡した場合は省略と同じ扱いでなく `ValueError` になります。フォームや環境変数の値をそのまま渡す場合は `city=value or None` としてください。またコードのリストが空（`land_type_code=[]`）の場合も `ValueError` になります。

`Client` はコネクションを再利用します。タイル系APIを複数タイル分呼ぶような使い方では、TLSハンドシェイクが1回で済みます。使い終わったら `close()` するか、`with` を使ってください。

```python
with Client(api_key=os.environ["REINFOLIB_API_KEY"]) as client:
    client.get_municipalities(area="13")
```

### リトライ

スロットリング（HTTP 429）と一時的なサーバエラー（500、502、503、504）は自動で再試行します。APIはリクエスト数の明確な上限を公開しておらず、間隔を空けて実行するよう案内しています。429 は障害ではなく想定される応答です。

待ち時間は指数的に伸びます。既定の `max_retries=3` では 0秒、2秒、4秒の順に待ち、4回目で諦めて `RateLimitError` を送出します。APIが `Retry-After` を返した場合はそちらが優先されます。

```python
# 再試行しない
client = Client(api_key=..., max_retries=0)
```

検索結果0件（HTTP 404）は再試行しません。`timeout` 引数は各試行を制限するもので、再試行の全体を制限するものではありません。

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

### 引数がタイル座標のみのAPI

タイル座標のみを取る以下のAPIは、引数が `z`, `x`, `y` だけです。

| メソッド | ID | データ | ズーム |
|---|---|---|---|
| `get_city_planning_areas_and_area_classification` | XKT001 | 都市計画区域/区域区分 | 11〜15 |
| `get_use_districts` | XKT002 | 用途地域 | 11〜15 |
| `get_location_normalization_plans` | XKT003 | 立地適正化計画 | 11〜15 |
| `get_schools` | XKT006 | 学校 | 13〜15 |
| `get_nursery_schools_and_kindergartens_etc` | XKT007 | 保育園・幼稚園等 | 13〜15 |
| `get_medical_institutions` | XKT010 | 医療機関 | 13〜15 |
| `get_future_population_estimates_by_250m_mesh` | XKT013 | 将来推計人口250mメッシュ | 11〜15 |
| `get_fire_prevention_districts_and_quasi_fire_prevention_districts` | XKT014 | 防火・準防火地域 | 11〜15 |
| `get_number_of_passengers_per_station` | XKT015 | 駅別乗降客数 | 11〜15 |
| `get_municipal_offices_and_public_meeting_facilities_etc` | XKT018 | 市区町村役場及び集会施設等 | 13〜15 |
| `get_district_plans` | XKT023 | 地区計画 | 11〜15 |
| `get_high_level_use_districts` | XKT024 | 高度利用地区 | 11〜15 |
| `get_expected_flood_inundation_areas_at_maximum_scale` | XKT026 | 洪水浸水想定区域（想定最大規模） | 14〜15 |
| `get_expected_storm_surge_inundation_areas` | XKT027 | 高潮浸水想定区域 | 13〜15 |
| `get_expected_tsunami_inundation` | XKT028 | 津波浸水想定 | 14〜15 |
| `get_sediment_disaster_alert_areas` | XKT029 | 土砂災害警戒区域 | 11〜15 |
| `get_city_planning_roads` | XKT030 | 都市計画道路 | 11〜15 |
| `get_designated_emergency_evacuation_sites` | XGT001 | 指定緊急避難場所 | 11〜15 |

```python
from pyreinfolib import tiles

client.get_use_districts(*tiles.containing(lon=139.7016, lat=35.6580, z=15))
```

### 行政区域コードでフィルタ可能なAPI

以下のAPIはタイル座標に加えて `administrative_area_code`（行政区域コード、5桁）を取ります。**任意**なので、省略すればタイル全体が返ります。

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

### 地すべり防止地区

`get_landslide_prevention_districts`（XKT021）は都道府県コードと行政コードで絞り込めます。どちらも任意です。

```python
client.get_landslide_prevention_districts(z=11, x=1819, y=806, prefecture_code="22")
```

**こちらの都道府県コードは先頭の0を付けます。** XKT019 とは逆で、静岡県は `"22"`、栃木県は `"09"` です。引数名も型も同じなので、区別はエンドポイントだけです。マニュアルの記載がそうなっているため、そのまま従っています。

## タイル座標

公開APIの多くは XYZ タイル座標で引きます。経度、緯度 (longitude, latitude) から変換するために `pyreinfolib.tiles` を用意しています。

### 点を含むタイル取得 (containing)

```python
from pyreinfolib import tiles

tile = tiles.containing(lon=139.7016, lat=35.6580, z=15)
# Tile(z=15, x=29099, y=12905)

client.get_number_of_passengers_per_station(*tile)
```

`Tile` は `z, x, y` の順なので、タイル系メソッドにそのまま展開して渡せます。

受け付けるズームレベルはエンドポイントごとに違います。9〜15、11〜15、13〜15、14〜15 の4種類があり、多くは11〜15です。最も広いのは `get_natural_park_areas` と `get_densely_inhabited_districts` の9〜15、最も狭いのは `get_expected_flood_inundation_areas_at_maximum_scale` と `get_expected_tsunami_inundation` の14〜15です。上の表の「ズーム」列に載せています。

範囲外を渡すと、どのエンドポイントが何を期待しているかを含む `ValueError` になります。`tiles` 側はエンドポイントを知らないのでそこでは検証しません。

引数は名前を付けて渡します（位置引数では渡せません）。緯度と経度はどちらも `float` なので、順序を取り違えても型では気づけないためです。

### 指定範囲を覆うタイル取得 (covering / count_covering)

```python
box = {"west": 139.665, "south": 35.640, "east": 139.724, "north": 35.679}

print(tiles.count_covering(**box, z=15))  # 30

for tile in tiles.covering(**box, z=15):
    client.get_real_estate_prices_point(*tile, period_from=20241, period_to=20242)
```

範囲を指定して、それを覆うタイルを取得したいケースです。
例えばズーム15ではタイル1枚が約1km四方で、渋谷区の範囲を取得したい場合30枚ほどになります。

`covering()` はイテレータを返します。1タイルが1リクエストであり、APIは間隔を空けた呼び出しを求めているため、呼び出し側がペースを制御したり途中で止められる形にしています。

タイル数はズームと範囲で桁が変わります。着手前に `count_covering()` で確認してください。引数は `covering()` と同じです。

| 範囲 | z=11 | z=13 | z=15 |
|---|---|---|---|
| 渋谷区 | 1 | 4 | 30 |
| 東京23区 | 9 | 90 | 1155 |
| 東京都（本土） | 28 | 288 | 4186 |

### タイル範囲取得 (bounds)

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

### APIのレスポンス結果が0件の場合

タイル座標を取らないAPI（`get_real_estate_prices`、`get_municipalities`、`get_appraisal_reports`）は、条件に合致するデータが無い場合に空の結果ではなく **HTTP 404** を返します（[API操作説明](https://www.reinfolib.mlit.go.jp/help/apiManual/)の3章 Q.8）。このライブラリではこれを `NoResultsError` として送出します。

```python
from pyreinfolib import Client, NoResultsError

client = Client(api_key=...)
try:
    prices = client.get_real_estate_prices(year=2024, city="13109")
except NoResultsError:
    prices = {"data": []}
```

タイル座標を取るAPIは0件でも200と空のフィーチャ一覧を返すため、`NoResultsError` は発生しません。

### APIError の内容を見る

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
以下のように別の型にしてあるので取り違えは型チェックで検出されます。誤ったコードを送っても API はエラーではなく絞り込まれた結果や空の結果を返すため、実行時には気づきにくい種類の間違いです。

| enum | 対象 | コード |
|---|---|---|
| `PriceClassification` | 不動産価格（XIT001、XPT001） | `01` 不動産取引価格情報 / `02` 成約価格情報 |
| `LandPriceClassification` | 地価公示・地価調査（XPT002） | `0` 地価公示 = `LAND_MARKET_VALUE_PUBLICATION` / `1` 都道府県地価調査 = `PREFECTURAL_LAND_MARKET_VALUE_RESEARCH` |

### レスポンスの型

返り値にも型が付いています。各メソッドのレスポンスの形を `pyreinfolib.types` に `TypedDict` で置いています。

```python
prices = client.get_real_estate_prices(year=2024, city="13109")

for record in prices["data"]:
    print(record["TradePrice"])
    print(record["TradePirce"])  # 型エラー
```

型名はメソッド名から機械的に決まります。変数や自作関数に注釈を付けるときに使ってください。

```python
from pyreinfolib.types import RealEstatePricesItem, UseDistrictsResponse


def total(records: list[RealEstatePricesItem]) -> int:
    return sum(int(r["TradePrice"]) for r in records)


districts: UseDistrictsResponse = client.get_use_districts(z=15, x=29099, y=12905)
```

| 接尾辞 | 対象 | 例 |
|---|---|---|
| `Response` | 返り値そのもの | `UseDistrictsResponse` |
| `Properties` | タイル系の1フィーチャの `properties` | `UseDistrictsProperties` |
| `Item` | 非タイル系の `data` の1要素 | `RealEstatePricesItem` |

**キーは API のタグ名そのままです。** 各エンドポイントのマニュアル個別ページの `＜出力＞` 表にあるタグ名を、整えずに使っています。国土数値情報の属性コード（`A27_001`）、ローマ字（`kubun_id`）、`_ja` 接尾辞、XCT001 の日本語キー（全角スペース入り）、XPT002 の `proximity_to_transportation_facilitites`（API 側の綴り間違い）も、そのままです。直すと存在しないキーになります。

値の型もマニュアルの宣言通りです。XIT001 は取引価格を含めて全フィールドが文字列型なので、`record["TradePrice"]` は `str` です。同じ `kubun_id` が XKT001 では `int`、XKT023 では `str` なのも、マニュアルの記載がそうなっているためです。

**どのキーが必ず来るかはマニュアルに記載がないため、全フィールドを省略可能として扱っています。** 読み取りは型チェックを通りますが、実行時に `KeyError` の可能性は残ります。null になりうるかも記載がないので表現していません。

`geometry` は6種のジオメトリの合併型で、`type` で絞り込んでから `coordinates` を読みます。XKT029 は同一エンドポイントでポリゴンとラインが混在するとマニュアルが明記しているので、エンドポイントごとに1種類とは決められません。

```python
for feature in client.get_schools(z=13, x=7269, y=3235)["features"]:
    geometry = feature["geometry"]
    if geometry is not None and geometry["type"] == "Point":
        lon, lat = geometry["coordinates"][0], geometry["coordinates"][1]
```

`get_future_population_estimates_by_250m_mesh`（XKT013）だけは `properties` が `dict[str, Any]` です。`PT01_20XX` のようにフィールド名が年を含み、マニュアルがその年をプレースホルダで書いているためです。

> [!NOTE]
> 0.6.0 以前は全メソッドが `dict[str, Any]` を返していました。返り値を `dict[str, Any]` と注釈していた場合、`TypedDict` は `dict[str, Any]` に代入できないため型チェックが落ちます。注釈を外すか、対応する `...Response` に差し替えてください。実行時の挙動は変わりません。

## Contributing

メソッド名や enum メンバー名は、API 操作説明の API 名から機械的に導出しています。導出手順と訳語の用語集は [CONTRIBUTING.md](CONTRIBUTING.md) にあります。

## Author

@matsudan (daaamatsun@gmail.com)
