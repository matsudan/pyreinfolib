"""Compare the fetched responses against what the manual's output tables declare.

    uv run python scripts/verify_response_types.py

Run `fetch_responses.py` first; this reads the same directory and needs no network or API key.

Neither source is sufficient on its own, which is why this compares them. Only the manual names
what a field means and whether it is 実数型 rather than 整数型, and only the manual lists fields a
sampled tile happened not to exercise. Only a response shows keys the manual gets wrong, keys it
omits altogether, and which keys are genuinely absent.

Prints names and types. The one place a value is printed is where the value is the answer:
`status`, a geometry `type`, and the feature collection's own `name` and `crs`.
"""

import json
import pathlib
import re
import sys
from collections import Counter

DECLARED_TYPES = {"文字列型": "str", "整数型": "int", "実数型": "float", "真偽型": "bool"}

# Elasticsearch metadata that shows through on the tile endpoints. Undocumented, so it would
# otherwise be reported as an unexpected key on almost every endpoint.
UNDOCUMENTED = {"_id", "_index"}


def declared_types(page: str, endpoint: str) -> dict[str, str]:
    """Tag name -> Python type, from the ＜出力＞ table on the endpoint's manual page.

    The table is rendered client side, so it is not in the served markup as a table. Its cells
    are in the RSC flight payload as `<td id="api{ENDPOINT}...Tag">` and `...DataType`, which is
    what this pairs up. An endpoint documenting more than one shape suffixes the group, as
    XKT007 does with `apiXKT007_2Output...`; those merge here, matching how the types treat it.

    `<td` is part of the pattern rather than incidental. The column headings carry the same ids
    with no row number, in `<th>` cells, so dropping the tag name would pick up タグ名 as a
    field called データ型.
    """
    tags: dict[str, str] = {}
    types: dict[str, str] = {}
    for cell, kind, value in re.findall(rf'<td id="api{endpoint}(\w*)(Tag|DataType)"[^>]*>([^<]*)<', page):
        (tags if kind == "Tag" else types)[cell] = value
    return {tags[cell]: DECLARED_TYPES[types[cell]] for cell in tags if cell in types}


def report(endpoint: str, expected: dict[str, str], records: list[dict]) -> list[str]:
    """Print what disagrees, and return one line per disagreement for the closing summary."""
    seen: dict[str, Counter] = {}
    present: Counter = Counter()
    for record in records:
        for key, value in record.items():
            seen.setdefault(key, Counter())[type(value).__name__] += 1
            present[key] += 1

    problems = []
    live_only = sorted(set(seen) - set(expected) - UNDOCUMENTED)
    manual_only = sorted(set(expected) - set(seen))
    if live_only:
        problems.append(f"{endpoint}: {len(live_only)} key(s) not in the manual: {live_only[:6]}")
    if manual_only:
        problems.append(f"{endpoint}: {len(manual_only)} manual key(s) never sent: {manual_only[:6]}")

    for key, counts in sorted(seen.items()):
        if key in expected and set(counts) - {expected[key], "NoneType"}:
            problems.append(f"{endpoint}: {key} is {expected[key]} in the manual, arrived as {dict(counts)}")
    if nulls := sorted(key for key, counts in seen.items() if "NoneType" in counts):
        problems.append(f"{endpoint}: arrived as null: {nulls}")

    absent = {key: len(records) - count for key, count in sorted(present.items()) if count != len(records)}
    print(f"{endpoint}: {len(records):>6,} records, {len(seen):>3} keys ({len(expected)} in the manual)")
    if absent:
        print(f"  absent from some record: {absent}")
    for problem in problems:
        print(f"  {problem.removeprefix(endpoint + ': ')}")
    return problems


def main() -> int:
    workdir = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".reinfolib-responses")
    responses = sorted(workdir.glob("X*.json"))
    if not responses:
        print(f"no responses in {workdir}; run fetch_responses.py first", file=sys.stderr)
        return 1

    problems: list[str] = []
    collections: dict[str, dict] = {}

    for path in responses:
        endpoint = path.stem
        page = (workdir / f"{endpoint}.html").read_text(encoding="utf-8")
        body = json.loads(path.read_text(encoding="utf-8"))

        if "features" in body:
            collections[endpoint] = body
            records = [feature["properties"] for feature in body["features"]]
        else:
            records = body["data"]
            print(f"{endpoint}: status={body.get('status')!r}")
        problems += report(endpoint, declared_types(page, endpoint), records)

    print("\n--- the members GeoJSON allows and the manual does not mention ---")
    for endpoint, body in collections.items():
        shapes = Counter(f["geometry"]["type"] if f["geometry"] else None for f in body["features"])
        print(f"{endpoint}: crs={body.get('crs', {}).get('properties', {}).get('name')} name={body.get('name')!r}")
        print(f"  geometry={dict(shapes)}")

    print(f"\n--- {len(problems)} disagreement(s) over {len(responses)} endpoint(s) ---")
    for problem in problems:
        print(problem)
    print("\nWhere these disagree, the response wins. See CONTRIBUTING.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
