import pygame, math, random, settings

class Projectile:
    def __init__(self, x, y, target_pos):
        self.rect = pygame.Rect(x, y, settings.PROJECTILE_SIZE, settings.PROJECTILE_SIZE)
        self.pos = pygame.Vector2(x, y)
        direction = target_pos - self.pos
        if direction.length() > 0: 
            self.vel = direction.normalize() * settings.PROJECTILE_SPEED
            angle = math.degrees(math.atan2(-direction.y, direction.x)) + 180
        else: 
            self.vel = pygame.Vector2(1, 0)
            angle = 0
        self.timer = 0
        try: 
            base = pygame.transform.scale(pygame.image.load("assets/medusa.png").convert_alpha(), (settings.PROJECTILE_SIZE, settings.PROJECTILE_SIZE))
            self.image = pygame.transform.rotate(base, angle)
        except: self.image = None

    def update(self, dt):
        self.pos += self.vel * dt
        self.rect.topleft = self.pos
        self.timer += dt
        return self.timer > settings.PROJECTILE_LIFETIME

    def draw(self, surf, ox, oy):
        if self.image: surf.blit(self.image, (self.rect.centerx - self.image.get_width()//2 - ox, self.rect.centery - self.image.get_height()//2 - oy))
        else: pygame.draw.circle(surf, (255, 0, 255), (self.rect.centerx - ox, self.rect.centery - oy), settings.PROJECTILE_SIZE//2)

class Squid:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, settings.SQUID_SIZE, settings.SQUID_SIZE)
        self.pos = pygame.Vector2(x, y)
        self.shoot_cd = random.uniform(0, 2)
        try: self.image = pygame.transform.scale(pygame.image.load("assets/squid.png").convert_alpha(), (settings.SQUID_SIZE, settings.SQUID_SIZE))
        except: self.image = None
        self.move_state, self.move_timer = 'WANDER', 0
        self.wander_vec = pygame.Vector2(0, 0)
        self.hp, self.max_hp, self.hit_timer = settings.SQUID_HP, settings.SQUID_HP, 0
    
    def take_damage(self, amount):
        if self.hit_timer > 0: return False
        self.hp -= amount
        self.hit_timer = 0.2
        return self.hp <= 0
        
    def update(self, dt, player_rect, projectiles_list, others, player_visible=True):
        self.hit_timer = max(0, self.hit_timer - dt)
        
        # Separation logic
        sep = pygame.Vector2(0, 0)
        for o in others:
            if o is not self:
                d = self.pos.distance_to(o.pos)
                if d < 80:
                    diff = self.pos - o.pos
                    if diff.length() > 0: sep += diff.normalize() * (200 / max(1, d))
        
        # If player not visible, force random wander
        force_wander = not player_visible
        
        if force_wander or random.random() < 0.03:
            if self.move_state != 'WANDER' or force_wander: # Ensure we are wandering
                 if force_wander and self.move_state == 'WANDER' and self.move_timer > 0: pass
                 else:
                    self.wander_vec = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
                    self.move_timer = 0.5 if not force_wander else random.uniform(0.5, 1.5)
                    self.move_state = 'WANDER'

        self.move_timer -= dt
        if self.move_timer <= 0:
            if self.move_state == 'ADJUST' and not force_wander:
                self.move_state = 'WANDER'
                self.move_timer = random.uniform(0.3, 0.8)
                self.wander_vec = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                if self.wander_vec.length() > 0: self.wander_vec = self.wander_vec.normalize()
            else:
                self.move_state = 'ADJUST' if not force_wander else 'WANDER'
                self.move_timer = random.uniform(0.5, 1.0)
                if force_wander:
                     self.wander_vec = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                     if self.wander_vec.length() > 0: self.wander_vec = self.wander_vec.normalize()
        
        vel = pygame.Vector2(0, 0)
        
        if not force_wander:
            dist_vec = pygame.Vector2(player_rect.center) - self.pos
            dist = dist_vec.length()

            if self.move_state == 'ADJUST':
                if dist > 0:
                    if dist < 250: vel = -dist_vec.normalize() * 150
                    elif dist > 450: vel = dist_vec.normalize() * 120
            elif self.move_state == 'WANDER':
                vel = self.wander_vec * 100
            
            self.shoot_cd -= dt
            if self.shoot_cd <= 0 and dist < settings.SQUID_SHOOT_DIST:
                self.shoot_cd = 2.0
                projectiles_list.append(Projectile(self.rect.centerx - 24, self.rect.centery - 24, pygame.Vector2(player_rect.center)))
        else:
            # Random movement only
            vel = self.wander_vec * 100
            
        self.pos += (vel + sep * 50) * dt
        self.rect.topleft = self.pos

    def draw(self, surf, ox, oy):
        # Shadow
        sw, sh = int(settings.SQUID_SIZE * 0.7), int(settings.SQUID_SIZE // 3 * 0.7)
        s = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 100), (0, 0, sw, sh))
        surf.blit(s, (self.rect.centerx - sw//2 - ox, self.rect.bottom - sh//2 - oy))

        if self.image:
            if self.hit_timer > 0:
                sq = (self.hit_timer / 0.2) * 0.3
                nw, nh = int(settings.SQUID_SIZE * (1 + sq * 0.5)), int(settings.SQUID_SIZE * (1 - sq))
                img = pygame.transform.scale(self.image, (nw, nh))
                surf.blit(img, (self.rect.centerx - nw//2 - ox, self.rect.bottom - nh - oy))
            else:
                surf.blit(self.image, (self.rect.x - ox, self.rect.y - oy))
        else: pygame.draw.rect(surf, (200, 0, 200), (self.rect.x - ox, self.rect.y - oy, settings.SQUID_SIZE, settings.SQUID_SIZE))
        
        if self.hp < self.max_hp:
            rx, ry = self.rect.x - ox + 12, self.rect.y - oy - 10
            pygame.draw.rect(surf, (255, 0, 0), (rx, ry, 40, 5))
            if self.hp > 0:
                pygame.draw.rect(surf, (0, 255, 0), (rx, ry, int(40 * (self.hp / self.max_hp)), 5))
class TomatoEnemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, settings.TOMATO_SIZE, settings.TOMATO_SIZE)
        self.pos = pygame.Vector2(x, y)
        self.max_hp, self.hp = settings.TOMATO_HP, settings.TOMATO_HP
        self.hit_timer = 0
        self.drop_type = "tomato"
        
        self.state = 'IDLE' 
        self.timer = random.uniform(0.5, 1.5)
        self.vel = pygame.Vector2(0, 0)
        self.angle = 0
        
        try:
            self.base_img = pygame.transform.scale(pygame.image.load("assets/tomato.png").convert_alpha(), (settings.TOMATO_SIZE, settings.TOMATO_SIZE))
            self.angwy_img = pygame.transform.scale(pygame.image.load("assets/tomato_angwy.png").convert_alpha(), (settings.TOMATO_SIZE, settings.TOMATO_SIZE))
        except: 
            self.base_img = None
            self.angwy_img = None

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
                if dist < settings.TOMATO_ATTACK_DIST: # Trigger Attack
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
        # Shadow
        sc = 1.0
        if self.state == 'JUMP':
             t = (0.5 - self.timer) / 0.5
             sc = 1.0 - 0.4 * math.sin(t * 3.14159)
        
        sw, sh = int(settings.TOMATO_SIZE * sc), int(settings.TOMATO_SIZE // 3 * sc)
        s = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 100), (0, 0, sw, sh))
        surf.blit(s, (self.rect.centerx - sw//2 - ox, self.rect.bottom - sh//2 - oy - 5))

        img = self.angwy_img if (self.state in ['CHARGE_PREP', 'ROLLING'] and self.angwy_img) else self.base_img
        if not img: 
            pygame.draw.circle(surf, (255, 0, 0), (self.rect.centerx - ox, self.rect.centery - oy), settings.TOMATO_SIZE//2)
            return

        w, h = settings.TOMATO_SIZE, settings.TOMATO_SIZE
        dx, dy = 0, 0
        if self.state in ['JUMP_PREP', 'LAND']:
            w, h = settings.TOMATO_SIZE + 10, settings.TOMATO_SIZE - 10
            img = pygame.transform.scale(img, (w, h))
            dy = 5
        elif self.state == 'JUMP':
            w, h = settings.TOMATO_SIZE - 10, settings.TOMATO_SIZE + 10
            img = pygame.transform.scale(img, (w, h))
            dy = -10 # Jump up visual
        elif self.state == 'ROLLING':
            img = pygame.transform.rotate(img, self.angle)
            w, h = img.get_size()
            off_dist = 10
            v = pygame.Vector2(0, off_dist).rotate(-self.angle)
            dx, dy = -v.x, -v.y

        elif self.state == 'CHARGE_PREP':
            off = math.sin(pygame.time.get_ticks() * 0.5) * 3
            ox += off

        draw_pos = (self.rect.centerx - w//2 - ox + dx, self.rect.centery - h//2 - oy + dy)
        if self.hit_timer > 0: 
            mask = pygame.mask.from_surface(img)
            surf.blit(mask.to_surface(setcolor=(255, 255, 255, 128), unsetcolor=(0,0,0,0)), draw_pos)
        else:
            surf.blit(img, draw_pos)
        
        if self.hp < self.max_hp:
             rx, ry = self.rect.x - ox + 7, self.rect.y - oy - 15
             pygame.draw.rect(surf, (255, 0, 0), (rx, ry, 40, 5))
             pygame.draw.rect(surf, (0, 255, 0), (rx, ry, int(40 * (self.hp / self.max_hp)), 5))
