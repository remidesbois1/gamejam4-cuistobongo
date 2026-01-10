import pygame
from item import Item

class Portal(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/portal.png", 128, 128)
        self.angle = 0
        self.orig = self.image
        
    def update(self, dt):
        self.angle = (self.angle + 100 * dt) % 360
        if self.orig:
            self.image = pygame.transform.rotate(self.orig, self.angle)

    def get_hitbox(self):
        return self.rect.inflate(-64, -64)

    def draw(self, surface, ox, oy):
        if self.image:
            r = self.image.get_rect(center=self.rect.center)
            surface.blit(self.image, (r.x - ox, r.y - oy))
        else:
            pygame.draw.circle(surface, (100, 0, 200), (self.rect.centerx - ox, self.rect.centery - oy), 64)
