import pygame, math, random

class Shockwave:
    def __init__(self, target):
        self.target = target
        self.radius, self.duration, self.timer = 220, 0.4, 0
        try: self.img = pygame.image.load("assets/bomgo_effect.png").convert_alpha()
        except: self.img = None

    def update(self, dt):
        self.timer += dt
        self.done = self.timer >= self.duration

    def draw(self, surface, ox, oy):
        if not self.img: return
        p = self.timer / self.duration
        s = int(self.radius * 2 * p)
        if s <= 0: return
        img = pygame.transform.scale(self.img, (s, s))
        img.set_alpha(int(255 * (1 - p)))
        c = self.target.rect.center
        surface.blit(img, (c[0] - ox - s//2, c[1] - oy - s//2))

class MusicNote:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.timer, self.duration = 0, 2.0
        try: self.img = pygame.transform.scale(pygame.image.load("assets/key_sol.png").convert_alpha(), (32, 32))
        except: self.img = None
    
    def update(self, dt):
        self.timer += dt
        self.y -= 50 * dt
        self.done = self.timer >= self.duration
    
    def draw(self, surface, ox, oy):
        if self.img:
            img = self.img.copy()
            img.set_alpha(int(255 * (1 - self.timer / self.duration)))
            surface.blit(img, (self.x - ox, self.y - oy))
        else:
            pygame.draw.circle(surface, (255, 200, 0), (int(self.x - ox), int(self.y - oy)), 10)

class ExplodingNote:
    def __init__(self, x, y, direction):
        self.pos = pygame.Vector2(x, y)
        self.dir = direction.normalize() if direction.length() > 0 else pygame.Vector2(1,0)
        self.speed = 450
        self.timer = 0
        self.explode_time = 0.6
        self.done = False
        self.explode_triggered = False
        
        c = pygame.Color(0,0,0)
        c.hsva = (random.randint(0, 360), 100, 100, 100)
        self.color = (c.r, c.g, c.b)
        
        try: 
            raw_img = pygame.image.load("assets/note_music.png").convert_alpha()
            self.img = pygame.transform.scale(raw_img, (48, 48))
            # Tinting: Make white then multiply
            self.img.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)
            self.img.fill((*self.color, 255), special_flags=pygame.BLEND_RGBA_MULT)
        except: self.img = None

    def update(self, dt):
        self.timer += dt
        if self.timer < self.explode_time:
            self.pos += self.dir * self.speed * dt
        elif not self.explode_triggered:
            self.explode_triggered = True
            self.done = True
            
    def draw(self, surface, ox, oy):
        if self.img:
            angle = math.sin(self.timer * 20) * 40
            rot_img = pygame.transform.rotate(self.img, angle)
            surface.blit(rot_img, (self.pos.x - ox - rot_img.get_width()//2, self.pos.y - oy - rot_img.get_height()//2))
        else:
            pygame.draw.circle(surface, self.color, (int(self.pos.x-ox), int(self.pos.y-oy)), 20)

class NoteParticle:
    def __init__(self, x, y, color):
        self.pos = pygame.Vector2(x, y)
        angle = random.uniform(0, 6.28)
        speed = random.uniform(350, 700)
        self.vel = pygame.Vector2(math.cos(angle)*speed, math.sin(angle)*speed)
        self.timer = 0
        self.duration = random.uniform(0.5, 0.8)
        self.done = False
        self.color = color
        try: 
            raw = pygame.image.load("assets/particule_note.png").convert_alpha()
            self.img = pygame.transform.scale(raw, (32, 32))
            # Tinting
            self.img.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)
            self.img.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
        except: self.img = None
        
    def update(self, dt):
        self.timer += dt
        self.pos += self.vel * dt
        if self.timer >= self.duration: self.done = True
        
    def draw(self, surface, ox, oy):
        if self.img:
            angle = self.timer * 800
            rot = pygame.transform.rotate(self.img, angle)
            alpha = 255
            if self.duration > 0:
                alpha = int(255 * (1 - self.timer / self.duration))
            rot.set_alpha(alpha)
            surface.blit(rot, (self.pos.x - ox - rot.get_width()//2, self.pos.y - oy - rot.get_height()//2))
        else:
            pygame.draw.circle(surface, self.color, (int(self.pos.x-ox), int(self.pos.y-oy)), 8)

class Shockwave:
    def __init__(self, target):
        self.target = target
        self.radius, self.duration, self.timer = 220, 0.4, 0
        try: self.img = pygame.image.load("assets/bomgo_effect.png").convert_alpha()
        except: self.img = None

    def update(self, dt):
        self.timer += dt
        self.done = self.timer >= self.duration

    def draw(self, surface, ox, oy):
        if not self.img: return
        p = self.timer / self.duration
        s = int(self.radius * 2 * p)
        if s <= 0: return
        img = pygame.transform.scale(self.img, (s, s))
        img.set_alpha(int(255 * (1 - p)))
        c = self.target.rect.center
        surface.blit(img, (c[0] - ox - s//2, c[1] - oy - s//2))

class MusicNote:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.timer, self.duration = 0, 2.0
        try: self.img = pygame.transform.scale(pygame.image.load("assets/key_sol.png").convert_alpha(), (32, 32))
        except: self.img = None
    
    def update(self, dt):
        self.timer += dt
        self.y -= 50 * dt
        self.done = self.timer >= self.duration
    
    def draw(self, surface, ox, oy):
        if self.img:
            img = self.img.copy()
            img.set_alpha(int(255 * (1 - self.timer / self.duration)))
            surface.blit(img, (self.x - ox, self.y - oy))
        else:
            pygame.draw.circle(surface, (255, 200, 0), (int(self.x - ox), int(self.y - oy)), 10)
