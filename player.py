import pygame
import settings
from inventory import Inventory

class Player:
    def __init__(self, x, y, map_inst):
        self.rect = pygame.Rect(x, y, 80, 80)
        self.pos, self.vel, self.map = pygame.Vector2(x, y), 500, map_inst
        self.inventory, self.weapon = Inventory(3), "drum_weapon"
        self.health, self.max_health = 100, 100
        self.inv_timer = 0
        self.last_dir = pygame.Vector2(1, 0)
        self.dash_timer = 0
        self.dash_vec = pygame.Vector2(0, 0)
        self.img_body, self.img_pan, self.legs, self.frame, self.anim_t = None, None, [], 0, 0
        try:
            self.img_body = pygame.transform.scale(pygame.image.load("assets/chief_bomgo.png").convert_alpha(), (80, 80))
            self.img_pan = pygame.transform.scale(pygame.image.load("assets/chief_pan.png").convert_alpha(), (80, 80))
            self.img_sax = pygame.transform.scale(pygame.image.load("assets/chief_sax.png").convert_alpha(), (80, 80))
            for i in [1, 2, 3]:
                img = pygame.image.load(f"assets/LEG{i}.png").convert_alpha()
                self.legs.append(pygame.transform.scale(img, (80, 60)))
        except: pass
    
    def take_damage(self, amount):
        if self.inv_timer > 0 or self.dash_timer > 0: return False
        self.health -= amount
        self.inv_timer = 0.5
        return self.health <= 0

    def respawn(self, x, y):
        self.health = self.max_health
        self.pos = pygame.Vector2(x, y)
        self.rect.topleft = self.pos
        self.inventory.counts = {k:0 for k in self.inventory.counts}
        self.last_dir = pygame.Vector2(1, 0)
        self.dash_timer = 0

    def start_dash(self, direction):
        if direction.length() == 0: direction = pygame.Vector2(1, 0)
        self.dash_vec = direction.normalize()
        self.dash_timer = 0.2
        self.inv_timer = 0.3

    def handle_input(self, dt):
        if self.dash_timer > 0:
            self.dash_timer -= dt
            self.pos += self.dash_vec * 1500 * dt
            self.pos.x = max(0, min(self.pos.x, self.map.width - 80))
            self.pos.y = max(0, min(self.pos.y, self.map.height - 80))
            self.rect.topleft = self.pos
            return

        self.inv_timer -= dt
        k = pygame.key.get_pressed()
        v = pygame.Vector2((k[pygame.K_RIGHT]|k[pygame.K_d])-(k[pygame.K_LEFT]|k[pygame.K_q]), (k[pygame.K_DOWN]|k[pygame.K_s])-(k[pygame.K_UP]|k[pygame.K_z]))
        if v.length() > 0:
            self.last_dir = v.normalize()
            self.pos += self.last_dir * self.vel * dt
            self.pos.x = max(0, min(self.pos.x, self.map.width - 80))
            self.pos.y = max(0, min(self.pos.y, self.map.height - 80))
            self.rect.topleft = self.pos
            
            self.anim_t += dt * 10
            if v.x < 0 or v.y < 0:
                self.frame = 2 - (int(self.anim_t) % 3)
            else:
                self.frame = int(self.anim_t) % 3
        else:
            self.frame, self.anim_t = 0, 0

    def draw(self, surf, ox, oy):
        pos = (self.rect.x - ox, self.rect.y - oy) # Body
        body = self.img_body
        if self.weapon == "pan_weapon" and self.img_pan: body = self.img_pan
        if self.weapon == "sax_weapon" and self.img_sax: body = self.img_sax
        
        if body:
            surf.blit(body, (pos[0] - 2, pos[1] - 79))
        else:
            pygame.draw.rect(surf, (255, 0, 0), (self.rect.x - ox, self.rect.y - oy, 80, 80))
        
        if self.legs:
            surf.blit(self.legs[self.frame], pos)
        elif not body: # This condition was `elif not img:` in the original, now `body` is the relevant variable.
            pygame.draw.rect(surf, settings.PLAYER_COLOR, (pos[0], pos[1], 80, 80))