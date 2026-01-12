import pygame, random, math
from enemy import Squid, TomatoEnemy
from item import Drop

class EnemyManager:
    def __init__(self):
        self.enemies = []
        self.projectiles = []
        self.drops = []

    def spawn(self, safe_func, w, h):
        self.enemies.clear()
        self.projectiles.clear()
        self.drops.clear()
        
        # Squids
        for _ in range(15):
            for _ in range(50):
                ex, ey = random.uniform(300, w - 300), random.uniform(300, h - 300)
                if safe_func(ex, ey, 100):
                    self.enemies.append(Squid(ex, ey))
                    break
        
        # Tomatoes
        for _ in range(25):
            for _ in range(50):
                ex, ey = random.uniform(300, w - 300), random.uniform(300, h - 300)
                if safe_func(ex, ey, 80):
                    self.enemies.append(TomatoEnemy(ex, ey))
                    break

    def update(self, dt, player, dim, portals=[]):
        for en in self.enemies:
            target = 1 if isinstance(en, TomatoEnemy) else 0

            if isinstance(en, Squid):
                en.update(dt, player.rect, self.projectiles, self.enemies, player_visible=(dim==0), portals=portals)
                if dim == target and en.rect.colliderect(player.rect):
                    player.take_damage(5)

            elif dim == target:
                en.update(dt, player.rect, self.projectiles, self.enemies)
                if en.rect.colliderect(player.rect):
                    player.take_damage(5)
            
        for proj in self.projectiles[:]:
            if proj.update(dt):
                self.projectiles.remove(proj)
                continue
            if dim == 0 and proj.rect.colliderect(player.rect):
                player.take_damage(10)
                try: self.projectiles.remove(proj)
                except: pass

        for d in self.drops[:]:
            if d.type == "tomato":
                if dim == 1 and player.rect.colliderect(d.rect):
                    if player.inventory.add_item(d.type): self.drops.remove(d)

    def draw(self, surf, ox, oy, dim):
        for en in self.enemies:
            target = 1 if isinstance(en, TomatoEnemy) else 0
            if dim == target: en.draw(surf, ox, oy)
            
        if dim == 0:
            for proj in self.projectiles: proj.draw(surf, ox, oy)
            
        for d in self.drops:
            if d.type == "tomato" and dim == 1: d.draw(surf, ox, oy)

    def check_hit(self, pos, damage, dim, radius=200):
        px, py = pos
        for en in self.enemies[:]:
            target = 1 if isinstance(en, TomatoEnemy) else 0
            if dim != target: continue
            
            if math.hypot(px - en.rect.centerx, py - en.rect.centery) < radius:
                if en.take_damage(damage):
                    if hasattr(en, 'drop_type') and en.drop_type:
                        self.drops.append(Drop(en.rect.x, en.rect.y, en.drop_type))
                    self.enemies.remove(en)
