# ricco

A Python ETL & geospatial utility library. Published to PyPI as `ricco`.

## Setup

```bash
pip install -e ".[test]"
```

## Commands

```bash
# Run all tests
pytest -v

# Run a single test file
pytest tests/test_base.py -v

# Run a single test function
pytest tests/test_base.py::test_is_empty -v

# Lint (ruff config in pyproject.toml)
ruff check src/ricco/

# Sort imports (ruff isort in pyproject.toml)
ruff check --select I --fix src/ricco/

# Version bump (updates __init__.py and doc/source/conf.py)
bump2version patch  # or minor / major
```

## Project Structure

- `src/ricco/` — main package, installed via `pyproject.toml` with `src` layout
  - `etl/` — file I/O (rdf, to_file), data transformers, graph utils
  - `geometry/` — spatial ops, coord transforms (WGS84/GCJ-02/BD-09), topology repair
  - `util/` — strings, dates, district lookups, assertions, OS helpers
  - `geocode/` — geocoding via Baidu/Amap APIs
  - `fs/` — OSS and SFTP file access
  - `resource/` — bundled CSV data (bd_region, postcode) and stopwords
- `tests/` — pytest tests, one file per module area
- `doc/` — Sphinx documentation source

## Key Conventions

- **Lint**: ruff with max-line-length=80, ignores E111/E114/E121/W504
- **Imports**: ruff isort with `force-single-line = true`, one import per line
- **Tests**: plain pytest, no fixtures framework; tests import directly from `ricco.*`
- **Version**: single source of truth in `src/ricco/__init__.py` (`__version__`), synced by bump2version
- **CI**: GitHub Actions runs pytest on push (Python 3.10/3.11/3.12); PyPI upload on GitHub release
- **Type annotations**: use `typing.Union` for union types (not tuple syntax `(A, B)`)

## Gotchas

- The package uses `src/` layout — always `pip install -e .` before running tests
- `pyproject.toml` manages all dependencies via `[project.optional-dependencies]` groups (test/docs/dev)
- `local.py` and `src/ricco/local/` are gitignored (local config, not committed)
