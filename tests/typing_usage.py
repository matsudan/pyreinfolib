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
    client.get_welfare_facilities(
        z=13,
        x=7312,
        y=3008,
        administrative_area_code="13102",
        welfare_facility_class_code=["01", "02"],
        welfare_facility_middle_class_code="0101",
        welfare_facility_minor_class_code=["020101", "020102"],
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
