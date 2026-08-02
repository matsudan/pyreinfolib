"""Caller-side usage, kept here to be type checked. Not a test module and never executed.

Checking `pyreinfolib` on its own is not enough. The zoom level defect fixed in #45 left the
package internally consistent and every runtime test passing, while the two idioms the README
documents -- `client.get_...(*tile)` and a loop over `tiles.covering` -- were rejected by any
type checker the moment a user ran one. The error only appears at the call site, so a call
site has to be checked.

Write what the README tells a reader to write. If something here stops type checking, the
documentation has started lying.

Runtime behaviour is covered by `test_client.py` and `test_tiles.py`; nothing here runs, and
no API key or network is involved.
"""

from pyreinfolib import APIError, Client, NoResultsError, RateLimitError, ReinfolibError, tiles
from pyreinfolib.enums import LandPriceClassification, LandTypeCode, PriceClassification, UseDivision
from pyreinfolib.types import (
    MunicipalitiesResponse,
    RealEstatePricesItem,
    UseDistrictsProperties,
    UseDistrictsResponse,
)

API_KEY = "not-a-real-key"


def construction() -> None:
    Client(api_key=API_KEY)
    Client(api_key=API_KEY, timeout=5)
    Client(api_key=API_KEY, timeout=(3.0, 10.0))
    Client(api_key=API_KEY, max_retries=0)

    with Client(api_key=API_KEY) as client:
        client.close()


def non_tile_endpoints(client: Client) -> None:
    client.get_real_estate_prices(year=2024)
    client.get_real_estate_prices(
        year=2024,
        quarter=1,
        price_classification=PriceClassification.REAL_ESTATE_TRANSACTION_PRICE,
        area="13",
        city="13109",
        station="003785",
        language="ja",
    )
    client.get_municipalities(area="13")
    client.get_municipalities(area="13", language="en")
    client.get_appraisal_reports(year=2024, area="13", division=UseDivision.INDUSTRIAL_LAND)


def tile_endpoints_from_a_point(client: Client) -> None:
    """The idiom that #45 fixed. `Tile.z` is an `int`, so a `Literal` parameter rejects it."""
    tile = tiles.containing(lon=139.7016, lat=35.6580, z=15)

    client.get_number_of_passengers_per_station(*tile)
    client.get_number_of_passengers_per_station(z=tile.z, x=tile.x, y=tile.y)
    client.get_real_estate_prices_point(*tile, period_from=20241, period_to=20242)
    client.get_land_market_value_publication_and_research_point(*tile, year=2020)

    # The endpoints whose further parameters are all optional. `*tile` has to fill `z`, `x`
    # and `y` without a filter being passed positionally into one of them.
    client.get_elementary_school_districts(*tile)
    client.get_junior_high_school_districts(*tile)
    client.get_libraries(*tile)
    client.get_welfare_facilities(*tile)
    client.get_natural_park_areas(*tile)
    client.get_designated_emergency_evacuation_sites(*tile)
    client.get_disaster_risk_areas(*tile)
    client.get_densely_inhabited_districts(*tile)
    client.get_city_planning_roads(*tile)
    client.get_landslide_prevention_districts(*tile)
    client.get_sediment_disaster_alert_areas(*tile)
    client.get_location_normalization_plans(*tile)


def tile_endpoints_over_an_extent(client: Client) -> None:
    """The other idiom #45 fixed, and the one that matters for anything larger than a point."""
    box = {"west": 139.665, "south": 35.640, "east": 139.724, "north": 35.679}

    count: int = tiles.count_covering(**box, z=15)
    assert count > 0

    for tile in tiles.covering(**box, z=15):
        client.get_real_estate_prices_point(
            *tile,
            period_from=20241,
            period_to=20242,
            price_classification=PriceClassification.CONTRACT_PRICE,
        )


def zoom_levels_from_elsewhere(client: Client) -> None:
    """A level that arrives computed rather than written out. The `Literal` rejected all of these."""
    zoom = 14
    client.get_number_of_passengers_per_station(z=zoom, x=1819, y=806)

    for z in range(11, 16):
        client.get_number_of_passengers_per_station(z=z, x=1819, y=806)

    client.get_number_of_passengers_per_station(z=int("13"), x=1819, y=806)


def code_sequences(client: Client) -> None:
    """A single code needs no list, and a sequence of them is accepted."""
    client.get_real_estate_prices_point(
        z=15,
        x=29099,
        y=12905,
        period_from=20241,
        period_to=20242,
        land_type_code=LandTypeCode.LAND,
    )
    client.get_real_estate_prices_point(
        z=15,
        x=29099,
        y=12905,
        period_from=20241,
        period_to=20242,
        land_type_code=[LandTypeCode.LAND, LandTypeCode.FOREST_LAND],
    )
    client.get_land_market_value_publication_and_research_point(
        z=13,
        x=7312,
        y=3008,
        year=2020,
        price_classification=LandPriceClassification.LAND_MARKET_VALUE_PUBLICATION,
        use_category_code=[UseDivision.RESIDENTIAL_LAND, UseDivision.COMMERCIAL_LAND],
    )


def municipality_code_filters(client: Client) -> None:
    """The tile filters are `str`, so a bare code and a sequence of them both type check.

    Unlike `land_type_code`, these have no enum: the municipality table runs to thousands of
    entries, and two of the seven welfare facility major classes have no published English
    name to take a member name from.
    """
    client.get_elementary_school_districts(z=11, x=1819, y=806, administrative_area_code="13102")
    client.get_junior_high_school_districts(z=11, x=1819, y=806, administrative_area_code=["01101", "13102"])
    client.get_libraries(z=13, x=7312, y=3008, administrative_area_code="13102")
    client.get_disaster_risk_areas(z=11, x=1819, y=806, administrative_area_code="13102")
    client.get_densely_inhabited_districts(z=9, x=227, y=100, administrative_area_code=["01101", "13102"])
    client.get_welfare_facilities(
        z=13,
        x=7312,
        y=3008,
        administrative_area_code="13102",
        welfare_facility_class_code=["01", "02"],
        welfare_facility_middle_class_code="0101",
        welfare_facility_minor_class_code=["020101", "020102"],
    )

    # XKT019 writes the same prefecture as `9` rather than `09`. Both filters are `str` like
    # the rest, so the padding rule is a runtime check rather than something a type says.
    client.get_natural_park_areas(z=9, x=227, y=100, prefecture_code="9")
    client.get_natural_park_areas(z=9, x=227, y=100, prefecture_code=["9", "11"], district_code="10")

    # XKT021 documents the same table as `09`. Same argument name, same type, opposite form,
    # so nothing here distinguishes the two but the endpoint.
    client.get_landslide_prevention_districts(z=11, x=1819, y=806, prefecture_code="09")
    client.get_landslide_prevention_districts(
        z=11, x=1819, y=806, prefecture_code=["09", "14"], administrative_area_code="22100"
    )


def error_handling(client: Client) -> None:
    """Catching these must not require importing `requests`, which is the point of #36."""
    try:
        client.get_real_estate_prices(year=2024, city="13109")
    except NoResultsError:
        pass
    except RateLimitError as e:
        _: int = e.status_code
    except APIError as e:
        print(e.status_code, e.response_body, e.url)
    except ReinfolibError:
        pass


def reading_a_non_tile_response(client: Client) -> None:
    """The half of the library that used to be `Any`. Every read here is checked now."""
    prices = client.get_real_estate_prices(year=2024, city="13109")

    for record in prices["data"]:
        # `str` because XIT001 declares every one of its fields 文字列型, the price included.
        price: str = record["TradePrice"]
        period: str = record["Period"]
        print(price, period)

    # The response type is nameable, so a caller can annotate a variable or a function that
    # takes one. Without this the types would only be reachable through inference.
    municipalities: MunicipalitiesResponse = client.get_municipalities(area="13")
    status: str = municipalities["status"]
    first: str = municipalities["data"][0]["name"]
    print(status, first)

    reports = client.get_appraisal_reports(year=2024, area="13", division=UseDivision.INDUSTRIAL_LAND)
    # Japanese keys, which is what XCT001 documents. The U+3000 spaces are part of the key.
    latitude: str = reports["data"][0]["緯度"]
    unit_price: str = reports["data"][0]["1㎡当たりの価格"]
    print(latitude, unit_price)


def summing_a_record(records: list[RealEstatePricesItem]) -> int:
    """A caller's own helper, annotated with the item type rather than `dict[str, Any]`."""
    return sum(int(record["TradePrice"]) for record in records)


def reading_a_tile_response(client: Client) -> None:
    """A feature collection, its features, and their properties."""
    districts: UseDistrictsResponse = client.get_use_districts(*tiles.containing(lon=139.7016, lat=35.6580, z=15))

    for feature in districts["features"]:
        properties: UseDistrictsProperties = feature["properties"]
        area: str = properties["use_area_ja"]
        # 整数型 on this endpoint. XKT023 declares the same field name 文字列型, which is why
        # each endpoint gets its own properties type rather than sharing one.
        kubun: str = properties["u_floor_area_ratio_ja"]
        print(area, kubun)

    # An empty tile is an empty list, not an error, so this is the normal shape of the loop.
    print(len(districts["features"]))


def narrowing_geometry(client: Client) -> None:
    """Geometry is a union tagged by `type`, so `coordinates` needs narrowing to read.

    XKT029 documents its own data as a mix of polygons and lines, so a single geometry type
    per endpoint would be wrong even where one could be guessed.
    """
    for feature in client.get_designated_emergency_evacuation_sites(z=11, x=1786, y=816)["features"]:
        geometry = feature["geometry"]
        if geometry is None:
            continue
        if geometry["type"] == "Point":
            lon, lat = geometry["coordinates"][0], geometry["coordinates"][1]
            print(lon, lat)
        elif geometry["type"] == "Polygon":
            ring = geometry["coordinates"][0]
            print(len(ring))


def the_one_endpoint_without_a_precise_type(client: Client) -> None:
    """XKT013 names its fields after a year the manual writes as `20XX`, so keys stay open."""
    for feature in client.get_future_population_estimates_by_250m_mesh(z=11, x=1819, y=806)["features"]:
        mesh_id = feature["properties"]["MESH_ID"]
        # Whichever year the published estimate carries. Unknown at type check time.
        population = feature["properties"]["PT00_2050"]
        print(mesh_id, population)


def tile_geometry() -> None:
    tile = tiles.containing(lon=139.7016, lat=35.6580, z=15)
    extent = tiles.bounds(tile)

    west: float = extent.west
    south: float = extent.south
    east: float = extent.east
    north: float = extent.north
    assert west <= east and south <= north

    z: int = tile.z
    x: int = tile.x
    y: int = tile.y
    assert (z, x, y) == tuple(tile)


def rejected_by_the_checker(client: Client) -> None:
    """Cases that must stay rejected.

    `ty check` reports an ignore directive that suppressed nothing, and a warning is enough to
    fail the run, so each of these fails the build if the rejection ever stops happening.
    """
    # The two price classification tables are not interchangeable.
    client.get_land_market_value_publication_and_research_point(
        z=13,
        x=7312,
        y=3008,
        year=2020,
        price_classification=PriceClassification.CONTRACT_PRICE,  # ty: ignore[invalid-argument-type]
    )
    client.get_real_estate_prices(
        year=2024,
        price_classification=LandPriceClassification.LAND_MARKET_VALUE_PUBLICATION,  # ty: ignore[invalid-argument-type]
    )

    # A bare code string is no longer accepted for a parameter that has an enum.
    client.get_real_estate_prices(year=2024, price_classification="01")  # ty: ignore[invalid-argument-type]

    # The point helpers are keyword only, so a longitude and a latitude cannot be swapped by
    # passing them positionally.
    tiles.containing(139.7016, 35.6580, 15)  # ty: ignore[too-many-positional-arguments, missing-argument]

    # An API key is required.
    Client()  # ty: ignore[missing-argument]

    # A key the endpoint does not have. This is the failure the response types exist to catch:
    # before them, `record["TradePirce"]` was a `KeyError` for whoever ran the code.
    record = client.get_real_estate_prices(year=2024)["data"][0]
    print(record["TradePirce"])  # ty: ignore[invalid-key]

    # A key that belongs to a different endpoint. XIT001 spells the municipality code
    # `MunicipalityCode`; the tile endpoints spell it `administrativeAreaCode`.
    print(record["administrativeAreaCode"])  # ty: ignore[invalid-key]

    # XIT001 declares every field 文字列型, so the price arrives as a string. Treating it as a
    # number is the mistake `dict[str, Any]` used to allow through.
    total: int = record["TradePrice"]  # ty: ignore[invalid-assignment]
    print(total)

    # Properties types are per endpoint, not shared, even where the field names overlap.
    plan = client.get_district_plans(z=11, x=1819, y=806)["features"][0]["properties"]
    districts: UseDistrictsProperties = plan  # ty: ignore[invalid-assignment]
    print(districts)

    # GeoJSON allows a null geometry, so a feature's geometry has to be checked before use.
    geometry = client.get_schools(z=13, x=7269, y=3235)["features"][0]["geometry"]
    print(geometry["coordinates"])  # ty: ignore[not-subscriptable]

    # And with the `None` excluded, a coordinate still cannot be read at a fixed depth: every
    # geometry has `coordinates`, but a Point's is a position where a Polygon's is a list of
    # rings. Narrowing on `type` is what makes the depth known.
    if geometry is not None:
        longitude: float = geometry["coordinates"][0]  # ty: ignore[invalid-assignment]
        print(longitude)
