import pygame, math, random

class Projectile:
    def __init__(self, x, y, target_pos):
        self.rect = pygame.Rect(x, y, 48, 48)
        self.pos = pygame.Vector2(x, y)
        direction = target_pos - self.pos
        if direction.length() > 0: 
            self.vel = direction.normalize() * 350
            angle = math.degrees(math.atan2(-direction.y, direction.x)) + 180
        else: 
            self.vel = pygame.Vector2(1, 0)
            angle = 0
        self.timer = 0
        try: 
            base = pygame.transform.scale(pygame.image.load("assets/medusa.png").convert_alpha(), (48, 48))
            self.image = pygame.transform.rotate(base, angle)
        except: self.image = None

    def update(self, dt):
        self.pos += self.vel * dt
        self.rect.topleft = self.pos
        self.timer += dt
        return self.timer > 3.0

    def draw(self, surf, ox, oy):
        if self.image: surf.blit(self.image, (self.rect.centerx - self.image.get_width()//2 - ox, self.rect.centery - self.image.get_height()//2 - oy))
        else: pygame.draw.circle(surf, (255, 0, 255), (self.rect.centerx - ox, self.rect.centery - oy), 24)

class Squid:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 64, 64)
        self.pos = pygame.Vector2(x, y)
        self.shoot_cd = random.uniform(0, 2)
        try: self.image = pygame.transform.scale(pygame.image.load("assets/squid.png").convert_alpha(), (64, 64))
        except: self.image = None
        self.move_state, self.move_timer = 'WANDER', 0
        self.wander_vec = pygame.Vector2(0, 0)
        self.hp, self.max_hp, self.hit_timer = 50, 50, 0
    
    def take_damage(self, amount):
        if self.hit_timer > 0: return False
        self.hp -= amount
        self.hit_timer = 0.2
        return self.hp <= 0
        
    def update(self, dt, player_rect, projectiles_list, others):
        self.hit_timer = max(0, self.hit_timer - dt)
        
        # Separation logic
        sep = pygame.Vector2(0, 0)
        for o in others:
            if o is not self:
                d = self.pos.distance_to(o.pos)
                if d < 80:
                    diff = self.pos - o.pos
                    if diff.length() > 0: sep += diff.normalize() * (200 / max(1, d))
        
        if random.random() < 0.03:
            self.wander_vec = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
            self.move_timer = 0.5
            self.move_state = 'WANDER'

        self.move_timer -= dt
        if self.move_timer <= 0:
            if self.move_state == 'ADJUST':
                self.move_state = 'WANDER'
                self.move_timer = random.uniform(0.3, 0.8)
                self.wander_vec = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                if self.wander_vec.length() > 0: self.wander_vec = self.wander_vec.normalize()
            else:
                self.move_state = 'ADJUST'
                self.move_timer = random.uniform(0.5, 1.0)
        
        dist_vec = pygame.Vector2(player_rect.center) - self.pos
        dist = dist_vec.length()
        
        vel = pygame.Vector2(0, 0)
        if self.move_state == 'ADJUST':
            if dist > 0:
                if dist < 250: vel = -dist_vec.normalize() * 150
                elif dist > 450: vel = dist_vec.normalize() * 120
        elif self.move_state == 'WANDER':
            vel = self.wander_vec * 100
            
        self.pos += (vel + sep * 50) * dt
        self.rect.topleft = self.pos
        
        self.shoot_cd -= dt
        if self.shoot_cd <= 0 and dist < 600:
            self.shoot_cd = 2.0
            projectiles_list.append(Projectile(self.rect.centerx - 24, self.rect.centery - 24, pygame.Vector2(player_rect.center)))

    def draw(self, surf, ox, oy):
        if self.image:
            if self.hit_timer > 0:
                sq = (self.hit_timer / 0.2) * 0.3
                nw, nh = int(64 * (1 + sq * 0.5)), int(64 * (1 - sq))
                img = pygame.transform.scale(self.image, (nw, nh))
                surf.blit(img, (self.rect.centerx - nw//2 - ox, self.rect.bottom - nh - oy))
            else:
                surf.blit(self.image, (self.rect.x - ox, self.rect.y - oy))
        else: pygame.draw.rect(surf, (200, 0, 200), (self.rect.x - ox, self.rect.y - oy, 64, 64))
        
        if self.hp < self.max_hp:
            rx, ry = self.rect.x - ox + 12, self.rect.y - oy - 10
            pygame.draw.rect(surf, (255, 0, 0), (rx, ry, 40, 5))
            if self.hp > 0:
                pygame.draw.rect(surf, (0, 255, 0), (rx, ry, int(40 * (self.hp / self.max_hp)), 5))
class TomatoEnemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 54, 54)
        self.pos = pygame.Vector2(x, y)
        self.max_hp, self.hp = 30, 30
        self.hit_timer = 0
        self.drop_type = "tomato"
        
        self.state = 'IDLE' 
        self.timer = random.uniform(0.5, 1.5)
        self.vel = pygame.Vector2(0, 0)
        self.angle = 0
        
        try: self.base_img = pygame.transform.scale(pygame.image.load("assets/tomato.png").convert_alpha(), (54, 54))
        except: self.base_img = None

    def take_damage(self, amount):
        if self.hit_timer > 0: return False
        self.hp -= amount
        self.hit_timer = 0.2
        return self.hp <= 0

    def update(self, dt, player_rect, projectiles_list, others):
        self.hit_timer = max(0, self.hit_timer - dt)
        dist_vec = pygame.Vector2(player_rect.center) - self.pos
        dist = dist_vec.length()
        
        self.timer -= dt
            
        if self.state == 'IDLE':
            self.vel = pygame.Vector2(0, 0)
            if self.timer <= 0:
                if dist < 220: # Trigger Attack
                    self.state, self.timer = 'CHARGE_PREP', 1.0
                else: # Wander Jump
                    self.state, self.timer = 'JUMP_PREP', 0.5
        
        elif self.state == 'JUMP_PREP':
            if self.timer <= 0:
                self.state, self.timer = 'JUMP', 0.5
                angle = random.uniform(0, 6.28)
                self.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * 120
        
        elif self.state == 'JUMP':
            self.pos += self.vel * dt
            if self.timer <= 0:
                self.state, self.timer = 'LAND', 0.2
                self.vel = pygame.Vector2(0, 0)
        
        elif self.state == 'LAND':
            if self.timer <= 0:
                self.state, self.timer = 'IDLE', random.uniform(0.5, 1.0)

        elif self.state == 'CHARGE_PREP':
            if self.timer <= 0:
                self.state, self.timer = 'ROLLING', 1.5
                if dist > 0: self.vel = dist_vec.normalize() * 320
        
        elif self.state == 'ROLLING':
            self.pos += self.vel * dt
            self.angle -= 720 * dt
            if self.timer <= 0:
                self.state, self.timer = 'IDLE', 1.5
                self.angle = 0

        sep = pygame.Vector2(0, 0)
        for o in others:
            if o is not self:
                d = self.pos.distance_to(o.pos)
                if d < 50:
                    diff = self.pos - o.pos
                    if diff.length() > 0: sep += diff.normalize() * (100 / max(1, d))
        self.pos += sep * dt
        self.rect.center = self.pos

    def draw(self, surf, ox, oy):
        img = self.base_img
        if not img: 
             pygame.draw.circle(surf, (255, 0, 0), (self.rect.centerx - ox, self.rect.centery - oy), 27)
             return

        w, h = 54, 54
        dy = 0
        if self.state in ['JUMP_PREP', 'LAND']:
            w, h = 64, 44
            img = pygame.transform.scale(img, (w, h))
            dy = 5
        elif self.state == 'JUMP':
            w, h = 44, 64
            img = pygame.transform.scale(img, (w, h))
            dy = -10 # Jump up visual
        elif self.state == 'ROLLING':
            img = pygame.transform.rotate(img, self.angle)
            w, h = img.get_size()
        elif self.state == 'CHARGE_PREP':
            off = math.sin(pygame.time.get_ticks() * 0.5) * 3
            ox += off

        if self.hit_timer > 0: 
            mask = pygame.mask.from_surface(img)
            surf.blit(mask.to_surface(setcolor=(255, 255, 255, 128), unsetcolor=(0,0,0,0)), (self.rect.centerx - w//2 - ox, self.rect.centery - h//2 - oy + dy))
        else:
            surf.blit(img, (self.rect.centerx - w//2 - ox, self.rect.centery - h//2 - oy + dy))
        
        if self.hp < self.max_hp:
             rx, ry = self.rect.x - ox + 7, self.rect.y - oy - 15
             pygame.draw.rect(surf, (255, 0, 0), (rx, ry, 40, 5))
             pygame.draw.rect(surf, (0, 255, 0), (rx, ry, int(40 * (self.hp / self.max_hp)), 5))
