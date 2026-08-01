"""Helpers shared between the test modules. Not a test module itself."""

import requests


def params_of(request: requests.PreparedRequest) -> dict[str, str]:
    """The query parameters `responses` recorded for a request.

    `responses` attaches `params` to the prepared request at runtime, so it is absent from
    requests' type stubs and has to be reached without the attribute syntax. Kept in one
    place so the reason is written down once.
    """
    return getattr(request, "params")
