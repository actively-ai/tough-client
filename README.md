# Tough Client

A local FastAPI app that forwards completion requests to the upstream server, plus a simulator that sends traffic to it.

You only need Python. `uv` is optional.

## Setup

Requires Python 3.9 or newer. Python 3.12 matches `.python-version`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows, activate with `.venv\Scripts\activate`. If the FastAPI install fails there, run `python -m pip install "fastapi[standard]"`.

### Optional: uv

If you already have [`uv`](https://docs.astral.sh/uv/), this creates `.venv` and installs the locked dependencies:

```bash
uv sync
```

Skip activation below and prefix each command with `uv run`.

## Run

Use two terminals. Activate the environment in each one (`source .venv/bin/activate`) unless you are using `uv run`.

Start the server:

```bash
python -m uvicorn main:app --reload
```

In the other terminal, start the simulator. Replace `your_name` with your name:

```bash
python simulator.py your_name
```

The simulator runs for 60 seconds against `http://localhost:8000/completion`. Stop either process with Ctrl+C.

With uv:

```bash
uv run python -m uvicorn main:app --reload
uv run python simulator.py your_name
```
