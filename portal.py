import pygame, random, math, settings
from item import Item

class Portal(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/portal.png", 128, 128)
        self.angle = 0
        self.orig = self.image
        self.pos = pygame.Vector2(x, y)
        
        # Movement state
        self.moving = False
        self.vel = pygame.Vector2(0, 0)
        self.target_vel = pygame.Vector2(0, 0)
        self.move_timer = 0

    def update(self, dt):
        self.angle = (self.angle + 100 * dt) % 360
        if self.orig:
            self.image = pygame.transform.rotate(self.orig, self.angle)
        
        if self.moving:
            self.move_timer -= dt
            if self.move_timer <= 0:
                # Pick new behavior
                self.move_timer = random.uniform(0.5, 2.0)
                if random.random() < 0.2: # Fake / Stop
                    self.target_vel = pygame.Vector2(0, 0)
                else:
                    angle = random.uniform(0, math.pi * 2)
                    speed = random.uniform(150, 250)
                    self.target_vel = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
            
            # Smoothly interpolate velocity for curves
            self.vel = self.vel.lerp(self.target_vel, dt * 3)
            
            self.pos += self.vel * dt
            
            # Clamp to map
            self.pos.x = max(100, min(self.pos.x, settings.MAP_WIDTH - 228))
            self.pos.y = max(100, min(self.pos.y, settings.MAP_HEIGHT - 228))
            self.rect.topleft = self.pos

    def get_hitbox(self):
        return self.rect.inflate(-64, -64)

    def draw(self, surface, ox, oy):
        if self.image:
            r = self.image.get_rect(center=self.rect.center)
            surface.blit(self.image, (r.x - ox, r.y - oy))
        else:
            pygame.draw.circle(surface, (100, 0, 200), (self.rect.centerx - ox, self.rect.centery - oy), 64)
