import random, math, pygame, numpy as np, settings
from item import Tomato, CheeseOre, Tree, Drop, DrumItem
from portal import Portal
from oven import PizzaOven
from effects import Shockwave

class WorldManager:
    def __init__(self, map_inst):
        self.map, self.dim = map_inst, 1
        ps = [(settings.MAP_WIDTH//4-64, settings.MAP_HEIGHT//4-64), (3*settings.MAP_WIDTH//4-64, settings.MAP_HEIGHT//4-64), 
              (settings.MAP_WIDTH//4-64, 3*settings.MAP_HEIGHT//4-64), (3*settings.MAP_WIDTH//4-64, 3*settings.MAP_HEIGHT//4-64)]
        self.portals = [Portal(x, y) for x, y in ps]
        self.oven = PizzaOven(settings.MAP_WIDTH//2-60, settings.MAP_HEIGHT//2-60)
        self.res, self.drops, self.weaps = [], [], [DrumItem(settings.MAP_WIDTH//2+150, settings.MAP_HEIGHT//2+50)]
        self.spawn()
        self.in_p, self.effs, self.cd, self.cd_limit = False, [], 0, 1.0
        self.sounds = []
        try:
            pygame.mixer.init()
            s = pygame.mixer.Sound("assets/tambour.wav")
            for r in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5]:
                a = pygame.sndarray.array(s)
                self.sounds.append(pygame.sndarray.make_sound(a[np.round(np.linspace(0, len(a)-1, int(len(a)/r))).astype(int)]))
            for snd in self.sounds: snd.set_volume(0.4)
        except: pass

    def spawn(self):
        for _ in range(20): self.res.append(Tomato(random.randint(0, settings.MAP_WIDTH-60), random.randint(0, settings.MAP_HEIGHT-60)))
        for _ in range(10): self.res.append(CheeseOre(random.randint(0, settings.MAP_WIDTH-80), random.randint(0, settings.MAP_HEIGHT-80)))
        for _ in range(15): self.res.append(Tree(random.randint(0, settings.MAP_WIDTH-100), random.randint(0, settings.MAP_HEIGHT-100)))

    def trigger_weapon(self, p):
        if p.weapon == "drum_weapon" and self.cd <= 0:
            self.effs.append(Shockwave(p))
            self.cd = self.cd_limit
            if self.sounds: random.choice(self.sounds).play()
            for r in self.res[:]:
                if ((self.dim == 1 and isinstance(r, Tomato)) or (self.dim == 0 and not isinstance(r, Tomato))) and math.hypot(p.rect.centerx-r.rect.centerx, p.rect.centery-r.rect.centery) < 200:
                    if r.take_damage(1):
                        self.drops.append(Drop(r.rect.x, r.rect.y, r.drop_type))
                        self.res.remove(r)
            return True
        return False

    def update(self, p, dt):
        self.cd, coll = max(0, self.cd - dt), False
        for po in self.portals: po.update(dt)
        for e in self.effs[:]:
            e.update(dt)
            if e.done: self.effs.remove(e)
        for po in self.portals:
            if p.rect.colliderect(po.rect):
                coll = True
                if not self.in_p and p.rect.colliderect(po.get_hitbox()): self.dim, self.in_p = 1 - self.dim, True; return True
                break
        if not coll: self.in_p = False
        for d in self.drops[:]:
            if ((self.dim == 1 and d.type == "tomato") or (self.dim == 0 and d.type != "tomato")) and p.rect.colliderect(d.rect) and p.inventory.add_item(d.type): self.drops.remove(d)
        if self.dim == 1:
            self.oven.update(p.rect)
            for w in self.weaps[:]:
                if p.rect.colliderect(w.rect): p.weapon, _ = w.type, self.weaps.remove(w)
        return False

    def draw(self, s, ox, oy):
        self.map.draw(s, ox, oy, self.dim)
        for r in self.res:
            if (self.dim == 1 and isinstance(r, Tomato)) or (self.dim == 0 and not isinstance(r, Tomato)): r.draw(s, ox, oy)
        for d in self.drops:
            if (self.dim == 1 and d.type == "tomato") or (self.dim == 0 and d.type != "tomato"): d.draw(s, ox, oy)
        if self.dim == 1:
            self.oven.draw(s, ox, oy)
            for w in self.weaps: w.draw(s, ox, oy)
        for po in self.portals: po.draw(s, ox, oy)
        for e in self.effs: e.draw(s, ox, oy)
