# Asteroids in Pygame

A simple Asteroids game using [Pygame](https://www.pygame.org/news) as the engine

## Requirements
- [Python](https://www.python.org/) >= 3.12
- [uv](https://docs.astral.sh/uv/getting-started/installation/) **or** a virtual environment tool of your choice
- [Mosquitto](https://mosquitto.org/) MQTT broker (for multiplayer)

## Environment Setup

### 1. Create a Python environment

Using uv (recommended):
```bash
uv venv
source .venv/bin/activate
```

Using vanilla Python:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

With uv:
```bash
uv pip install -r pyproject.toml
```

With pip:
```bash
pip install -r <(uv pip compile pyproject.toml --generate-hashes --quiet)
```
or simply:
```bash
pip install pygame==2.6.1 paho-mqtt>=1.6.1
```

### 3. Run an MQTT broker (multiplayer only)

Install Mosquitto and start it locally (default port 1883). For development you can run:
```bash
mosquitto -p 50000
```
Match the port with the in-game setup screens.

## Running the Game

With uv:
```bash
uv run main.py
```

With Python directly:
```bash
python3 main.py
```
