import pygame, random, math
from item import Tomato, CheeseOre, Tree, Drop

class ResourceManager:
    def __init__(self):
        self.res = []
        self.drops = []

    def spawn(self, safe_func, w, h):
        self.res.clear()
        self.drops.clear()
        types = [(Tree, 25, 4, 6), (CheeseOre, 35, 3, 5)]
        
        for cls, n_clusters, n_per, min_dist in types:
            for _ in range(n_clusters):
                for _ in range(50):
                    cx, cy = random.uniform(300, w - 300), random.uniform(300, h - 300)
                    if safe_func(cx, cy, 150):
                        for _ in range(n_per):
                            for _ in range(20):
                                sang, sdist = random.uniform(0, math.pi*2), random.uniform(0, 200)
                                tx, ty = cx + math.cos(sang) * sdist, cy + math.sin(sang) * sdist
                                if 100 < tx < w-100 and 100 < ty < h-100 and safe_func(tx, ty, min_dist):
                                    self.res.append(cls(tx, ty)); break
                        break

    def is_safe(self, x, y, size):
        for r in self.res:
            if math.hypot(x - r.rect.centerx, y - r.rect.centery) < size: return False
        return True

    def update(self, dt, player, dim, items_flee=False):
        for r in self.res: r.update(dt)
        for d in self.drops[:]:
            if items_flee:
                # Check dim validity for update (logic from draw/collide)
                if (dim == 1 and d.type == "tomato") or (dim == 0 and d.type != "tomato"):
                    d.update(dt, player.rect)

            if ((dim == 1 and d.type == "tomato") or (dim == 0 and d.type != "tomato")) and player.rect.colliderect(d.rect):
                if player.inventory.add_item(d.type):
                    self.drops.remove(d)

    def draw(self, surf, ox, oy, dim):
        for r in self.res:
            r.draw(surf, ox, oy, dim)
        for d in self.drops:
            if (dim == 1 and d.type == "tomato") or (dim == 0 and d.type != "tomato"): 
                d.draw(surf, ox, oy, dim)

    def check_hit(self, pos, damage, dim, radius=200):
        px, py = pos
        for r in self.res[:]:
            if math.hypot(px - r.rect.centerx, py - r.rect.centery) < radius:
                if r.take_damage(damage, dim):
                    self.drops.append(Drop(r.rect.x, r.rect.y, r.drop_type))
                    self.res.remove(r)
