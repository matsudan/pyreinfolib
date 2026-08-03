"""Fetch one response per endpoint, for checking the types in `pyreinfolib.types` against.

    REINFOLIB_API_KEY=... uv run python scripts/fetch_responses.py

Writes `<workdir>/<endpoint>.html` (the manual page) and `<workdir>/<endpoint>.json` (the
response). Then run `verify_response_types.py` over the same directory.

The request for each endpoint is the one its own manual page gives as a curl example, rather
than anything chosen here. That matters for the tile endpoints: an arbitrary tile is usually
empty, and an empty tile answers nothing about which keys a response carries.

Takes a couple of minutes. The API asks callers to space their requests out and publishes no
limit, hence the wait between them.
"""

import html
import os
import pathlib
import re
import sys
import time

import requests

ENDPOINTS = (
    "XIT001 XIT002 XCT001 XPT001 XPT002 "
    "XKT001 XKT002 XKT003 XKT004 XKT005 XKT006 XKT007 XKT010 XKT011 XKT013 XKT014 XKT015 "
    "XKT016 XKT017 XKT018 XKT019 XKT020 XKT021 XKT022 XKT023 XKT024 XKT025 XKT026 XKT027 "
    "XKT028 XKT029 XKT030 XKT031 XGT001 XST001"
).split()

MANUAL_URL = "https://www.reinfolib.mlit.go.jp/help/apiManual/{}/"
SECONDS_BETWEEN_REQUESTS = 2


def manual_page(endpoint: str, workdir: pathlib.Path) -> str:
    """The endpoint's manual page, downloaded once and then read from disk."""
    path = workdir / f"{endpoint}.html"
    if not path.exists():
        response = requests.get(MANUAL_URL.format(endpoint.lower()), timeout=30)
        response.raise_for_status()
        path.write_text(response.text, encoding="utf-8")
    return path.read_text(encoding="utf-8")


def example_request(page: str) -> str:
    """The URL out of the page's curl example.

    It sits in the page as HTML, so the separators arrive as `&amp;` and the closing quote of
    the curl argument as `&quot;`. Hence unescaping, and then dropping that quote.

    The query has to be matched as ASCII parameter characters rather than as anything up to
    whitespace. Every page also shows its endpoint as `.../XIT001?＜パラメータ＞` further up, and
    those brackets are U+FF1C and U+FF1E, so a pattern excluding `<` and `>` matches it happily
    and returns a URL with no parameters at all.
    """
    match = re.search(r"https://www\.reinfolib\.mlit\.go\.jp/ex-api/external/\w+\?[\w=&;.,%-]+", page)
    if match is None:
        raise LookupError("no example request on the manual page")
    return html.unescape(match.group()).rstrip('"')


def main() -> int:
    api_key = os.environ.get("REINFOLIB_API_KEY")
    if not api_key:
        print("REINFOLIB_API_KEY is not set", file=sys.stderr)
        return 1

    workdir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".reinfolib-responses")
    workdir.mkdir(parents=True, exist_ok=True)

    failed = []
    for index, endpoint in enumerate(ENDPOINTS):
        if index:
            time.sleep(SECONDS_BETWEEN_REQUESTS)

        url = example_request(manual_page(endpoint, workdir))
        # `requests` decompresses on its own, which these responses need: the API gzips them.
        response = requests.get(url, headers={"Ocp-Apim-Subscription-Key": api_key}, timeout=120)
        if not response.ok:
            print(f"{endpoint}: {response.status_code} {response.reason} -- {response.text[:120]}")
            failed.append(endpoint)
            continue

        (workdir / f"{endpoint}.json").write_bytes(response.content)
        print(f"{endpoint}: {len(response.content):>9,} bytes")

    print(f"\n{len(ENDPOINTS) - len(failed)} of {len(ENDPOINTS)} into {workdir}")
    if failed:
        print(f"failed: {' '.join(failed)}")
        print("A stale example request is the usual cause; the manual page will have a newer one.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
