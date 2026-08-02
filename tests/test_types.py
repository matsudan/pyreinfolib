"""Tests that tie every endpoint method to its response type.

`TypedDict` has no runtime behaviour, so there is nothing here that checks a decoded body
against a type -- `tests/typing_usage.py` is where the types are exercised, by a type checker.

What is worth a runtime test is the wiring, because that is what a new endpoint gets wrong. A
method added with the old `dict[str, Any]` return, or annotated with the response type of the
endpoint above it, passes `ruff`, `ty` and every test in `test_client.py`. These two do not let
it through.
"""

import typing

import pytest

from pyreinfolib import types
from pyreinfolib.client import Client

ENDPOINT_METHODS = sorted(name for name in vars(Client) if name.startswith("get_"))


def expected_response_type_name(method: str) -> str:
    """The type name the naming rule in CONTRIBUTING.md derives from a method name."""
    stem = method.removeprefix("get_")
    return "".join(part[:1].upper() + part[1:] for part in stem.split("_")) + "Response"


def test_every_endpoint_method_is_covered() -> None:
    """A guard on the guard: if this count drops, the parametrised test below stopped running."""
    assert len(ENDPOINT_METHODS) == 32


@pytest.mark.parametrize("method", ENDPOINT_METHODS)
def test_return_annotation_is_the_endpoints_response_type(method: str) -> None:
    """The annotation must be the response type whose name the method name derives.

    Resolved with `get_type_hints` rather than read as a string, so an annotation naming a type
    that does not exist fails here too.
    """
    name = expected_response_type_name(method)
    assert hasattr(types, name), f"`{method}` has no `{name}` in pyreinfolib.types"

    annotation = typing.get_type_hints(getattr(Client, method))["return"]
    assert annotation == getattr(types, name)


@pytest.mark.parametrize("method", ENDPOINT_METHODS)
def test_response_type_is_a_feature_collection_or_a_data_envelope(method: str) -> None:
    """Tile endpoints return GeoJSON; the three that are not addressed by tile do not.

    Which of the two a method returns is decided by whether it takes tile coordinates, so the
    two facts are checked against each other rather than listed twice.
    """
    response = getattr(types, expected_response_type_name(method))
    takes_tile_coordinates = "z" in typing.get_type_hints(getattr(Client, method))

    expected = types.FeatureCollection if takes_tile_coordinates else types.DataResponse
    assert typing.get_origin(response) is expected
