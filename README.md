# Asteroids in Pygame

A simple Asteroids game using [Pygame](https://www.pygame.org/news) as the engine

## Requirements
- [Python](https://www.python.org/) >= 3.12
- [Pygame](https://www.pygame.org/news) 2.6.1
- [paho-mqtt](https://pypi.org/project/paho-mqtt/) (for multiplayer)
- A running MQTT broker (e.g., [Mosquitto](https://mosquitto.org/))

**Recommended** to use [UV](https://docs.astral.sh/uv/getting-started/installation/)

```bash
#To test pygame execution inside UV: 
uv run -m pygame
#To run the game use:
uv run main.py
```

If UV is not installed, use Python with Pygame globally installed
```bash
python main.py
```

## Multiplayer (MQTT)

The game can sync multiple players over MQTT. The first client to connect becomes the host and spawns/simulates asteroids; other clients render the shared world. Each connected user gets a unique ship color; score increments only for the player who shot the asteroid.

Quick start with Mosquitto locally:

```bash
# Terminal 1: start Mosquitto broker
mosquitto -v

# Terminal 2+: run one or more game clients
MQTT_HOST=127.0.0.1 uv run main.py
# optionally set a custom id
PLAYER_ID=alice MQTT_HOST=127.0.0.1 uv run main.py
```
