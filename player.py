import pygame
import settings
from inventory import Inventory

class Player:
    def __init__(self, x, y, map_inst):
        self.rect = pygame.Rect(x, y, 80, 80)
        self.pos, self.vel, self.map = pygame.Vector2(x, y), 500, map_inst
        self.inventory, self.weapon = Inventory(2), None
        try: self.image = pygame.transform.scale(pygame.image.load("assets/player.png").convert_alpha(), (80, 80))
        except: self.image = None

    def handle_input(self, dt):
        k = pygame.key.get_pressed()
        v = pygame.Vector2((k[pygame.K_RIGHT]|k[pygame.K_d])-(k[pygame.K_LEFT]|k[pygame.K_a]), (k[pygame.K_DOWN]|k[pygame.K_s])-(k[pygame.K_UP]|k[pygame.K_w]))
        if v.length() > 0:
            self.pos += v.normalize() * self.vel * dt
            self.pos.x = max(0, min(self.pos.x, self.map.width - 80))
            self.pos.y = max(0, min(self.pos.y, self.map.height - 80))
            self.rect.topleft = self.pos

    def draw(self, surf, ox, oy):
        if self.image: surf.blit(self.image, (self.rect.x - ox, self.rect.y - oy))
        else: pygame.draw.rect(surf, settings.PLAYER_COLOR, (self.rect.x - ox, self.rect.y - oy, 80, 80))