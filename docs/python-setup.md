# Python setup and 3.14 compatibility

## Supported versions

The project requires **Python 3.9+**. FastAPI depends on Pydantic, and Pydantic's
native extension (`pydantic-core`) ships platform wheels per CPython version.

`.python-version` is set to `3.12` for pyenv/uv. That is a convenience pin, not
an upper bound. `python3 -m venv` uses whatever `python3` is on `PATH`.

## Why `pip install -r requirements.txt` failed on 3.14

`pydantic-core==2.33.2` (pulled in by `pydantic==2.11.7`) has wheels through
CPython 3.13 only. On 3.14, pip has no wheel and falls back to a source build
via maturin/PyO3. That build fails with:

```
the configured Python interpreter version (3.14) is newer than
PyO3's maximum supported version (3.13)
```

Pydantic 2.12+ added 3.14 support and publishes `cp314` wheels. The venv
lockfile now pins:

- `pydantic==2.13.4`
- `pydantic-core==2.46.4`
- `typing-inspection==0.4.2`

`uv.lock` already resolved a 3.14-capable Pydantic (2.12.3 / pydantic-core
2.41.4), so `uv run` was not affected. `poetry.lock` is updated to match
`requirements.txt`.

## Local workaround (without this pin bump)

If you need the old pins, create the venv with 3.13 (or 3.12):

```bash
python3.13 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Keeping lockfiles in sync

When bumping Pydantic, update all three:

1. `poetry update pydantic` → `poetry.lock`
2. Mirror the new `pydantic`, `pydantic-core`, and `typing-inspection` versions
   in `requirements.txt`
3. `uv lock --upgrade-package pydantic` → `uv.lock` (if uv is available)
