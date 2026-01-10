import pygame

class PizzaOven:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 120, 120)
        self.active = False
        try:
            self.image = pygame.transform.scale(pygame.image.load("assets/oven.png").convert_alpha(), (120, 120))
        except:
            self.image = None

    def update(self, player_rect):
        self.active = pygame.Vector2(self.rect.center).distance_to(player_rect.center) < 150

    def draw(self, surface, ox, oy):
        pos = (self.rect.x - ox, self.rect.y - oy)
        if self.active:
            s = pygame.Surface((140, 140), pygame.SRCALPHA)
            pygame.draw.rect(s, (255, 255, 100, 100), (0, 0, 140, 140), border_radius=15)
            surface.blit(s, (pos[0]-10, pos[1]-10))
            f = pygame.font.SysFont("Arial", 24, True)
            t = f.render("Appuyer sur E pour Cuisiner", True, (255, 255, 255))
            surface.blit(t, (self.rect.centerx - ox - t.get_width()//2, pos[1]-40))
        if self.image: surface.blit(self.image, pos)
        else: pygame.draw.rect(surface, (150, 75, 0), (pos[0], pos[1], 120, 120))
