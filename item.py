import pygame
import random

class Item:
    def __init__(self, x, y, image_path, size=32, max_health=None):
        self.size = size
        self.rect = pygame.Rect(x, y, self.size, self.size)
        try:
            self.image = pygame.transform.scale(pygame.image.load(image_path).convert_alpha(), (self.size, self.size))
        except:
            self.image = None
        self.max_health = max_health
        self.health = max_health

    def take_damage(self, amount):
        if self.health is not None:
            self.health -= amount
            return self.health <= 0
        return True

    def draw(self, surface, offset_x, offset_y):
        pos = (self.rect.x - offset_x, self.rect.y - offset_y)
        if self.image:
            surface.blit(self.image, pos)
        else:
            pygame.draw.rect(surface, (200, 200, 200), (pos[0], pos[1], self.size, self.size))
        
        if self.health is not None and self.health < self.max_health:
            pygame.draw.rect(surface, (50, 0, 0), (pos[0], pos[1] + self.size + 5, self.size, 8))
            pygame.draw.rect(surface, (255, 0, 0), (pos[0], pos[1] + self.size + 5, int(self.size * (self.health / self.max_health)), 8))

class Tomato(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/tomato.png", 54)
        self.type = "tomato"

class CheeseOre(Item):
    def __init__(self, x, y):
        super().__init__(x, y, random.choice(["assets/fromage_ore1.png", "assets/fromage_ore2.png"]), 72, 3)
        self.type = "cheese"

class Dough(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/dough.png", 72, 2)
        self.type = "dough"

class DrumItem(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/drum.png", 64)
        self.type = "drum_weapon"
