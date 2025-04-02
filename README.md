# Tough Client

## virtualenv

### Installation

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip and install the requirements
pip install --upgrade pip
pip install -r requirements.txt
```

If you have trouble activating the virtual environment on Windows, try `venv\Scripts\activate`.

If you have trouble installing on windows, try running `pip install "fastapi[standard]"`.

### Usage

```bash
# Run the server
source venv/bin/activate
python -m uvicorn main:app --reload

# Run the simulator
source venv/bin/activate
python3 simulator.py <your_name>
```

## Poetry

### Installation

```bash
poetry install --no-root
```

### Usage

```bash
# Run the server
poetry run uvicorn main:app --reload

# Run the simulator
poetry run python3 simulator.py <your_name>
```

## uv

### Usage

```bash
# Run the server
uv run python -m uvicorn main:app --reload

# Run the simulator
uv run python3 simulator.py <your_name>
```
