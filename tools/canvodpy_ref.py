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


def locked_packages() -> list[tuple[str, str, str, str]]:
    """``(name, version, where, ref)`` of every canvodpy package in ``uv.lock``.

    ``ref`` is the locked commit for a git source, the release tag
    ``v<version>`` for PyPI.
    """
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
        rows.append((name, package["version"], where, ref))
    return sorted(rows)


def reference() -> str:
    """The canvodpy ref the agent docs are checked against.

    The locked commit of the canvodpy packages taken from git (the newest
    canvodpy the extensions build on), else the release tag of canvodpy.

    Raises
    ------
    ValueError
        If the canvodpy packages from git are locked at different commits,
        or no canvodpy package is locked.
    """
    rows = locked_packages()
    commits = {ref for _, _, where, ref in rows if where.startswith("git")}
    if len(commits) > 1:
        raise ValueError(f"canvodpy packages locked at several commits: {sorted(commits)}")
    if commits:
        return commits.pop()
    tags = [ref for name, _, _, ref in rows if name == "canvodpy"]
    if not tags:
        raise ValueError("No canvodpy package in uv.lock")
    return tags[0]


def main() -> int:
    rows = [(*row[:3], f"{REPO_URL}/tree/{row[3]}") for row in locked_packages()]
    if not rows:
        print("No canvodpy package in uv.lock", file=sys.stderr)
        return 1
    widths = [max(len(row[i]) for row in rows) for i in range(3)]
    for row in rows:
        print(
            "  ".join(cell.ljust(width) for cell, width in zip(row[:3], widths, strict=True)),
            row[3],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
