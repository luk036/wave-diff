# Changelog

All notable changes to this project will be documented in this file.

## Version 0.2 (2026-10-09)

### Features
- **`src/` layout**: Moved the package from `experiments/` to `src/wave_diff/` for a proper src layout, with docs and README updated to match. (#c9d98c3, #12f3c2c)

### Bug Fixes
- **Remaining `skeleton` references**: Removed the leftover skeleton test references. (#383381c)

### Testing & Code Quality
- **90%+ coverage**: Added comprehensive unit tests for `diff_distance`, `diff_tool`, and `waveform_diff` (including CLI paths). (#4c2751f, #272153a, #cc446a7)

### Code Cleanup
- **Removed PyScaffold boilerplate**: Deleted `skeleton.py`/`test_skeleton.py`, dropped Python < 3.9 compat, dead entry points, stale `IFLOW.md`, and the duplicate `LICENSE`. (#7d573ec)
- **Formatting**: Applied `ruff format` to the diff modules. (#61d97d3, #6fa20c6)

### Documentation
- **svgbob + Levenshtein diagram**: Enabled `sphinxcontrib.svgbob` and added an edit-path diagram to the `levenshtein_distance` docstring. (#b5bc74a)

### Build & CI
- **CI repair**: Fixed the broken `entry_points`/`skeleton` imports, pinned the `ruff` version, and added the runtime dependencies. (#cf199ba, #dba82ec)
