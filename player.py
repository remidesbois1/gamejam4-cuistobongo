import pygame
import settings

class Player:
    def __init__(self, x, y, map_instance):
        self.width = 32
        self.height = 32
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.velocity = 5
        self.map = map_instance

    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        dx = 0
        dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.velocity
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.velocity
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.velocity
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.velocity

        self.move(dx, dy)

    def move(self, dx, dy):
        if 0 <= self.rect.x + dx <= self.map.width - self.rect.width:
            self.rect.x += dx
        
        if 0 <= self.rect.y + dy <= self.map.height - self.rect.height:
            self.rect.y += dy

    def draw(self, surface):
        pygame.draw.rect(surface, settings.PLAYER_COLOR, self.rect)