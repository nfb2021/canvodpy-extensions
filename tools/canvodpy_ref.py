"""Show which canvodpy code this workspace is locked against.

For every canvodpy package in ``uv.lock``: its version and the source tree
to read, a commit of the canvodpy repository (git source) or the release
tag (PyPI). Read canvodpy's code and docs there, not on its ``main``.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
REPO_URL = "https://github.com/nfb2021/canvodpy"


def main() -> int:
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    rows = []
    for package in lock["package"]:
        name, source = package["name"], package.get("source", {})
        if not name.startswith("canvod") or "editable" in source or "virtual" in source:
            continue
        if "git" in source:
            url = urlsplit(source["git"])
            branch = unquote(parse_qs(url.query).get("branch", ["?"])[0])
            ref, where = url.fragment, f"git, branch {branch}"
        else:
            ref, where = f"v{package['version']}", "PyPI"
        rows.append((name, package["version"], where, f"{REPO_URL}/tree/{ref}"))
    if not rows:
        print("No canvodpy package in uv.lock", file=sys.stderr)
        return 1
    widths = [max(len(row[i]) for row in rows) for i in range(3)]
    for row in sorted(rows):
        print(
            "  ".join(cell.ljust(width) for cell, width in zip(row[:3], widths, strict=True)),
            row[3],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
