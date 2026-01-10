import pygame

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
