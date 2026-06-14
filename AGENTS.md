# ricco

A Python ETL & geospatial utility library. Published to PyPI as `ricco`.

## Setup

```bash
pip install -r requirements.txt
pip install -r requirements_test.txt
pip install -e .
```

## Commands

```bash
# Run all tests
pytest -v

# Run a single test file
pytest tests/test_base.py -v

# Run a single test function
pytest tests/test_base.py::test_is_empty -v

# Lint (flake8 config in tox.ini)
flake8 src/ricco/

# Sort imports (isort config in tox.ini)
isort src/ricco/

# Version bump (updates __init__.py and doc/source/conf.py)
bump2version patch  # or minor / major
```

## Project Structure

- `src/ricco/` — main package, installed via `setup.py` with `package_dir={'': 'src'}`
  - `etl/` — file I/O (rdf, to_file), data transformers, graph utils
  - `geometry/` — spatial ops, coord transforms (WGS84/GCJ-02/BD-09), topology repair
  - `util/` — strings, dates, district lookups, assertions, OS helpers
  - `geocode/` — geocoding via Baidu/Amap APIs
  - `fs/` — OSS and SFTP file access
  - `resource/` — bundled CSV data (bd_region, postcode) and stopwords
- `tests/` — pytest tests, one file per module area
- `doc/` — Sphinx documentation source

## Key Conventions

- **Lint**: flake8 with max-line-length=80, ignores D203/E111/E114/E121/H101/H301/H306/W504
- **Imports**: isort with `force_single_line = True`, one import per line
- **Tests**: plain pytest, no fixtures framework; tests import directly from `ricco.*`
- **Version**: single source of truth in `src/ricco/__init__.py` (`__version__`), synced by bump2version
- **CI**: GitHub Actions runs pytest on push (Python 3.9); PyPI upload on GitHub release
- **Type annotations**: use `typing.Union` for union types (not tuple syntax `(A, B)`)

## Gotchas

- The package uses `src/` layout — always `pip install -e .` before running tests
- `requirements.txt` pins exact versions for dev; `setup.py` `install_requires` uses ranges for published package
- `MANIFEST.in` includes resource CSVs — don't remove them from `src/ricco/resource/`
- `local.py` and `src/ricco/local/` are gitignored (local config, not committed)
