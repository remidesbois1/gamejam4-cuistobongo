import pygame, random, math, settings
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
        for _ in range(28):
            for _ in range(50):
                ex, ey = random.uniform(300, w - 300), random.uniform(300, h - 300)
                if safe_func(ex, ey, 80):
                    self.enemies.append(TomatoEnemy(ex, ey))
                    break

    def update(self, dt, player, dim, portals=[], oven_pos=None, oven_dim=1, items_flee=False):
        for en in self.enemies:
            target_dim = getattr(en, 'dim', 1 if isinstance(en, TomatoEnemy) else 0)
            
            if oven_pos and target_dim == oven_dim:
                 dist_to_oven = en.pos.distance_to(oven_pos)
                 safe_radius = settings.OVEN_SAFE_ZONE_RADIUS + 15
                 if dist_to_oven < safe_radius:
                     push_vec = (en.pos - oven_pos).normalize() * 500
                     en.pos += push_vec * dt
                     en.rect.center = en.pos
                     en.rect.topleft = en.pos

            if isinstance(en, Squid):
                en.update(dt, player.rect, self.projectiles, self.enemies, player_visible=(dim==target_dim), portals=portals)
                if dim == target_dim and en.rect.colliderect(player.rect):
                    player.take_damage(5)

            elif dim == target_dim:
                en.update(dt, player.rect, self.projectiles, self.enemies)
                if en.rect.colliderect(player.rect):
                    player.take_damage(5)
            
        for proj in self.projectiles[:]:
            if proj.update(dt):
                self.projectiles.remove(proj)
                continue
                
            if oven_pos:
                 target_dim = getattr(proj, 'dim', 0)
                 if target_dim == oven_dim:
                     if proj.pos.distance_to(oven_pos) < settings.OVEN_SAFE_ZONE_RADIUS + 20:
                         try: self.projectiles.remove(proj)
                         except: pass
                         continue

            target_dim = getattr(proj, 'dim', 0)
            if target_dim == dim and proj.rect.colliderect(player.rect):
                 player.take_damage(10)
                 try: self.projectiles.remove(proj)
                 except: pass

        for d in self.drops[:]:
            target_dim = getattr(d, 'dim', 1) 
            if items_flee and dim == target_dim:
                d.update(dt, player.rect)
                
            if d.type == "tomato":
                 # Check correct dimension
                 target_dim = getattr(d, 'dim', 1) 
                 if dim == target_dim and player.rect.colliderect(d.rect):
                    if player.inventory.add_item(d.type): self.drops.remove(d)

    def draw(self, surf, ox, oy, dim):
        for en in self.enemies:
            target_dim = getattr(en, 'dim', 1 if isinstance(en, TomatoEnemy) else 0)
            if dim == target_dim: en.draw(surf, ox, oy)
            
        for proj in self.projectiles:
            target_dim = getattr(proj, 'dim', 0)
            if dim == target_dim: proj.draw(surf, ox, oy)
            
        for d in self.drops:
            if d.type == "tomato" and dim == d.dim: d.draw(surf, ox, oy)

    def check_hit(self, pos, damage, dim, radius=200):
        px, py = pos
        for en in self.enemies[:]:
            target_dim = getattr(en, 'dim', 1 if isinstance(en, TomatoEnemy) else 0)
            if dim != target_dim: continue
            
            if math.hypot(px - en.rect.centerx, py - en.rect.centery) < radius:
                if en.take_damage(damage):
                    if hasattr(en, 'drop_type') and en.drop_type:
                        self.drops.append(Drop(en.rect.x, en.rect.y, en.drop_type, dim=target_dim))
                    self.enemies.remove(en)
