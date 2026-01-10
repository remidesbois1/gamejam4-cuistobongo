import pygame

class PizzaOven:
    def __init__(self, x, y):
        self.w, self.h = 130, 160
        self.rect = pygame.Rect(x, y, self.w, self.h)
        self.active = False
        try:
            self.image = pygame.transform.scale(pygame.image.load("assets/oven.png").convert_alpha(), (self.w, self.h))
        except:
            self.image = None
        self.f = pygame.font.Font("assets/Handpixies.ttf", 24)

    def update(self, player_rect):
        self.active = pygame.Vector2(self.rect.center).distance_to(player_rect.center) < 180

    def draw(self, surface, ox, oy):
        pos = (self.rect.x - ox, self.rect.y - oy)
        if self.active:
            s = pygame.Surface((self.w + 20, self.h + 20), pygame.SRCALPHA)
            pygame.draw.rect(s, (255, 215, 0, 60), s.get_rect(), border_radius=15)
            pygame.draw.rect(s, (255, 215, 0), s.get_rect(), 3, border_radius=15)
            surface.blit(s, (pos[0]-10, pos[1]-10))
            
            ts = self.f.render("Appuyer sur E pour Cuisiner", True, (0, 0, 0))
            t = self.f.render("Appuyer sur E pour Cuisiner", True, (255, 255, 255))
            tx = self.rect.centerx - ox - t.get_width()//2
            ty = pos[1] - 40
            surface.blit(ts, (tx + 2, ty + 2))
            surface.blit(t, (tx, ty))

        if self.image: surface.blit(self.image, pos)
        else: pygame.draw.rect(surface, (150, 75, 0), (pos[0], pos[1], self.w, self.h))
