"""Tile coordinate helpers for the endpoints addressed by XYZ tiles.

Most of the published API is addressed by tile coordinates rather than by place, so a caller
holding a latitude and longitude cannot reach those endpoints without this conversion. Every
user of them would otherwise write the same arithmetic.

The grid is the standard slippy map scheme: Web Mercator, with `y` counted from the north
edge rather than the south. The API manual says only "XYZ" without naming the convention, but
inverting the tile coordinates it uses in its own examples lands in Japan under this reading
and in the southern hemisphere under TMS.

Nothing here needs a `Client`, an API key or a network, so these are plain functions.

Note that the naming rule in CONTRIBUTING.md does not apply in this module. There is no API
name to derive from: tiles are a web mapping concept, not a Real Estate Information Library
one. The vocabulary is the established one for the domain instead -- a tile *contains* a
point, a set of tiles *covers* an extent.
"""

import math
from collections.abc import Iterator
from typing import NamedTuple

# Web Mercator cannot reach the poles: the projection runs to infinity as latitude approaches
# ±90. This is the conventional cut-off, the latitude at which the projected world is square.
MAX_LATITUDE = 85.0511287798


class Tile(NamedTuple):
    """An XYZ tile address.

    The fields are ordered to match the client's tile methods, so a tile can be unpacked
    straight into one:

        client.get_number_of_passengers_per_station(*tile)
    """

    z: int
    x: int
    y: int


class Bounds(NamedTuple):
    """The geographic extent of a tile, in degrees.

    Ordered west, south, east, north, which is the order `covering` takes and the order
    GeoJSON uses for a bounding box.
    """

    west: float
    south: float
    east: float
    north: float


def _check_zoom(z: int) -> None:
    if z < 0:
        raise ValueError(f"`z` must not be negative, got {z}.")


def _check_lon(lon: float) -> None:
    if not -180.0 <= lon <= 180.0:
        raise ValueError(f"`lon` must be between -180 and 180, got {lon}.")


def _check_lat(lat: float) -> None:
    # Rejecting rather than clamping: a value out of range is a mistake to report, not a point
    # to move to the nearest one that can be placed.
    if not -MAX_LATITUDE <= lat <= MAX_LATITUDE:
        raise ValueError(
            f"`lat` must be between {-MAX_LATITUDE} and {MAX_LATITUDE}, got {lat}. "
            "Web Mercator cannot represent latitudes beyond that. Check whether a longitude "
            "reached a latitude argument: Japan spans 122E to 154E, and every one of those is "
            "out of range for a latitude."
        )


def containing(*, lon: float, lat: float, z: int) -> Tile:
    """Return the tile that contains a point.

    Keyword only on purpose. GeoJSON and most tile libraries order a point longitude first,
    while the API's own audience thinks of it as 緯度経度, latitude first. Naming the
    arguments removes the question rather than settling it.

    :param lon: Longitude in degrees.
    :param lat: Latitude in degrees.
    :param z: Zoom level. Each endpoint documents the levels it accepts.
    :return: The tile containing the point.
    :raises ValueError: If `z` is negative, or the point is outside the projected world.
    """
    _check_zoom(z)
    _check_lon(lon)
    _check_lat(lat)

    n = 2**z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)

    # A point exactly on the world's eastern or southern edge computes to `n`, one past the
    # last tile in that row or column.
    return Tile(z, min(x, n - 1), min(y, n - 1))


def bounds(tile: Tile) -> Bounds:
    """Return the geographic extent of a tile.

    Takes a `Tile` rather than three numbers so that `x` and `y` cannot be swapped, which is
    a mistake that produces a valid tile somewhere else entirely.

    :param tile: The tile to measure.
    :return: Its extent in degrees.
    """
    z, x, y = tile
    _check_zoom(z)
    n = 2**z

    def lat_at(row: int) -> float:
        return math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * row / n))))

    return Bounds(
        west=x / n * 360.0 - 180.0,
        south=lat_at(y + 1),
        east=(x + 1) / n * 360.0 - 180.0,
        north=lat_at(y),
    )


def _corner_tiles(west: float, south: float, east: float, north: float, z: int) -> tuple[Tile, Tile]:
    if west > east:
        raise ValueError(f"`west` must not be east of `east`, got west={west}, east={east}.")
    if south > north:
        raise ValueError(f"`south` must not be north of `north`, got south={south}, north={north}.")

    return (
        containing(lon=west, lat=north, z=z),
        containing(lon=east, lat=south, z=z),
    )


def _tiles_between(top_left: Tile, bottom_right: Tile) -> Iterator[Tile]:
    for y in range(top_left.y, bottom_right.y + 1):
        for x in range(top_left.x, bottom_right.x + 1):
            yield Tile(top_left.z, x, y)


def covering(*, west: float, south: float, east: float, north: float, z: int) -> Iterator[Tile]:
    """Yield every tile that overlaps a bounding box, row by row from the north-west corner.

    An iterator rather than a list, because each tile is one request against an API that asks
    to be called with gaps between calls, and the counts get large quickly: a Tokyo ward is
    covered by 30 tiles at zoom 15, and Tokyo prefecture by several thousand. Yielding lets
    the caller pace itself or stop early. Use `count_covering` to find out how many there are
    before committing to the loop.

    A box that crosses the antimeridian is rejected rather than wrapped. The API's data does
    not reach it, so wrapping would be untested behaviour serving no caller.

    :param west: Western edge, longitude in degrees.
    :param south: Southern edge, latitude in degrees.
    :param east: Eastern edge, longitude in degrees.
    :param north: Northern edge, latitude in degrees.
    :param z: Zoom level.
    :return: The covering tiles.
    :raises ValueError: If the box is inverted, or an edge is outside the projected world.
      Raised by this call, before any tile is yielded, so a `try` around the loop is not where
      it lands.
    """
    # Yielding is delegated so that this stays an ordinary function and the box is checked by
    # the call the caller wrote. A generator body does not run until the first tile is asked
    # for, which would put the `ValueError` wherever the iteration happens to be -- inside a
    # worker, or in a loop whose `try` is there for the request rather than for the box.
    top_left, bottom_right = _corner_tiles(west, south, east, north, z)

    return _tiles_between(top_left, bottom_right)


def count_covering(*, west: float, south: float, east: float, north: float, z: int) -> int:
    """Return how many tiles `covering` would yield, without yielding them.

    Worth checking first: at zoom 15 a prefecture-sized box runs to thousands of tiles, and
    therefore thousands of requests.

    :param west: Western edge, longitude in degrees.
    :param south: Southern edge, latitude in degrees.
    :param east: Eastern edge, longitude in degrees.
    :param north: Northern edge, latitude in degrees.
    :param z: Zoom level.
    :return: The number of covering tiles.
    :raises ValueError: If the box is inverted, or an edge is outside the projected world.
    """
    top_left, bottom_right = _corner_tiles(west, south, east, north, z)

    return (bottom_right.x - top_left.x + 1) * (bottom_right.y - top_left.y + 1)
