# pyreinfolib

[![PyPI](https://img.shields.io/pypi/v/pyreinfolib)](https://pypi.org/project/pyreinfolib/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyreinfolib)](https://pypi.org/project/pyreinfolib/)
[![ci](https://github.com/matsudan/pyreinfolib/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/matsudan/pyreinfolib/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/pypi/l/pyreinfolib)](https://github.com/matsudan/pyreinfolib/blob/main/LICENSE)

[日本語](https://github.com/matsudan/pyreinfolib/blob/main/README.md) | English

A Python client for the APIs provided by Japan's Ministry of Land, Infrastructure, Transport and Tourism (MLIT) through the [Real Estate Information Library](https://www.reinfolib.mlit.go.jp/). See [Endpoints](#endpoints) for the APIs supported by this package.

See the official [API manual](https://www.reinfolib.mlit.go.jp/help/apiManual/) for the API specification. Request an API key through the [API application form](https://www.reinfolib.mlit.go.jp/api/request/).

## Installation

```shell
pip install pyreinfolib
```

## Quick start

```python
import os

from pyreinfolib import Client

client = Client(api_key=os.environ["REINFOLIB_API_KEY"])

# Real estate transaction prices in Shibuya City for Q1 2024
result = client.get_real_estate_prices(year=2024, quarter=1, city="13113")

for record in result["data"]:
    print(record["Type"], record["TradePrice"], record["Area"])
```

Most datasets are addressed by map tile coordinates. Use `pyreinfolib.tiles` to convert longitude and latitude to a tile address.

```python
from pyreinfolib import tiles

tile = tiles.containing(lon=139.7016, lat=35.6580, z=15)

for feature in client.get_use_districts(*tile)["features"]:
    print(feature["properties"]["use_area_ja"])
```

<a id="endpoints"></a>
## Endpoints

### APIs without tile coordinates

XIT001 requires `year` and at least one of `area`, `city`, and `station`. XIT002 requires `area`; XCT001 requires all three arguments in the table. Other arguments are optional.

| Data | Method | ID | Arguments |
|---|---|---|---|
| Real estate prices | `get_real_estate_prices` | XIT001 | `year`, `price_classification`, `quarter`, `area`, `city`, `station`, `language` |
| Municipalities in a prefecture | `get_municipalities` | XIT002 | `area`, `language` |
| Appraisal reports | `get_appraisal_reports` | XCT001 | `year`, `area`, `division` |

### APIs using tile coordinates

Every method requires `z`, `x`, and `y`. XPT001 also requires `period_from` and `period_to`; XPT002 also requires `year`. Other arguments in the last column are optional. Omitting one disables that filter.

| Data | Method | ID | Zoom | Additional arguments |
|---|---|---|---|---|
| Real estate price points | `get_real_estate_prices_point` | XPT001 | 11–15 | `period_from` (required), `period_to` (required), `price_classification`, `land_type_code` |
| Land market value publication and research points | `get_land_market_value_publication_and_research_point` | XPT002 | 13–15 | `year` (required), `price_classification`, `use_category_code` |
| City planning areas and area classification | `get_city_planning_areas_and_area_classification` | XKT001 | 11–15 | — |
| Use districts | `get_use_districts` | XKT002 | 11–15 | — |
| Location normalization plans | `get_location_normalization_plans` | XKT003 | 11–15 | — |
| Elementary school districts | `get_elementary_school_districts` | XKT004 | 11–15 | `administrative_area_code` |
| Junior high school districts | `get_junior_high_school_districts` | XKT005 | 11–15 | `administrative_area_code` |
| Schools | `get_schools` | XKT006 | 13–15 | — |
| Nursery schools, kindergartens, etc. | `get_nursery_schools_and_kindergartens_etc` | XKT007 | 13–15 | — |
| Medical institutions | `get_medical_institutions` | XKT010 | 13–15 | — |
| Welfare facilities | `get_welfare_facilities` | XKT011 | 13–15 | `administrative_area_code`, `welfare_facility_class_code`, `welfare_facility_middle_class_code`, `welfare_facility_minor_class_code` |
| Population projections in 250 m grid squares | `get_population_projections_in_250m_grid_squares` | XKT013 | 11–15 | — |
| Fire prevention districts and quasi-fire prevention districts | `get_fire_prevention_districts_and_quasi_fire_prevention_districts` | XKT014 | 11–15 | — |
| Number of passengers per station | `get_number_of_passengers_per_station` | XKT015 | 11–15 | — |
| Disaster risk areas | `get_disaster_risk_areas` | XKT016 | 11–15 | `administrative_area_code` |
| Libraries | `get_libraries` | XKT017 | 13–15 | `administrative_area_code` |
| Municipal offices, meeting facilities, etc. | `get_municipal_offices_and_meeting_facilities_etc` | XKT018 | 13–15 | — |
| Natural park areas | `get_natural_park_areas` | XKT019 | 9–15 | `prefecture_code`, `district_code` |
| Large-scale developed embankments | `get_large_scale_developed_embankments` | XKT020 | 11–15 | — |
| Landslide prevention districts | `get_landslide_prevention_districts` | XKT021 | 11–15 | `prefecture_code`, `administrative_area_code` |
| Steep slope failure hazard areas | `get_steep_slope_failure_hazard_areas` | XKT022 | 11–15 | `prefecture_code`, `administrative_area_code` |
| District plans | `get_district_plans` | XKT023 | 11–15 | — |
| High-level use districts | `get_high_level_use_districts` | XKT024 | 11–15 | — |
| Liquefaction tendency based on topographical classification | `get_liquefaction_tendency_based_on_topographical_classification` | XKT025 | 11–15 | — |
| Expected flood inundation areas at maximum scale | `get_expected_flood_inundation_areas_at_maximum_scale` | XKT026 | 14–15 | — |
| Expected storm surge inundation areas | `get_expected_storm_surge_inundation_areas` | XKT027 | 13–15 | — |
| Expected tsunami inundation | `get_expected_tsunami_inundation` | XKT028 | 14–15 | — |
| Sediment disaster alert areas | `get_sediment_disaster_alert_areas` | XKT029 | 11–15 | — |
| City planning roads | `get_city_planning_roads` | XKT030 | 11–15 | — |
| Densely inhabited districts | `get_densely_inhabited_districts` | XKT031 | 9–15 | `administrative_area_code` |
| Designated emergency evacuation sites | `get_designated_emergency_evacuation_sites` | XGT001 | 11–15 | — |
| Disaster history | `get_disaster_history` | XST001 | 9–15 | `disastertype_code` |
| Special monitored areas | `get_special_monitored_areas` | XNT001 | 11–15 | — |

Each method's docstring describes its argument formats and links to the relevant code tables.

## Tile coordinates

### Tile containing a point (`containing`)

```python
from pyreinfolib import tiles

tile = tiles.containing(lon=139.7016, lat=35.6580, z=15)
# Tile(z=15, x=29099, y=12905)

client.get_number_of_passengers_per_station(*tile)
```

`Tile` stores its fields as `z, x, y`, so it can be unpacked directly into a tile method. Pass longitude and latitude to `containing` by keyword because both are `float` values and a type checker cannot detect them in the wrong order.

Accepted zoom levels vary by endpoint. A level outside the endpoint's range raises `ValueError` with the accepted range.

### Tiles covering an extent (`covering` / `count_covering`)

```python
box = {"west": 139.665, "south": 35.640, "east": 139.724, "north": 35.679}

print(tiles.count_covering(**box, z=15))  # 30

for tile in tiles.covering(**box, z=15):
    client.get_real_estate_prices_point(*tile, period_from=20241, period_to=20242)
```

Each tile requires one API request. Use `count_covering()` to check the count before starting. Around Tokyo, a tile at zoom 15 is roughly one kilometre square.

### Tile bounds (`bounds`)

```python
tiles.bounds(tile)
# Bounds(west=139.691162109375, south=35.65729624809628, east=139.7021484375, north=35.66622234103478)
```

`Bounds` follows the GeoJSON bounding-box order: west, south, east, north.

## Filtering

### Code arguments

Arguments that take codes accept either one code or a sequence of codes.

```python
client.get_elementary_school_districts(z=11, x=1819, y=806, administrative_area_code="13102")
client.get_elementary_school_districts(z=11, x=1819, y=806, administrative_area_code=["01101", "13102"])
```

Pass members of `pyreinfolib.enums` to `price_classification`, `division`, `land_type_code`, and `use_category_code`.

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

The API calls both parameters `priceClassification`, but XIT001/XPT001 and XPT002 use different code systems. Separate enum types allow a type checker to detect a mix-up.

| Enum | Applies to | Codes |
|---|---|---|
| `PriceClassification` | Real estate prices (XIT001, XPT001) | `01` real estate transaction prices / `02` contract prices |
| `LandPriceClassification` | Land market value publication and research (XPT002) | `0` publication / `1` prefectural research |

Other code arguments take `str`. Examples include the three welfare-facility levels ([major](https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMajorClassificationCode.html), [middle](https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMiddleClassificationCode.html), and [minor](https://nlftp.mlit.go.jp/ksj/gml/codelist/welfareInstitution_welfareFacilityMinorClassificationCode.html)) and the disaster classification code.

```python
client.get_welfare_facilities(
    z=13,
    x=7312,
    y=3008,
    welfare_facility_class_code=["02", "05"],
)

client.get_disaster_history(z=9, x=227, y=100, disastertype_code=["11", "22"])
```

The disaster classification code has no separate code table. See the [XST001 manual](https://www.reinfolib.mlit.go.jp/help/apiManual/xst001/) or the `get_disaster_history` docstring.

### Prefecture code formats

The format of `prefecture_code` depends on the endpoint.

| Method | ID | Format | Tochigi example |
|---|---|---|---|
| `get_natural_park_areas` | XKT019 | No leading zero | `"9"` |
| `get_landslide_prevention_districts` | XKT021 | Two digits | `"09"` |
| `get_steep_slope_failure_hazard_areas` | XKT022 | Two digits | `"09"` |

The argument name and type cannot distinguish the formats. Passing `"09"` to XKT019 raises `ValueError`. Passing `"9"` to XKT021 or XKT022 returns an empty tile, which is indistinguishable from a tile with no matching data.

### Omitting arguments

Omitting an optional filter or passing `None` disables that filter. `get_real_estate_prices` is an exception: at least one of `area`, `city`, and `station` is required.

An empty string is not treated as omission and raises `ValueError`. When passing values from a form or environment variable, use `city=value or None`. An empty sequence of codes, such as `land_type_code=[]`, also raises `ValueError` to prevent an accidentally unfiltered request.

## Client configuration

`Client` reuses connections when possible. Call `close()` when finished, or use it as a context manager.

```python
with Client(api_key=os.environ["REINFOLIB_API_KEY"]) as client:
    client.get_municipalities(area="13")
```

### Retries

HTTP 429 and temporary server errors (500, 502, 503, and 504) are retried automatically. With the default `max_retries=3`, the client makes up to four attempts and waits 0, 2, and 4 seconds before retrying. A `Retry-After` header from the API takes precedence.

If the final response is 429, the client raises `RateLimitError`; for a final 5xx response, it raises `APIError`. The API publishes no fixed request limit and asks clients to leave time between requests.

```python
# Disable retries
client = Client(api_key=..., max_retries=0)
```

A query with no results (HTTP 404) is not retried. `timeout` limits each attempt, not the complete sequence of retries.

## Error handling

Transport and API-response exceptions derive from `ReinfolibError`, so callers do not need to import `requests` to catch them. Invalid arguments raise `ValueError`.

```
ReinfolibError
├── TransportError          No response (connection failure or timeout)
└── APIError                Unusable response; has status_code, response_body, and url
    ├── AuthenticationError Missing or rejected API key (401)
    ├── NoResultsError      No matching results (404)
    ├── RateLimitError      Too many requests from the same API key (429)
    └── InvalidResponseError Response body was not JSON
```

### No results

XIT001, XIT002, and XCT001 return HTTP 404 instead of an empty result when no data matches the query (see Q.8 in section 3 of the [API manual](https://www.reinfolib.mlit.go.jp/help/apiManual/)). The client raises `NoResultsError`.

```python
from pyreinfolib import NoResultsError

try:
    prices = client.get_real_estate_prices(year=2024, city="13109")
except NoResultsError:
    prices = {"status": "OK", "data": []}
```

Tile APIs return HTTP 200 with an empty `features` list, so they do not raise `NoResultsError` for an empty tile.

### `APIError` attributes

```python
from pyreinfolib import APIError

try:
    client.get_municipalities(area="99")
except APIError as e:
    print(e.status_code, e.response_body, e.url)
```

## Typing

The package includes type information under [PEP 561](https://peps.python.org/pep-0561/). Return values are `TypedDict` types in `pyreinfolib.types`, allowing type checkers to detect access to a nonexistent key.

```python
prices = client.get_real_estate_prices(year=2024, city="13109")

for record in prices["data"]:
    print(record["TradePrice"])
    print(record["TradePirce"])  # Type error
```

Type names are derived mechanically from method names and can be used to annotate variables and application functions.

```python
from pyreinfolib.types import RealEstatePricesItem, UseDistrictsResponse


def total(records: list[RealEstatePricesItem]) -> int:
    return sum(int(r["TradePrice"]) for r in records)


districts: UseDistrictsResponse = client.get_use_districts(z=15, x=29099, y=12905)
```

| Suffix | Represents | Example |
|---|---|---|
| `Response` | A method's return value | `UseDistrictsResponse` |
| `Properties` | One feature's `properties` in a tile response | `UseDistrictsProperties` |
| `Item` | One `data` item in a non-tile response | `RealEstatePricesItem` |

### Notes on the response types

- **Keys and value types match the API.** National Land Numerical Information attribute codes such as `A27_001` and Japanese keys are preserved. XIT001 declares every field, including transaction prices, as a string, so `record["TradePrice"]` is `str`.
- **Every record key is optional.** The manual does not state which keys are required. A read can therefore pass a type check and still raise `KeyError` at runtime.
- **`geometry` may be `None` and may have different shape types.** Exclude `None` and narrow on `type` before reading `coordinates`.
- **Read each response's `crs` before combining datasets.** In the responses checked for this package, XKT017 (libraries) and XKT019 (natural park areas) report EPSG:4612 (JGD2000).
- **XKT013 uses `dict[str, Any]` for `properties`.** Its field names contain years, such as `PT01_20XX`, and the actual years change when the data is updated.

```python
for feature in client.get_schools(z=13, x=7269, y=3235)["features"]:
    geometry = feature["geometry"]
    if geometry is not None and geometry["type"] == "Point":
        lon, lat = geometry["coordinates"][0], geometry["coordinates"][1]
```

## Contributing

Development instructions and naming rules are in [CONTRIBUTING.md](https://github.com/matsudan/pyreinfolib/blob/main/CONTRIBUTING.md). Translation sources are recorded in [GLOSSARY.md](https://github.com/matsudan/pyreinfolib/blob/main/GLOSSARY.md). Both documents are in Japanese.

## Author

@matsudan (daaamatsun@gmail.com)
