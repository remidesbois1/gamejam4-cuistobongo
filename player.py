import pygame
import settings

class Player:
    def __init__(self, x, y, map_instance):
        self.width = 48
        self.height = 48
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.velocity = 8
        self.map = map_instance
        
        # Load and scale player image
        try:
            self.image = pygame.image.load("assets/player.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        except pygame.error:
            self.image = None

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

    def draw(self, surface, offset_x, offset_y):
        draw_rect = self.rect.copy()
        draw_rect.x -= offset_x
        draw_rect.y -= offset_y
        
        if self.image:
            surface.blit(self.image, draw_rect)
        else:
            pygame.draw.rect(surface, settings.PLAYER_COLOR, draw_rect)