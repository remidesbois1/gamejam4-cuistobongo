import pygame, random, math

class Item:
    def __init__(self, x, y, image_path, w=32, h=32):
        self.w, self.h, self.rect = w, h, pygame.Rect(x, y, w, h)
        try: self.image = pygame.transform.scale(pygame.image.load(image_path).convert_alpha(), (w, h))
        except: self.image = None
    def draw(self, surf, ox, oy):
        pos = (self.rect.x - ox, self.rect.y - oy)
        if self.image: surf.blit(self.image, pos)
        else: pygame.draw.rect(surf, (200, 200, 200), (pos[0], pos[1], self.w, self.h))

class Resource(Item):
    def __init__(self, x, y, image_path, w, h, max_health, drop_type):
        super().__init__(x, y, image_path, w, h)
        self.max_health, self.health, self.drop_type = max_health, max_health, drop_type
        self.hit_timer = 0
    
    def update(self, dt):
        self.hit_timer = max(0, self.hit_timer - dt)

    def take_damage(self, amount):
        self.health -= amount
        self.hit_timer = 0.2
        return self.health <= 0

    def draw(self, surf, ox, oy):
        pos = (self.rect.x - ox, self.rect.y - oy)
        
        # Squash effect
        if self.image:
            if self.hit_timer > 0:
                sq = (self.hit_timer / 0.2) * 0.3
                nw, nh = int(self.w * (1 + sq * 0.5)), int(self.h * (1 - sq))
                img = pygame.transform.scale(self.image, (nw, nh))
                # Center horizontally, align bottom
                dx = (self.w - nw) // 2
                dy = (self.h - nh)
                surf.blit(img, (pos[0] + dx, pos[1] + dy))
            else:
                surf.blit(self.image, pos)
        else: pygame.draw.rect(surf, (200, 200, 200), (pos[0], pos[1], self.w, self.h))

        if self.health < self.max_health:
            pos = (self.rect.x - ox, self.rect.y - oy)
            pygame.draw.rect(surf, (50, 0, 0), (pos[0], pos[1] + self.h + 5, self.w, 8))
            pygame.draw.rect(surf, (255, 0, 0), (pos[0], pos[1] + self.h + 5, int(self.w * (self.health / self.max_health)), 8))

class Tomato(Resource):
    def __init__(self, x, y): super().__init__(x, y, "assets/tomato.png", 54, 54, 1, "tomato")
class CheeseOre(Resource):
    def __init__(self, x, y): super().__init__(x, y, random.choice(["assets/fromage_ore1.png", "assets/fromage_ore2.png"]), 72, 72, 3, "cheese")
class Tree(Resource):
    def __init__(self, x, y): super().__init__(x, y, "assets/tree.png", 80, 120, 4, "dough")

class Drop(Item):
    PATHS = {"tomato": "assets/tomato-icon.png", "cheese": "assets/fromage-icon.png", "dough": "assets/dough.png"}
    def __init__(self, x, y, drop_type): super().__init__(x, y, self.PATHS.get(drop_type, ""), 40, 40); self.type = drop_type
    def draw(self, surf, ox, oy):
        pos = (self.rect.x - ox, self.rect.y - oy + math.sin(pygame.time.get_ticks() * 0.005) * 10)
        if self.image: surf.blit(self.image, pos)
        else: pygame.draw.circle(surf, (255, 255, 255), (int(pos[0] + 20), int(pos[1] + 20)), 15)

class DrumItem(Item):
    def __init__(self, x, y): super().__init__(x, y, "assets/drum.png", 64, 64); self.type = "drum_weapon"
