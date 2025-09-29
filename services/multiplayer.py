import contextlib
import json
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional

import paho.mqtt.client as mqtt

from constants import (
    MULTIPLAYER_DEFAULT_BROKER,
    MULTIPLAYER_DEFAULT_PORT,
    MULTIPLAYER_STATE_SEND_HZ,
    MULTIPLAYER_TOPIC_ROOT,
)
from entities.player_input import PlayerInputState


def _vec_to_list(vector) -> list[float]:
    return [float(vector.x), float(vector.y)]


@dataclass
class MultiplayerConfig:
    broker: str = MULTIPLAYER_DEFAULT_BROKER
    port: int = MULTIPLAYER_DEFAULT_PORT
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def topic(self, suffix: str) -> str:
        return f"{MULTIPLAYER_TOPIC_ROOT}/{self.session_id}/{suffix}"


class MultiplayerHostSession:
    """MQTT Host responsible for simulating the game and broadcasting state."""

    def __init__(self, config: MultiplayerConfig, game_screen):
        self.config = config
        self.game_screen = game_screen

        client_id = f"asteroids-host-{config.session_id}-{uuid.uuid4().hex[:6]}"
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self._pending_events: Deque[tuple] = deque()
        self._event_lock = threading.Lock()

        self._remote_clients: Dict[str, str] = {}  # mqtt client id -> player id
        self._player_to_client: Dict[str, str] = {}

        self._last_state_sent = 0.0
        self._state_interval = 1.0 / max(1, MULTIPLAYER_STATE_SEND_HZ)

        self._running = False
        self._known_explosions: set[str] = set()

    # MQTT lifecycle -----------------------------------------------------
    def start(self):
        if self._running:
            return
        self._running = True
        self.client.connect(self.config.broker, self.config.port, keepalive=30)
        self.client.loop_start()

    def stop(self):
        if not self._running:
            return
        self._running = False
        self.client.loop_stop()
        with contextlib.suppress(Exception):
            self.client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            print(f"[MultiplayerHostSession] Failed to connect to MQTT broker (code {rc}).")
            return
        join_topic = self.config.topic("join")
        input_topic = self.config.topic("inputs/#")
        client.subscribe(join_topic, qos=1)
        client.subscribe(input_topic, qos=0)
        print(f"[MultiplayerHostSession] Hosting session '{self.config.session_id}' on {self.config.broker}:{self.config.port}")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print("[MultiplayerHostSession] Unexpected MQTT disconnect.")

    def _on_message(self, client, userdata, message):
        topic = message.topic
        payload_text = message.payload.decode("utf-8")
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError:
            print(f"[MultiplayerHostSession] Ignoring malformed payload on {topic}: {payload_text}")
            return

        suffix = topic.removeprefix(self.config.topic("")).strip("/")
        parts = [part for part in suffix.split("/") if part]

        if not parts:
            return

        head = parts[0]
        if head == "join":
            with self._event_lock:
                self._pending_events.append(("join", payload))
            return

        if head == "inputs" and len(parts) == 2:
            player_id = parts[1]
            with self._event_lock:
                self._pending_events.append(("input", player_id, payload))
            return

    # Host loop ----------------------------------------------------------
    def process_pending(self):
        queue: Deque[tuple] = deque()
        with self._event_lock:
            while self._pending_events:
                queue.append(self._pending_events.popleft())

        while queue:
            event = queue.popleft()
            name = event[0]
            if name == "join":
                self._handle_join(event[1])
            elif name == "input":
                self._handle_input(event[1], event[2])

    def _handle_join(self, payload: dict):
        client_id = payload.get("client_id")
        if not client_id:
            return

        if client_id in self._remote_clients:
            # resend the welcome payload so reconnecting clients resume control
            player_id = self._remote_clients[client_id]
            self._send_join_ack(client_id, player_id)
            return

        player = self.game_screen.spawn_player()
        self.game_screen.set_player_input(player.player_id, PlayerInputState())

        self._remote_clients[client_id] = player.player_id
        self._player_to_client[player.player_id] = client_id

        self._send_join_ack(client_id, player.player_id)
        print(f"[MultiplayerHostSession] Player {player.player_id} joined (client {client_id}).")

    def _handle_input(self, player_id: str, payload: dict):
        input_state = PlayerInputState.from_dict(payload.get("state", payload))
        self.game_screen.set_player_input(player_id, input_state)

    def _send_join_ack(self, client_id: str, player_id: str):
        ack_topic = self.config.topic(f"clients/{client_id}")
        ack_payload = json.dumps({
            "type": "join_accept",
            "player_id": player_id,
            "session_id": self.config.session_id,
        })
        self.client.publish(ack_topic, ack_payload, qos=1, retain=False)

    def broadcast_state(self):
        now = time.perf_counter()
        if now - self._last_state_sent < self._state_interval:
            return
        self._last_state_sent = now

        state_payload = self._build_state_payload()
        state_topic = self.config.topic("state")
        self.client.publish(state_topic, json.dumps(state_payload), qos=0, retain=False)

    def broadcast_game_over(self, score: int):
        payload = json.dumps({
            "type": "game_over",
            "score": score,
        })
        topic = self.config.topic("events")
        self.client.publish(topic, payload, qos=1, retain=False)

    def remote_player_count(self) -> int:
        return len(self._remote_clients)

    def _build_state_payload(self) -> dict:
        players = []
        for player in self.game_screen.players:
            players.append({
                "id": player.player_id,
                "position": _vec_to_list(player.position),
                "velocity": _vec_to_list(player.velocity),
                "rotation": player.rotation,
                "input": player.input_state.to_dict(),
            })

        asteroids = []
        for asteroid in self.game_screen.asteroid_group:
            asteroids.append({
                "id": asteroid.entity_id,
                "position": _vec_to_list(asteroid.position),
                "velocity": _vec_to_list(asteroid.velocity),
                "radius": asteroid.radius,
                "rotation": asteroid.rotation,
                "rotation_speed": asteroid.rotation_speed,
                "points": asteroid.get_local_points(),
            })

        shots = []
        for shot in self.game_screen.shot_group:
            shots.append({
                "id": shot.entity_id,
                "position": _vec_to_list(shot.position),
                "velocity": _vec_to_list(shot.velocity),
            })

        new_explosions = []
        for explosion in self.game_screen.consume_new_explosions():
            if explosion.entity_id in self._known_explosions:
                continue
            self._known_explosions.add(explosion.entity_id)
            new_explosions.append({
                "id": explosion.entity_id,
                "position": _vec_to_list(explosion.origin),
            })

        active_ids = {explosion.entity_id for explosion in self.game_screen.explosions}
        self._known_explosions.intersection_update(active_ids)

        return {
            "type": "state",
            "timestamp": time.time(),
            "score": self.game_screen.score,
            "players": players,
            "asteroids": asteroids,
            "shots": shots,
            "effects": {
                "new_explosions": new_explosions,
            },
        }


class MultiplayerClientSession:
    """Client that mirrors host state and publishes player input."""

    def __init__(self, config: MultiplayerConfig):
        self.config = config
        self.client_id = uuid.uuid4().hex
        client_name = f"asteroids-client-{self.client_id[:6]}"
        self.client = mqtt.Client(client_id=client_name)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self.player_id: Optional[str] = None
        self._state_lock = threading.Lock()
        self._latest_state: Optional[dict] = None
        self._latest_event: Optional[dict] = None

        self._ready_event = threading.Event()
        self._running = False

    def start(self):
        if self._running:
            return
        self._running = True
        self.client.connect(self.config.broker, self.config.port, keepalive=30)
        self.client.loop_start()

    def stop(self):
        if not self._running:
            return
        self._running = False
        self.client.loop_stop()
        with contextlib.suppress(Exception):
            self.client.disconnect()

    def wait_until_ready(self, timeout: float = 10.0) -> bool:
        return self._ready_event.wait(timeout=timeout)

    def _on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            print(f"[MultiplayerClientSession] Failed to connect to MQTT broker (code {rc}).")
            return

        client.subscribe(self.config.topic("state"), qos=0)
        client.subscribe(self.config.topic("events"), qos=1)
        client.subscribe(self.config.topic(f"clients/{self.client_id}"), qos=1)

        join_payload = json.dumps({
            "type": "join_request",
            "client_id": self.client_id,
        })
        client.publish(self.config.topic("join"), join_payload, qos=1, retain=False)

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print("[MultiplayerClientSession] Unexpected MQTT disconnect.")

    def _on_message(self, client, userdata, message):
        payload_text = message.payload.decode("utf-8")
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError:
            print(f"[MultiplayerClientSession] Ignoring malformed payload on {message.topic}: {payload_text}")
            return

        suffix = message.topic.removeprefix(self.config.topic("")).strip("/")
        parts = [part for part in suffix.split("/") if part]

        if not parts:
            return

        head = parts[0]

        if head == "state":
            with self._state_lock:
                self._latest_state = payload
            return

        if head == "events":
            with self._state_lock:
                self._latest_event = payload
            return

        if head == "clients" and len(parts) == 2:
            client_id = parts[1]
            if client_id != self.client_id:
                return
            if payload.get("type") == "join_accept":
                self.player_id = payload.get("player_id")
                self._ready_event.set()
                print(f"[MultiplayerClientSession] Joined as player {self.player_id}.")

    def consume_state(self) -> Optional[dict]:
        with self._state_lock:
            return self._latest_state

    def consume_event(self) -> Optional[dict]:
        with self._state_lock:
            event = self._latest_event
            self._latest_event = None
            return event

    def publish_input(self, input_state: PlayerInputState):
        if self.player_id is None:
            return
        payload = json.dumps({
            "type": "input",
            "player_id": self.player_id,
            "state": input_state.to_dict(),
        })
        topic = self.config.topic(f"inputs/{self.player_id}")
        self.client.publish(topic, payload, qos=0, retain=False)
