"""Check that the agent instructions name only paths and recipes that exist.

Reads ``AGENTS.md``, ``packages/*/AGENTS.md`` and
``.claude/skills/*/SKILL.md``. A path in backticks must exist relative to
the repository root or to the file's directory; a ``just <recipe>`` must be
a recipe of the root Justfile. ``canvodpy:<path>`` names a path in the
canvodpy repository; it is checked if a canvodpy checkout is found
(``$CANVODPY_REPO``, or ``canvodpy`` next to this repository). Placeholders
(``<...>``, ``PKG``, ``*``) and the paths listed below are not checked.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Paths outside this repository: git refs, temporary files.
OTHER_REPO_PREFIXES = ("origin/", "/tmp/")

#: Prefix of a path in the canvodpy repository.
CANVODPY = "canvodpy:"

#: Files of the user's canvodpy configuration.
USER_FILES = frozenset({"canvod-settings.yaml"})

#: Recipes of the canvodpy Justfile, named in the guides.
OTHER_REPO_RECIPES = frozenset({"naming-init", "config-check-data"})

_CODE_SPAN = re.compile(r"`([^`\n]+)`")
_FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
_JUST = re.compile(r"(?:^|[\s`(])just ([a-z][a-z0-9-]*)")
_PATH_SUFFIXES = (".md", ".py", ".toml", ".yaml", ".yml", ".ini", ".lock")
_PLACEHOLDER = re.compile(r"[<>*{}]|PKG|X\.Y\.Z")


def agent_files() -> list[Path]:
    return [
        ROOT / "AGENTS.md",
        *sorted(ROOT.glob("packages/*/AGENTS.md")),
        *sorted(ROOT.glob(".claude/skills/*/SKILL.md")),
    ]


def canvodpy_repo() -> Path | None:
    repo = Path(os.environ.get("CANVODPY_REPO", ROOT.parent / "canvodpy"))
    return repo if (repo / "canvodpy" / "pyproject.toml").is_file() else None


def just_recipes() -> set[str]:
    out = subprocess.run(
        ["just", "--summary"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return set(out.split())


def is_path(span: str) -> bool:
    if " " in span or span.startswith(("http", "-")) or _PLACEHOLDER.search(span):
        return False
    return "/" in span or span.endswith(_PATH_SUFFIXES)


def problems(file: Path, recipes: set[str], canvodpy: Path | None) -> list[str]:
    text = file.read_text(encoding="utf-8")
    found = []
    for span in _CODE_SPAN.findall(_FENCE.sub("", text)):
        if span.startswith(CANVODPY):
            path = span.removeprefix(CANVODPY)
            if canvodpy and not _PLACEHOLDER.search(path) and not (canvodpy / path).exists():
                found.append(f"path `{path}` does not exist in canvodpy ({canvodpy})")
            continue
        if not is_path(span) or span.startswith(OTHER_REPO_PREFIXES) or span in USER_FILES:
            continue
        if not ((ROOT / span).exists() or (file.parent / span).exists()):
            found.append(f"path `{span}` does not exist")
    for recipe in _JUST.findall(text):
        if recipe not in recipes and recipe not in OTHER_REPO_RECIPES:
            found.append(f"`just {recipe}` is not a recipe")
    return found


def main() -> int:
    recipes = just_recipes()
    canvodpy = canvodpy_repo()
    if canvodpy is None:
        print("No canvodpy checkout found: canvodpy paths not checked")
    failed = False
    for file in agent_files():
        for problem in problems(file, recipes, canvodpy):
            print(f"{file.relative_to(ROOT)}: {problem}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
