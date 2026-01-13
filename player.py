import pygame, math
import settings
import random
from inventory import Inventory

class Player:
    def __init__(self, x, y, map_inst):
        self.rect = pygame.Rect(x, y, settings.PLAYER_SIZE, settings.PLAYER_SIZE)
        self.pos, self.vel, self.map = pygame.Vector2(x, y), settings.PLAYER_SPEED, map_inst
        self.inventory, self.weapon = Inventory(3), "drum_weapon"
        self.health, self.max_health = settings.PLAYER_HP, settings.PLAYER_HP
        self.inv_timer = 0
        self.last_dir = pygame.Vector2(1, 0)
        self.dash_timer = 0
        self.dash_vec = pygame.Vector2(0, 0)
        self.img_body, self.img_pan, self.legs, self.frame, self.anim_t = None, None, [], 0, 0
        self.dmg_sounds = []
        try:
            self.img_body = pygame.transform.scale(pygame.image.load("assets/chief_bomgo.png").convert_alpha(), (settings.PLAYER_SIZE, settings.PLAYER_SIZE))
            self.img_pan = pygame.transform.scale(pygame.image.load("assets/chief_pan.png").convert_alpha(), (settings.PLAYER_SIZE, settings.PLAYER_SIZE))
            self.img_sax = pygame.transform.scale(pygame.image.load("assets/chief_sax.png").convert_alpha(), (settings.PLAYER_SIZE, settings.PLAYER_SIZE))
            for i in [1, 2, 3]:
                img = pygame.image.load(f"assets/LEG{i}.png").convert_alpha()
                self.legs.append(pygame.transform.scale(img, (settings.PLAYER_SIZE, 60)))
            for i in [1, 2, 3, 4]:
                s = pygame.mixer.Sound(f"assets/chief-degat{i}.wav")
                s.set_volume(0.5)
                self.dmg_sounds.append(s)
            
            # Death Assets
            self.img_dead = pygame.transform.scale(pygame.image.load("assets/chief_dead.png").convert_alpha(), (settings.PLAYER_SIZE, settings.PLAYER_SIZE))
            self.img_broken_leg = pygame.transform.scale(pygame.image.load("assets/BROKEN_LEG.png").convert_alpha(), (settings.PLAYER_SIZE, 60))
            self.img_tomb = pygame.transform.scale(pygame.image.load("assets/tombe.png").convert_alpha(), (settings.PLAYER_SIZE, settings.PLAYER_SIZE))
        except: pass
        self.needs_shake = False
        self.tombs = []
    
    def add_tomb(self, dim):
        self.tombs.append((pygame.Vector2(self.rect.topleft), dim))

    
    
    def on_death(self):
        self.death_debris = []
        PATHS = {"tomato": "assets/tomato-icon.png", "cheese": "assets/fromage-icon.png", "dough": "assets/dough.png"}
        
        center = pygame.Vector2(self.rect.centerx, self.rect.centery)
        for k, count in self.inventory.counts.items():
             for _ in range(count):
                 # Random target position around player
                 dist = random.uniform(60, 200)
                 angle = random.uniform(0, math.pi * 2)
                 target = center + pygame.Vector2(math.cos(angle) * dist, math.sin(angle) * dist)
                 
                 path = PATHS.get(k, None)
                 if path:
                     try:
                         img = pygame.transform.scale(pygame.image.load(path).convert_alpha(), (40, 40))
                         # Store origin, target, and image
                         self.death_debris.append({
                             'origin': center.copy(), 
                             'target': target, 
                             'img': img,
                             'rot': random.uniform(-20, 20)
                         })
                     except: pass

    def draw_death(self, surf, ox, oy, timer, dim):
        # Draw existing tombs
        for t_pos, t_dim in self.tombs:
            if t_dim == dim:
                surf.blit(self.img_tomb, (t_pos.x - ox, t_pos.y - oy))

        pos = (self.rect.x - ox, self.rect.y - oy)

        # Debris Animation
        if hasattr(self, 'death_debris'):
            # Calculate progress (scatter takes 0.5s)
            t = min(1.0, timer / 0.5)
            # Ease out cubic
            ease = 1 - pow(1 - t, 3)
            
            for d in self.death_debris:
                cur_pos = d['origin'].lerp(d['target'], ease)
                draw_pos = (cur_pos.x - ox, cur_pos.y - oy)
                
                # Shadow
                s = pygame.Surface((30, 10), pygame.SRCALPHA)
                pygame.draw.ellipse(s, (0, 0, 0, 80), (0, 0, 30, 10))
                surf.blit(s, (draw_pos[0] + 5, draw_pos[1] + 30))
                
                # Item
                surf.blit(d['img'], draw_pos)

        # Dead Body Phase (Hide when crushed)
        if timer < 1.4:
            if self.img_broken_leg: surf.blit(self.img_broken_leg, pos)
            # Offset body higher like normal
            if self.img_dead: surf.blit(self.img_dead, (pos[0], pos[1] - 79))
        
        # Tomb Phase
        if timer > 1.0 and self.img_tomb:
            # Fall animation
            progress = min(1.0, (timer - 1.0) / 0.4)
            start_y = -300
            end_y = pos[1]
            
            # Ease in out
            cur_y = start_y + (end_y - start_y) * (progress * progress)
            
            surf.blit(self.img_tomb, (pos[0], cur_y))
    
    def take_damage(self, amount):
        if self.inv_timer > 0 or self.dash_timer > 0: return False
        self.health -= amount
        self.inv_timer = settings.PLAYER_INV_TIME
        self.needs_shake = True
        if self.dmg_sounds:
            random.choice(self.dmg_sounds).play()
        return self.health <= 0

    def respawn(self, x, y):
        self.health = self.max_health
        self.pos = pygame.Vector2(x, y)
        self.rect.topleft = self.pos
        self.inventory.counts = {k:0 for k in self.inventory.counts}
        self.last_dir = pygame.Vector2(1, 0)
        self.dash_timer = 0

        self.speed_multiplier = 1.0

    def start_dash(self, direction):
        if direction.length() == 0: direction = pygame.Vector2(1, 0)
        self.dash_vec = direction.normalize()
        self.dash_timer = settings.PLAYER_DASH_TIME
        self.inv_timer = settings.PLAYER_DASH_INV_TIME

    def handle_input(self, dt):
        if self.dash_timer > 0:
            self.dash_timer -= dt
            self.pos += self.dash_vec * settings.PLAYER_DASH_SPEED * dt
            self.pos.x = max(0, min(self.pos.x, self.map.width - settings.PLAYER_SIZE))
            self.pos.y = max(0, min(self.pos.y, self.map.height - settings.PLAYER_SIZE))
            self.rect.topleft = self.pos
            return

        self.inv_timer -= dt
        k = pygame.key.get_pressed()
        right = any(k[key] for key in settings.KEYS_RIGHT)
        left = any(k[key] for key in settings.KEYS_LEFT)
        down = any(k[key] for key in settings.KEYS_DOWN)
        up = any(k[key] for key in settings.KEYS_UP)
        v = pygame.Vector2(int(right)-int(left), int(down)-int(up))
        if v.length() > 0:
            self.last_dir = v.normalize()
            self.pos += self.last_dir * self.vel * self.speed_multiplier * dt
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

    def draw(self, surf, ox, oy, dim):
        # Draw persistent tombs
        for t_pos, t_dim in self.tombs:
            if t_dim == dim and self.img_tomb:
                surf.blit(self.img_tomb, (t_pos.x - ox, t_pos.y - oy))

        pos = (self.rect.x - ox, self.rect.y - oy)

        s = pygame.Surface((60, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 100), (0, 0, 60, 20))
        surf.blit(s, (pos[0] + 10, pos[1] + 42))

        body = self.img_body
        if self.weapon == "pan_weapon" and self.img_pan: body = self.img_pan
        if self.weapon == "sax_weapon" and self.img_sax: body = self.img_sax

        alpha = 255
        if self.inv_timer > 0:
            if int(self.inv_timer * 15) % 2 == 0: alpha = 90

        if body:
            body.set_alpha(alpha)
            surf.blit(body, (pos[0] - 2, pos[1] - 79))
            body.set_alpha(255)
        else:
            pygame.draw.rect(surf, (255, 0, 0), (self.rect.x - ox, self.rect.y - oy, 80, 80))
        
        if self.legs:
            lg = self.legs[self.frame]
            lg.set_alpha(alpha)
            surf.blit(lg, pos)
            lg.set_alpha(255)
        elif not body:
            pygame.draw.rect(surf, settings.PLAYER_COLOR, (pos[0], pos[1], 80, 80))

        bx, by = pos[0] + 10, pos[1] - 100
        bw, bh = 60, 8
        pygame.draw.rect(surf, (50, 0, 0), (bx, by, bw, bh), border_radius=2)
        if self.health > 0:
            pygame.draw.rect(surf, (0, 255, 0), (bx, by, int(bw * (self.health / self.max_health)), bh), border_radius=2)
        pygame.draw.rect(surf, (0, 0, 0), (bx, by, bw, bh), 1, border_radius=2)