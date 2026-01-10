import pygame

class Shockwave:
    def __init__(self, target):
        self.target = target
        self.radius, self.duration, self.timer = 220, 0.4, 0
        try: self.img = pygame.image.load("assets/shockwave.png").convert_alpha()
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
