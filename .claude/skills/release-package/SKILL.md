---
name: release-package
description: Release one or more canvodpy-extensions packages (version bump, changelog, PR, tag, GitHub Release, downstream re-pin). Use only when the user asks to release.
disable-model-invocation: true
---

# Release a package

A release of package `PKG` is the annotated tag `PKG-v<version>` on `main`
(e.g. `canvod-filemap-v1.0.0`) plus a GitHub Release. Nothing goes to PyPI.
Tagging and publishing are visible to everyone: confirm the version with the
user before step 2 and before step 4.

## 1. Check before releasing

```bash
git checkout main && git pull
just versions                 # current versions
just changelog PKG            # what the release will list
```

- The changelog only lists conventional commits that touched
  `packages/PKG/`. Missing entries mean commits without a conventional type
  or outside that path; fix them in a follow-up commit or the release notes.
- A breaking change since the last release means a major bump (minor while
  the version is 0.x). Look for `feat!` / `BREAKING CHANGE`.
- Root `[tool.uv.sources]` must not point the released package's canvodpy
  dependencies at a branch that will disappear (see the
  `canvodpy-dependency` guide).

## 2. Release commit, on a branch

```bash
git checkout -b chore/release-PKG-X.Y.Z    # several packages: one branch
just release PKG X.Y.Z                     # or major | minor | patch
```

`just release` refuses a dirty tree or an existing tag, runs the package's
tests, then makes one commit `chore(release): PKG X.Y.Z` that sets the
version (package `pyproject.toml`, `uv.lock`), writes
`packages/PKG/CHANGELOG.md` and re-pins the install snippets in
`README.md`, `docs/` and `packages/PKG/README.md` to the new tag. Several
packages: run it once per package on the same branch.

Check the commit: `git show --stat HEAD`, read the changelog section,
`grep -rn "PKG-v" README.md docs packages/PKG/README.md`.

## 3. PR and merge

```bash
git push -u origin chore/release-PKG-X.Y.Z
gh pr create --fill
```

Wait for CI and the merge. Don't tag the branch: the merge commit differs
from the branch commit, and a tag on the branch would point outside `main`.

## 4. Tag

```bash
git checkout main && git pull
just tag PKG
```

`just tag` requires `main` equal to `origin/main` and the tag in the
changelog, then pushes the annotated tag. That runs
`.github/workflows/release.yml`, which checks the tag against the package
version and drafts a GitHub Release from the changelog.

## 5. Publish and verify

- `gh release list`, then read the draft (`gh release view PKG-vX.Y.Z`) and
  publish it: `gh release edit PKG-vX.Y.Z --draft=false`.
- Install from the tag outside the workspace:

```bash
uv venv /tmp/ext-check && source /tmp/ext-check/bin/activate
uv pip install "PKG @ git+https://github.com/nfb2021/canvodpy-extensions.git@PKG-vX.Y.Z#subdirectory=packages/PKG"
python -c "import canvod.<short name>"
```

## 6. Downstream

canvodpy pins canvod-filemap and canvod-adapters in its root
`pyproject.toml` (`[tool.uv.sources]`, `tag = "PKG-vX.Y.Z"`; for filemap
also the range in the `filemap` dependency group). Update them in a canvodpy
PR and relock there (`uv lock --upgrade-package PKG`).

## If something went wrong

- Wrong tag, not yet published: `git push --delete origin PKG-vX.Y.Z`,
  `git tag -d PKG-vX.Y.Z`, delete the draft, fix, tag again.
- Published release: never move its tag. Release a patch version instead.
