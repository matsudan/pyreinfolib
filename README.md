# pyreinfolib

[![PyPI](https://img.shields.io/pypi/v/pyreinfolib)](https://pypi.org/project/pyreinfolib/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyreinfolib)](https://pypi.org/project/pyreinfolib/)
[![ci](https://github.com/matsudan/pyreinfolib/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/matsudan/pyreinfolib/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/pypi/l/pyreinfolib)](https://github.com/matsudan/pyreinfolib/blob/main/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

国土交通省[不動産情報ライブラリ](https://www.reinfolib.mlit.go.jp/)APIサービスのPythonクライアントです。公開されている35本のAPIすべてに対応しています。

API仕様の詳細は[API操作説明ページ](https://www.reinfolib.mlit.go.jp/help/apiManual/)をご参照ください。APIキーは[利用申請](https://www.reinfolib.mlit.go.jp/help/apiManual/)で取得します。

## Installation

```shell
pip install pyreinfolib
```

## Quick start

```python
import os

from pyreinfolib import Client

client = Client(api_key=os.environ["REINFOLIB_API_KEY"])

# 2024年第1四半期、渋谷区の不動産取引価格
result = client.get_real_estate_prices(year=2024, quarter=1, city="13113")

for record in result["data"]:
    print(record["Type"], record["TradePrice"], record["Area"])
```

APIの多くは地図のタイル座標を指定して取得します。緯度経度からの変換は `pyreinfolib.tiles` が行います。

```python
from pyreinfolib import tiles

tile = tiles.containing(lon=139.7016, lat=35.6580, z=15)

for feature in client.get_use_districts(*tile)["features"]:
    print(feature["properties"]["use_area_ja"])
```

## Endpoints

### 都道府県・市区町村コードで取得するAPI

| データ | メソッド | ID | 引数 |
|---|---|---|---|
| 不動産価格（取引価格・成約価格）情報 | `get_real_estate_prices` | XIT001 | `year`、`price_classification`、`quarter`、`area`、`city`、`station`、`language` |
| 都道府県内市区町村一覧 | `get_municipalities` | XIT002 | `area`、`language` |
| 鑑定評価書情報 | `get_appraisal_reports` | XCT001 | `year`、`area`、`division` |

### タイル座標で取得するAPI

`z`, `x`, `y` は必須です。それ以外の引数はすべて任意で、省略するとタイル全体が返ります。

| データ | メソッド | ID | ズーム | `z`, `x`, `y` に加えて渡せる引数 |
|---|---|---|---|---|
| 不動産価格のポイント | `get_real_estate_prices_point` | XPT001 | 11〜15 | `period_from`、`period_to`、`price_classification`、`land_type_code` |
| 地価公示・地価調査のポイント | `get_land_market_value_publication_and_research_point` | XPT002 | 13〜15 | `year`、`price_classification`、`use_category_code` |
| 都市計画区域／区域区分 | `get_city_planning_areas_and_area_classification` | XKT001 | 11〜15 | — |
| 用途地域 | `get_use_districts` | XKT002 | 11〜15 | — |
| 立地適正化計画 | `get_location_normalization_plans` | XKT003 | 11〜15 | — |
| 小学校区 | `get_elementary_school_districts` | XKT004 | 11〜15 | `administrative_area_code` |
| 中学校区 | `get_junior_high_school_districts` | XKT005 | 11〜15 | `administrative_area_code` |
| 学校 | `get_schools` | XKT006 | 13〜15 | — |
| 保育園・幼稚園等 | `get_nursery_schools_and_kindergartens_etc` | XKT007 | 13〜15 | — |
| 医療機関 | `get_medical_institutions` | XKT010 | 13〜15 | — |
| 福祉施設 | `get_welfare_facilities` | XKT011 | 13〜15 | `administrative_area_code`、`welfare_facility_class_code`、`welfare_facility_middle_class_code`、`welfare_facility_minor_class_code` |
| 将来推計人口250mメッシュ | `get_population_projections_in_250m_grid_squares` | XKT013 | 11〜15 | — |
| 防火・準防火地域 | `get_fire_prevention_districts_and_quasi_fire_prevention_districts` | XKT014 | 11〜15 | — |
| 駅別乗降客数 | `get_number_of_passengers_per_station` | XKT015 | 11〜15 | — |
| 災害危険区域 | `get_disaster_risk_areas` | XKT016 | 11〜15 | `administrative_area_code` |
| 図書館 | `get_libraries` | XKT017 | 13〜15 | `administrative_area_code` |
| 市区町村役場及び集会施設等 | `get_municipal_offices_and_meeting_facilities_etc` | XKT018 | 13〜15 | — |
| 自然公園地域 | `get_natural_park_areas` | XKT019 | 9〜15 | `prefecture_code`、`district_code` |
| 大規模盛土造成地マップ | `get_large_scale_developed_embankments` | XKT020 | 11〜15 | — |
| 地すべり防止地区 | `get_landslide_prevention_districts` | XKT021 | 11〜15 | `prefecture_code`、`administrative_area_code` |
| 急傾斜地崩壊危険区域 | `get_steep_slope_failure_hazard_areas` | XKT022 | 11〜15 | `prefecture_code`、`administrative_area_code` |
| 地区計画 | `get_district_plans` | XKT023 | 11〜15 | — |
| 高度利用地区 | `get_high_level_use_districts` | XKT024 | 11〜15 | — |
| 地形区分に基づく液状化の発生傾向図 | `get_liquefaction_tendency_based_on_topographical_classification` | XKT025 | 11〜15 | — |
| 洪水浸水想定区域（想定最大規模） | `get_expected_flood_inundation_areas_at_maximum_scale` | XKT026 | 14〜15 | — |
| 高潮浸水想定区域 | `get_expected_storm_surge_inundation_areas` | XKT027 | 13〜15 | — |
| 津波浸水想定 | `get_expected_tsunami_inundation` | XKT028 | 14〜15 | — |
| 土砂災害警戒区域 | `get_sediment_disaster_alert_areas` | XKT029 | 11〜15 | — |
| 都市計画道路 | `get_city_planning_roads` | XKT030 | 11〜15 | — |
| 人口集中地区 | `get_densely_inhabited_districts` | XKT031 | 9〜15 | `administrative_area_code` |
| 指定緊急避難場所 | `get_designated_emergency_evacuation_sites` | XGT001 | 11〜15 | — |
| 災害履歴 | `get_disaster_history` | XST001 | 9〜15 | `disastertype_code` |

各メソッドの docstring に、引数の形式とコード表へのリンクがあります。

## Tile coordinates

### 点を含むタイルの取得 (containing)

```python
from pyreinfolib import tiles

tile = tiles.containing(lon=139.7016, lat=35.6580, z=15)
# Tile(z=15, x=29099, y=12905)

client.get_number_of_passengers_per_station(*tile)
```

`Tile` は `z, x, y` の順なので、タイル系メソッドにそのまま展開して渡せます。

引数は名前を付けて渡します（位置引数では渡せません）。緯度と経度はどちらも `float` なので、順序を取り違えても型では気づけないためです。

受け付けるズームレベルはエンドポイントごとに違います。上の表の「ズーム」列を見てください。範囲外を渡すと、どのエンドポイントが何を期待しているかを含む `ValueError` になります。

### 指定範囲を覆うタイルの取得 (covering / count_covering)

```python
box = {"west": 139.665, "south": 35.640, "east": 139.724, "north": 35.679}

print(tiles.count_covering(**box, z=15))  # 30

for tile in tiles.covering(**box, z=15):
    client.get_real_estate_prices_point(*tile, period_from=20241, period_to=20242)
```

ズーム15ではタイル1枚が約1km四方です。1タイルが1リクエストになるので、着手前に `count_covering()` で枚数を確認してください。引数は `covering()` と同じです。

| 範囲 | z=11 | z=13 | z=15 |
|---|---|---|---|
| 渋谷区 | 1 | 4 | 30 |
| 東京23区 | 9 | 90 | 1155 |
| 東京都（本土） | 28 | 288 | 4186 |

### タイル範囲の取得 (bounds)

```python
tiles.bounds(tile)
# Bounds(west=139.691162109375, south=35.65729624809628, east=139.7021484375, north=35.66622234103478)
```

`Bounds` は GeoJSON の bbox と同じ west, south, east, north の順です。

## Filtering

### コードでの絞り込み

コードを取る引数は、1つでもリストでも渡せます。

```python
client.get_elementary_school_districts(z=11, x=1819, y=806, administrative_area_code="13102")
client.get_elementary_school_districts(z=11, x=1819, y=806, administrative_area_code=["01101", "13102"])
```

`price_classification`、`division`、`land_type_code`、`use_category_code` は `pyreinfolib.enums` の enum を渡します。

```python
from pyreinfolib.enums import LandTypeCode, PriceClassification

client.get_real_estate_prices_point(
    z=15,
    x=29099,
    y=12905,
    period_from=20241,
    period_to=20242,
    price_classification=PriceClassification.CONTRACT_PRICE,
    land_type_code=[LandTypeCode.LAND, LandTypeCode.LAND_AND_BUILDING],
)
```

`price_classification` は API 上どちらも同じ名前ですが、コード体系が2つに分かれています。別の型にしてあるので取り違えは型チェックで検出されます。

| enum | 対象 | コード |
|---|---|---|
| `PriceClassification` | 不動産価格（XIT001、XPT001） | `01` 不動産取引価格情報 / `02` 成約価格情報 |
| `LandPriceClassification` | 地価公示・地価調査（XPT002） | `0` 地価公示 / `1` 都道府県地価調査 |

それ以外のコードは `str` です。福祉施設の3階層（[大分類](https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMajorClassificationCode.html)、[中分類](https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMiddleClassificationCode.html)、[小分類](https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMinorClassificationCode.html)）と、災害履歴の災害分類コードがこれに当たります。

```python
client.get_welfare_facilities(
    z=13,
    x=7312,
    y=3008,
    welfare_facility_class_code=["02", "05"],  # 老人福祉施設、児童福祉施設等
)

client.get_disaster_history(z=9, x=227, y=100, disastertype_code=["11", "22"])
```

災害分類コードは 11 浸水域等、12 堤防決壊箇所等、13 高潮浸水域等、14 高潮破堤箇所等、21 がけ崩れ等、22 地すべり等、23 河道閉塞箇所等、24 土石流等、33 液状化、34 地震土砂災害、37 津波高、38 津波浸水域 です。

### 都道府県コードの形式

`prefecture_code` の形式はエンドポイントごとに決まっています。

| メソッド | ID | 形式 | 栃木県の場合 |
|---|---|---|---|
| `get_natural_park_areas` | XKT019 | 先頭の0を付けない | `"9"` |
| `get_landslide_prevention_districts` | XKT021 | 2桁 | `"09"` |
| `get_steep_slope_failure_hazard_areas` | XKT022 | 2桁 | `"09"` |

引数名も型も同じなので、渡す値からは区別が付きません。XKT019 に `"09"` を渡すと `ValueError` になりますが、**XKT021 と XKT022 に `"9"` を渡した場合は空のタイルが返り**、該当データがないタイルと見分けが付きません。

### 引数の省略

引数を省略するか `None` を渡すと、その絞り込みを行いません。`get_real_estate_prices(year=2024)` は全国が対象になります。

**空文字は省略と同じ扱いになりません。** `ValueError` になります。フォームや環境変数の値をそのまま渡す場合は `city=value or None` としてください。コードのリストが空（`land_type_code=[]`）の場合も `ValueError` です。絞り込んだつもりで全件が返るのを防ぐためです。

## Client configuration

`Client` はコネクションを再利用します。タイル系APIを複数タイル分呼ぶ使い方では、TLSハンドシェイクが1回で済みます。使い終わったら `close()` するか、`with` を使ってください。

```python
with Client(api_key=os.environ["REINFOLIB_API_KEY"]) as client:
    client.get_municipalities(area="13")
```

### リトライ

スロットリング（HTTP 429）と一時的なサーバエラー（500、502、503、504）は自動で再試行します。APIはリクエスト数の上限を公開しておらず、間隔を空けて実行するよう案内しているため、429 は障害ではなく想定される応答です。

待ち時間は指数的に伸びます。既定の `max_retries=3` では 0秒、2秒、4秒の順に待ち、4回目で諦めて `RateLimitError` を送出します。APIが `Retry-After` を返した場合はそちらが優先されます。

```python
# 再試行しない
client = Client(api_key=..., max_retries=0)
```

検索結果0件（HTTP 404）は再試行しません。`timeout` は各試行を制限するもので、再試行の全体を制限するものではありません。

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

### 結果が0件の場合

都道府県・市区町村コードで取得するAPIは、条件に合致するデータが無い場合に空の結果ではなく **HTTP 404** を返します（[API操作説明](https://www.reinfolib.mlit.go.jp/help/apiManual/)の3章 Q.8）。`NoResultsError` として送出します。

```python
from pyreinfolib import NoResultsError

try:
    prices = client.get_real_estate_prices(year=2024, city="13109")
except NoResultsError:
    prices = {"status": "OK", "data": []}
```

タイル座標で取得するAPIは0件でも200と空のフィーチャ一覧を返すため、`NoResultsError` は発生しません。

### APIError の中身

```python
from pyreinfolib import APIError

try:
    client.get_municipalities(area="99")
except APIError as e:
    print(e.status_code, e.response_body, e.url)
```

## Typing

型情報を同梱しています（[PEP 561](https://peps.python.org/pep-0561/)）。返り値の形は `pyreinfolib.types` に `TypedDict` で置いてあるので、キーの綴り間違いが型エラーになります。

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
| `Item` | 都道府県・市区町村コードで取得するAPIの `data` の1要素 | `RealEstatePricesItem` |

### 型を読むときの注意

**キーと値の型は API のマニュアル通りです。** 整えていないので、国土数値情報の属性コード（`A27_001`）、ローマ字（`kubun_id`）、`_ja` 接尾辞、XCT001 の日本語キー（全角スペース入り）、XPT002 の `proximity_to_transportation_facilitites`（API 側の綴り間違い）がそのまま出てきます。

値の型もマニュアルの宣言通りです。XIT001 は取引価格を含めて全フィールドが文字列型なので、`record["TradePrice"]` は `str` です。

**どのキーが必ず来るかはマニュアルに記載がないため、全フィールドを省略可能として扱っています。** 読み取りは型チェックを通りますが、実行時に `KeyError` の可能性は残ります。

`geometry` は6種のジオメトリの合併型です。`type` で絞り込んでから `coordinates` を読みます。

```python
for feature in client.get_schools(z=13, x=7269, y=3235)["features"]:
    geometry = feature["geometry"]
    if geometry is not None and geometry["type"] == "Point":
        lon, lat = geometry["coordinates"][0], geometry["coordinates"][1]
```

`get_population_projections_in_250m_grid_squares`（XKT013）だけは `properties` が `dict[str, Any]` です。`PT01_20XX` のようにフィールド名が年を含み、マニュアルがその年をプレースホルダで書いているためです。

> [!NOTE]
> 0.6.0 以前は全メソッドが `dict[str, Any]` を返していました。返り値を `dict[str, Any]` と注釈していた場合、`TypedDict` は `dict[str, Any]` に代入できないため型チェックが落ちます。注釈を外すか、対応する `...Response` に差し替えてください。実行時の挙動は変わりません。

## Contributing

[CONTRIBUTING.md](CONTRIBUTING.md) に開発環境と命名規則、[GLOSSARY.md](GLOSSARY.md) に訳語と典拠があります。

## Author

@matsudan (daaamatsun@gmail.com)
