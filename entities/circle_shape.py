import pygame

from constants import SCREEN_HEIGHT, SCREEN_WIDTH

class CircleShape(pygame.sprite.Sprite):
    def __init__(self, x, y, radius):
        # we will be using this later
        if hasattr(self, "containers"):
            super().__init__(self.containers)
        else:
            super().__init__()

        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.radius = radius

    def draw(self, screen):
        # sub-classes must override
        pass

    def update(self, dt):
        # sub-classes must override
        pass
    
    def collides_with(self, other):
        return self.position.distance_to(other.position) < (self.radius + other.radius)

    def wrap_position(self):
        wrapped_x = False
        wrapped_y = False

        if self.position.x < -self.radius:
            self.position.x = SCREEN_WIDTH + self.radius
            wrapped_x = True
        elif self.position.x > SCREEN_WIDTH + self.radius:
            self.position.x = -self.radius
            wrapped_x = True

        if self.position.y < -self.radius:
            self.position.y = SCREEN_HEIGHT + self.radius
            wrapped_y = True
        elif self.position.y > SCREEN_HEIGHT + self.radius:
            self.position.y = -self.radius
            wrapped_y = True

        return wrapped_x, wrapped_y
