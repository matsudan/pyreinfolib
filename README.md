# pyreinfolib

[![PyPI](https://img.shields.io/pypi/v/pyreinfolib)](https://pypi.org/project/pyreinfolib/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyreinfolib)](https://pypi.org/project/pyreinfolib/)
[![ci](https://github.com/matsudan/pyreinfolib/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/matsudan/pyreinfolib/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/pypi/l/pyreinfolib)](https://github.com/matsudan/pyreinfolib/blob/main/LICENSE)

日本語 | [English](https://github.com/matsudan/pyreinfolib/blob/main/README.en.md)

国土交通省の[不動産情報ライブラリ](https://www.reinfolib.mlit.go.jp/) API を利用する Python クライアントです。対応する API は[対応エンドポイント](#endpoints)に一覧があります。

API 仕様は[API操作説明](https://www.reinfolib.mlit.go.jp/help/apiManual/)を参照してください。API キーは[API利用申請](https://www.reinfolib.mlit.go.jp/api/request/)で取得します。

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

多くのデータは地図のタイル座標を指定して取得します。緯度・経度からの変換には `pyreinfolib.tiles` を使います。

```python
from pyreinfolib import tiles

tile = tiles.containing(lon=139.7016, lat=35.6580, z=15)

for feature in client.get_use_districts(*tile)["features"]:
    print(feature["properties"]["use_area_ja"])
```

<a id="endpoints"></a>
## Endpoints

### タイル座標を使わない API

XIT001 では `year` と、`area`・`city`・`station` のいずれか1つ以上が必須です。XIT002 では `area`、XCT001 では表にある3つの引数がすべて必須です。その他の引数は任意です。

| データ | メソッド | ID | 引数 |
|---|---|---|---|
| 不動産価格（取引価格・成約価格）情報 | `get_real_estate_prices` | XIT001 | `year`、`price_classification`、`quarter`、`area`、`city`、`station`、`language` |
| 都道府県内市区町村一覧 | `get_municipalities` | XIT002 | `area`、`language` |
| 鑑定評価書情報 | `get_appraisal_reports` | XCT001 | `year`、`area`、`division` |

### タイル座標を使う API

すべてのメソッドで `z`、`x`、`y` が必須です。XPT001 では `period_from` と `period_to`、XPT002 では `year` も必須です。表の「追加引数」にあるその他の引数は任意で、省略するとその条件では絞り込みません。

| データ | メソッド | ID | ズーム | 追加引数 |
|---|---|---|---|---|
| 不動産価格のポイント | `get_real_estate_prices_point` | XPT001 | 11〜15 | `period_from`（必須）、`period_to`（必須）、`price_classification`、`land_type_code` |
| 地価公示・地価調査のポイント | `get_land_market_value_publication_and_research_point` | XPT002 | 13〜15 | `year`（必須）、`price_classification`、`use_category_code` |
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
| 特別注視区域 | `get_special_monitored_areas` | XNT001 | 11〜15 | — |

引数の形式とコード表は各メソッドの docstring に記載しています。

## Tile coordinates

### 点を含むタイル（`containing`）

```python
from pyreinfolib import tiles

tile = tiles.containing(lon=139.7016, lat=35.6580, z=15)
# Tile(z=15, x=29099, y=12905)

client.get_number_of_passengers_per_station(*tile)
```

`Tile` は `z, x, y` の順なので、タイル系メソッドにそのまま展開できます。緯度と経度はどちらも `float` で順序の間違いを型では検出できないため、`containing` にはキーワード引数で渡します。

利用できるズームレベルはエンドポイントごとに異なります。範囲外を渡すと、利用できる範囲を示す `ValueError` が発生します。

### 指定範囲を覆うタイル（`covering` / `count_covering`）

```python
box = {"west": 139.665, "south": 35.640, "east": 139.724, "north": 35.679}

print(tiles.count_covering(**box, z=15))  # 30

for tile in tiles.covering(**box, z=15):
    client.get_real_estate_prices_point(*tile, period_from=20241, period_to=20242)
```

1タイルにつき1リクエストになるため、実行前に `count_covering()` で枚数を確認してください。東京付近では、ズーム15のタイルはおよそ1 km四方です。

### タイルの範囲（`bounds`）

```python
tiles.bounds(tile)
# Bounds(west=139.691162109375, south=35.65729624809628, east=139.7021484375, north=35.66622234103478)
```

`Bounds` は GeoJSON の bbox と同じく west, south, east, north の順です。

## Filtering

### コードを使う引数

コードを受け取る引数には、単一のコードまたはコードのシーケンスを渡せます。

```python
client.get_elementary_school_districts(z=11, x=1819, y=806, administrative_area_code="13102")
client.get_elementary_school_districts(z=11, x=1819, y=806, administrative_area_code=["01101", "13102"])
```

`price_classification`、`division`、`land_type_code`、`use_category_code` には `pyreinfolib.enums` の enum を渡します。

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

API 上ではどちらも `priceClassification` ですが、XIT001/XPT001 と XPT002 ではコード体系が異なります。別の型にしてあるため、取り違えは型チェックで検出できます。

| enum | 対象 | コード |
|---|---|---|
| `PriceClassification` | 不動産価格（XIT001、XPT001） | `01` 不動産取引価格情報 / `02` 成約価格情報 |
| `LandPriceClassification` | 地価公示・地価調査（XPT002） | `0` 地価公示 / `1` 都道府県地価調査 |

それ以外のコードは `str` です。たとえば、福祉施設の3階層（[大分類](https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMajorClassificationCode.html)、[中分類](https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMiddleClassificationCode.html)、[小分類](https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMinorClassificationCode.html)）と災害履歴の災害分類コードが該当します。

```python
client.get_welfare_facilities(
    z=13,
    x=7312,
    y=3008,
    welfare_facility_class_code=["02", "05"],  # 老人福祉施設、児童福祉施設等
)

client.get_disaster_history(z=9, x=227, y=100, disastertype_code=["11", "22"])
```

災害分類コードには独立したコード表がありません。[XST001 のマニュアル](https://www.reinfolib.mlit.go.jp/help/apiManual/xst001/)または `get_disaster_history` の docstring を参照してください。

### 都道府県コードの形式

`prefecture_code` の形式はエンドポイントごとに異なります。

| メソッド | ID | 形式 | 栃木県の場合 |
|---|---|---|---|
| `get_natural_park_areas` | XKT019 | 先頭の0を付けない | `"9"` |
| `get_landslide_prevention_districts` | XKT021 | 2桁 | `"09"` |
| `get_steep_slope_failure_hazard_areas` | XKT022 | 2桁 | `"09"` |

引数名と型は同じなので、値から形式を判別できません。XKT019 に `"09"` を渡すと `ValueError` になります。XKT021 と XKT022 に `"9"` を渡すと空のタイルが返り、データがない場合と見分けが付きません。

### 引数の省略

任意の絞り込み引数は、省略するか `None` を渡すと適用されません。ただし、`get_real_estate_prices` では `area`、`city`、`station` のいずれか1つ以上が必要です。

空文字は省略として扱わず、`ValueError` を送出します。フォームや環境変数の値を渡す場合は `city=value or None` としてください。空のコード列（`land_type_code=[]` など）も、意図せず全件を取得するのを防ぐため `ValueError` になります。

## Client configuration

`Client` は可能な範囲で接続を再利用します。使い終わったら `close()` を呼ぶか、`with` 文を使ってください。

```python
with Client(api_key=os.environ["REINFOLIB_API_KEY"]) as client:
    client.get_municipalities(area="13")
```

### リトライ

HTTP 429 と一時的なサーバーエラー（500、502、503、504）は自動で再試行します。既定の `max_retries=3` では最大4回試行し、再試行前に0秒、2秒、4秒待ちます。API が `Retry-After` を返した場合は、その値を優先します。

最終応答が429なら `RateLimitError`、5xxなら `APIError` を送出します。API はリクエスト数の上限を公開せず、間隔を空けて実行するよう案内しています。

```python
# 再試行しない
client = Client(api_key=..., max_retries=0)
```

検索結果0件（HTTP 404）は再試行しません。`timeout` は各試行の制限で、再試行を含む全体の制限ではありません。

## Error handling

通信または API 応答に関する例外は `ReinfolibError` を継承しているため、`requests` を import せずに捕捉できます。引数の不備は `ValueError` になります。

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

XIT001、XIT002、XCT001 は、条件に合うデータがない場合に HTTP 404 を返します（[API操作説明](https://www.reinfolib.mlit.go.jp/help/apiManual/)の3章 Q.8）。ライブラリはこれを `NoResultsError` として送出します。

```python
from pyreinfolib import NoResultsError

try:
    prices = client.get_real_estate_prices(year=2024, city="13109")
except NoResultsError:
    prices = {"status": "OK", "data": []}
```

タイル座標を使う API は、0件でも HTTP 200 と空の `features` を返すため、`NoResultsError` は発生しません。

### `APIError` の属性

```python
from pyreinfolib import APIError

try:
    client.get_municipalities(area="99")
except APIError as e:
    print(e.status_code, e.response_body, e.url)
```

## Typing

型情報を同梱しています（[PEP 561](https://peps.python.org/pep-0561/)）。返り値は `pyreinfolib.types` の `TypedDict` で表し、存在しないキーへのアクセスを型エラーとして検出できます。

```python
prices = client.get_real_estate_prices(year=2024, city="13109")

for record in prices["data"]:
    print(record["TradePrice"])
    print(record["TradePirce"])  # 型エラー
```

型名はメソッド名から機械的に決まります。変数や自作関数の型注釈に利用できます。

```python
from pyreinfolib.types import RealEstatePricesItem, UseDistrictsResponse


def total(records: list[RealEstatePricesItem]) -> int:
    return sum(int(r["TradePrice"]) for r in records)


districts: UseDistrictsResponse = client.get_use_districts(z=15, x=29099, y=12905)
```

| 接尾辞 | 対象 | 例 |
|---|---|---|
| `Response` | メソッドの返り値 | `UseDistrictsResponse` |
| `Properties` | タイル系の1フィーチャの `properties` | `UseDistrictsProperties` |
| `Item` | 非タイル系の `data` の1要素 | `RealEstatePricesItem` |

### 型定義を利用する際の注意

- **キー名と値の型は API のままです。** 国土数値情報の属性コード（`A27_001`）や日本語キーもそのまま現れます。XIT001 は取引価格を含む全フィールドが文字列なので、`record["TradePrice"]` は `str` です。
- **すべてのキーを省略可能としています。** 必須のキーがマニュアルに明記されていないためです。型チェックが通っても、実行時に `KeyError` になる可能性があります。
- **`geometry` は `None` または複数の形状型です。** `coordinates` を読む前に、`None` を除外して `type` で形状を絞り込んでください。
- **座標系はレスポンスの `crs` で確認してください。** 確認済みのレスポンスでは、図書館（XKT017）と自然公園地域（XKT019）が EPSG:4612（JGD2000）を返します。
- **XKT013 の `properties` は `dict[str, Any]` です。** フィールド名が `PT01_20XX` のように年を含み、実際の年がデータ更新によって変わるためです。

```python
for feature in client.get_schools(z=13, x=7269, y=3235)["features"]:
    geometry = feature["geometry"]
    if geometry is not None and geometry["type"] == "Point":
        lon, lat = geometry["coordinates"][0], geometry["coordinates"][1]
```

## Contributing

開発手順と命名規則は [CONTRIBUTING.md](https://github.com/matsudan/pyreinfolib/blob/main/CONTRIBUTING.md)、訳語と典拠は [GLOSSARY.md](https://github.com/matsudan/pyreinfolib/blob/main/GLOSSARY.md) にあります。

## Author

@matsudan (daaamatsun@gmail.com)
