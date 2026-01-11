import pygame, random, math

class Item:
    def __init__(self, x, y, image_path, w=32, h=32):
        self.w, self.h, self.rect = w, h, pygame.Rect(x, y, w, h)
        try: self.image = pygame.transform.scale(pygame.image.load(image_path).convert_alpha(), (w, h))
        except: self.image = None
    def draw(self, surf, ox, oy, dim=None):
        pos = (self.rect.x - ox, self.rect.y - oy)
        if self.image: surf.blit(self.image, pos)
        else: pygame.draw.rect(surf, (200, 200, 200), (pos[0], pos[1], self.w, self.h))

class Resource(Item):
    def __init__(self, x, y, image_path, w, h, max_health, drop_type, alt_image_path=None):
        super().__init__(x, y, image_path, w, h)
        self.max_health, self.health, self.drop_type = max_health, max_health, drop_type
        self.hit_timer = 0
        self.alt_image = None
        if alt_image_path:
            try: self.alt_image = pygame.transform.scale(pygame.image.load(alt_image_path).convert_alpha(), (w, h))
            except: pass
    
    def update(self, dt):
        self.hit_timer = max(0, self.hit_timer - dt)

    def take_damage(self, amount, dim):
        if self.alt_image:
            if dim == 1: return False
        else:
            if dim == 0: return False
            
        if self.hit_timer > 0: return False
        
        self.health -= amount
        self.hit_timer = 0.2
        return self.health <= 0

    def draw(self, surf, ox, oy, dim):
        img_to_draw = self.image
        if self.alt_image:
            if dim == 0: img_to_draw = self.alt_image
        else:
            if dim == 0: return
        
        pos = (self.rect.x - ox, self.rect.y - oy)
        
        if img_to_draw:
            if self.hit_timer > 0:
                sq = (self.hit_timer / 0.2) * 0.3
                nw, nh = int(self.w * (1 + sq * 0.5)), int(self.h * (1 - sq))
                img = pygame.transform.scale(img_to_draw, (nw, nh))
                dx = (self.w - nw) // 2
                dy = (self.h - nh)
                surf.blit(img, (pos[0] + dx, pos[1] + dy))
            else:
                surf.blit(img_to_draw, pos)
        else: pygame.draw.rect(surf, (200, 200, 200), (pos[0], pos[1], self.w, self.h))

        if self.health < self.max_health and (dim == 0 or not self.alt_image):
            if self.alt_image and dim == 1: return

            pos = (self.rect.x - ox, self.rect.y - oy)
            pygame.draw.rect(surf, (50, 0, 0), (pos[0], pos[1] + self.h + 5, self.w, 8))
            pygame.draw.rect(surf, (255, 0, 0), (pos[0], pos[1] + self.h + 5, int(self.w * (self.health / self.max_health)), 8))

class Tomato(Resource):
    def __init__(self, x, y): 
        super().__init__(x, y, "assets/tomato.png", 54, 54, 1, "tomato")

class CheeseOre(Resource):
    def __init__(self, x, y):
        if random.random() < 0.5:
            normal, alt = "assets/stone.png", "assets/fromage_ore1.png"
        else:
            normal, alt = "assets/stone2.png", "assets/fromage_ore2.png"
        super().__init__(x, y, normal, 72, 72, 3, "cheese", alt_image_path=alt)

class Tree(Resource):
    def __init__(self, x, y): 
        super().__init__(x, y, "assets/tree-normal.png", 80, 120, 4, "dough", alt_image_path="assets/tree.png")

class Drop(Item):
    PATHS = {"tomato": "assets/tomato-icon.png", "cheese": "assets/fromage-icon.png", "dough": "assets/dough.png"}
    def __init__(self, x, y, drop_type): super().__init__(x, y, self.PATHS.get(drop_type, ""), 40, 40); self.type = drop_type
    def draw(self, surf, ox, oy, dim=None):
        t = pygame.time.get_ticks() * 0.005
        bob = math.sin(t)
        
        # Shadow
        sc = 1.0 - 0.3 * bob # Shrink when high
        sw, sh = int(30 * sc), int(10 * sc)
        s = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 100), (0, 0, sw, sh))
        surf.blit(s, (self.rect.centerx - sw//2 - ox, self.rect.bottom - sh//2 - oy + 10))

        pos = (self.rect.x - ox, self.rect.y - oy + bob * 10)
        if self.image: surf.blit(self.image, pos)
        else: pygame.draw.circle(surf, (255, 255, 255), (int(pos[0] + 20), int(pos[1] + 20)), 15)

class DrumItem(Item):
    def __init__(self, x, y): super().__init__(x, y, "assets/drum.png", 64, 64); self.type = "drum_weapon"

class PanItem(Item):
    def __init__(self, x, y): super().__init__(x, y, "assets/chief_pan.png", 64, 64); self.type = "pan_weapon"

class SaxItem(Item):
    def __init__(self, x, y): super().__init__(x, y, "assets/chief_sax.png", 64, 64); self.type = "sax_weapon"
