from dataclasses import dataclass


@dataclass
class PlayerInputState:
    """Represents the per-frame input for a player.

    The host simulates the game using these values. Multiplayer clients send
    them across the network, while the local keyboard controller populates the
    instance directly.
    """

    thrust: bool = False
    reverse: bool = False
    rotate_left: bool = False
    rotate_right: bool = False
    shoot: bool = False

    def to_dict(self) -> dict:
        return {
            "thrust": self.thrust,
            "reverse": self.reverse,
            "rotate_left": self.rotate_left,
            "rotate_right": self.rotate_right,
            "shoot": self.shoot,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "PlayerInputState":
        return cls(
            thrust=bool(payload.get("thrust", False)),
            reverse=bool(payload.get("reverse", False)),
            rotate_left=bool(payload.get("rotate_left", False)),
            rotate_right=bool(payload.get("rotate_right", False)),
            shoot=bool(payload.get("shoot", False)),
        )

    @classmethod
    def from_keyboard(cls) -> "PlayerInputState":
        import pygame

        keys = pygame.key.get_pressed()
        return cls(
            thrust=keys[pygame.K_w] or keys[pygame.K_UP],
            reverse=keys[pygame.K_s] or keys[pygame.K_DOWN],
            rotate_left=keys[pygame.K_a] or keys[pygame.K_LEFT],
            rotate_right=keys[pygame.K_d] or keys[pygame.K_RIGHT],
            shoot=keys[pygame.K_SPACE],
        )
