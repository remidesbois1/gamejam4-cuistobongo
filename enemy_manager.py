import pygame, random, math
from enemy import Squid

class EnemyManager:
    def __init__(self):
        self.enemies = []
        self.projectiles = []

    def spawn(self, safe_func, w, h):
        self.enemies.clear()
        self.projectiles.clear()
        for _ in range(15):
            for _ in range(50):
                ex, ey = random.uniform(300, w - 300), random.uniform(300, h - 300)
                if safe_func(ex, ey, 100):
                    self.enemies.append(Squid(ex, ey))
                    break

    def update(self, dt, player, dim):
        if dim != 0: return
        
        for en in self.enemies:
            en.update(dt, player.rect, self.projectiles, self.enemies)
            
        for proj in self.projectiles[:]:
            if proj.update(dt):
                self.projectiles.remove(proj)
                continue
            if proj.rect.colliderect(player.rect):
                player.take_damage(10)
                try: self.projectiles.remove(proj)
                except: pass

    def draw(self, surf, ox, oy, dim):
        if dim != 0: return
        for en in self.enemies: en.draw(surf, ox, oy)
        for proj in self.projectiles: proj.draw(surf, ox, oy)

    def check_hit(self, pos, damage, radius=200):
        px, py = pos
        for en in self.enemies[:]:
            if math.hypot(px - en.rect.centerx, py - en.rect.centery) < radius:
                if en.take_damage(damage):
                    self.enemies.remove(en)
