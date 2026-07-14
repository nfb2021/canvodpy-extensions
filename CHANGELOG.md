# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [v0.1.0](https://github.com/nfb2021/canvodpy-extensions/releases/tag/v0.1.0) - 2026-07-14

<small>[Compare with first commit](https://github.com/nfb2021/canvodpy-extensions/compare/b66aae271f5de3a48a3af8201012e1eac73cf6dd...v0.1.0)</small>

### Features

- add canvod-adapters package with gnssvod converter ([ce77b5c](https://github.com/nfb2021/canvodpy-extensions/commit/ce77b5c1196b4550e2da459e3aabbc35d627f1b4) by Nicolas Bader).
- add canvod-airflow package with daily + backfill DAGs ([b66aae2](https://github.com/nfb2021/canvodpy-extensions/commit/b66aae271f5de3a48a3af8201012e1eac73cf6dd) by Nicolas Bader). Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>, [Claude-Session](https://claude.ai/code/session_01TuRKjBQkrn2397FiXg5Bc5)

### Bug Fixes

- cz bump was passed VERSION via --increment, which only accepts MAJOR/MINOR/PATCH ([48a305d](https://github.com/nfb2021/canvodpy-extensions/commit/48a305d7cb8257cd190b4ca409b39a5b0200ed19) by Nicolas Bader). Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
- relock uv.lock and sync composite action's setup-uv pin ([9db61ef](https://github.com/nfb2021/canvodpy-extensions/commit/9db61ef388af0a6e388e4c38a855f4be9fb014c6) by Nicolas Bader). Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
- resolve ty type errors blocking pre-push hook ([c70aeae](https://github.com/nfb2021/canvodpy-extensions/commit/c70aeae9f137cb4d54d8ca597e6678dfb673fef6) by Nicolas Bader). Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
