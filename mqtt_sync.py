import os
import json
import time
import threading
from queue import Queue

try:
    import paho.mqtt.client as mqtt
except Exception:  # keep it simple: optional dep
    mqtt = None


class MQTTGameClient:
    """
    Minimal MQTT wrapper for syncing Asteroids.

    Topics (all under prefix 'asteroids/'):
      - 'host' (retained): payload: {"host_id": str}
      - 'players/<id>/join' (retained): payload: {"id": str, "color": [r,g,b]}
      - 'players/<id>/state': payload: {"id": str, "x": float, "y": float, "rot": float}
      - 'players/<id>/shoot': payload: {"id": str, "x": float, "y": float, "rot": float}
      - 'events': payload: {"type": "world_state"|"explosion"|"score", ...}
    """

    def __init__(self, player_id: str, on_event):
        self.player_id = player_id
        self.on_event = on_event  # callable(dict)
        self.host_id = None
        self.connected = False
        self._claimed_host = False
        self._claim_host_after = time.monotonic() + 0.6
        self._event_queue = Queue()
        self._client = None
        self._last_world_pub = 0.0
        self._last_state_pub = 0.0
        self._last = {}

        # broker config
        self.broker_host = os.getenv("MQTT_HOST", "localhost")
        self.broker_port = int(os.getenv("MQTT_PORT", "5050"))

    def available(self):
        return mqtt is not None

    def connect(self):
        if not self.available():
            return False
        self._client = mqtt.Client(client_id=f"asteroids-{self.player_id}")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        # simple LWT: if host dies, clear retained host
        self._client.will_set("asteroids/host", json.dumps({"host_id": ""}), retain=True)
        try:
            self._client.connect(self.broker_host, self.broker_port, 60)
        except Exception:
            return False
        self._client.loop_start()
        return True

    def _on_connect(self, client, userdata, flags, rc):
        self.connected = True
        # subscribe to everything we need
        client.subscribe("asteroids/host")
        client.subscribe("asteroids/players/+/join")
        client.subscribe("asteroids/players/+/state")
        client.subscribe("asteroids/players/+/shoot")
        client.subscribe("asteroids/events")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8")) if msg.payload else {}
        except Exception:
            return

        topic = msg.topic
        if topic == "asteroids/host":
            host_id = payload.get("host_id") or None
            self.host_id = host_id
            self._event_queue.put({"type": "host", "host_id": host_id})
            return

        if topic.startswith("asteroids/players/"):
            parts = topic.split("/")
            if len(parts) >= 4:
                _prefix, _players, pid, action = parts[:4]
                payload["player_id"] = pid
                payload["action"] = action
                self._event_queue.put({"type": "player", **payload})
            return

        if topic == "asteroids/events":
            self._event_queue.put(payload)
            return

    def get_event(self, timeout=0.0):
        try:
            return self._event_queue.get(timeout=timeout)
        except Exception:
            return None

    def maybe_claim_host(self):
        # called from main loop periodically
        if self.host_id is None and not self._claimed_host and time.monotonic() > self._claim_host_after and self.connected and self._client:
            # claim host by publishing retained
            self._client.publish("asteroids/host", json.dumps({"host_id": self.player_id}), retain=True)
            self._claimed_host = True

    def is_host(self):
        return self.host_id == self.player_id

    def publish_join(self, color_rgb):
        if not self._client:
            return
        self._client.publish(f"asteroids/players/{self.player_id}/join", json.dumps({"id": self.player_id, "color": color_rgb}), retain=True)

    def publish_player_state(self, x, y, rot):
        if not self._client:
            return
        if not self._throttle("player_state", 1.0/120.0):
            return
        self._client.publish(
            f"asteroids/players/{self.player_id}/state",
            json.dumps({"id": self.player_id, "x": x, "y": y, "rot": rot}),
        )

    def publish_shoot(self, x, y, rot):
        if not self._client:
            return
        self._client.publish(f"asteroids/players/{self.player_id}/shoot", json.dumps({"id": self.player_id, "x": x, "y": y, "rot": rot}))

    def publish_world_state(self, world_dict, min_interval=0.1):
        # throttle to min_interval seconds and hard-cap at 120 Hz
        now = time.monotonic()
        if not self._client:
            return
        if now - self._last_world_pub < max(min_interval, 1.0/120.0):
            return
        self._last_world_pub = now
        self._client.publish("asteroids/events", json.dumps({"type": "world_state", **world_dict}))

    def publish_explosion(self, x, y):
        if not self._client:
            return
        self._client.publish("asteroids/events", json.dumps({"type": "explosion", "x": x, "y": y}))

    def publish_score(self, player_id, delta):
        if not self._client:
            return
        self._client.publish("asteroids/events", json.dumps({"type": "score", "player_id": player_id, "delta": delta}))

    def publish_player_dead(self, player_id):
        if not self._client:
            return
        self._client.publish("asteroids/events", json.dumps({"type": "player_dead", "player_id": player_id}))

    def publish_player_respawn(self, player_id, x, y, rot):
        if not self._client:
            return
        self._client.publish(
            "asteroids/events",
            json.dumps({"type": "player_respawn", "player_id": player_id, "x": x, "y": y, "rot": rot}),
        )

    def _throttle(self, key, min_interval):
        now = time.monotonic()
        last = self._last.get(key, 0.0)
        if now - last < min_interval:
            return False
        self._last[key] = now
        return True
