import random, math, pygame, numpy as np, settings
from item import Tomato, CheeseOre, Dough, DrumItem
from portal import Portal
from oven import PizzaOven
from effects import Shockwave

class WorldManager:
    def __init__(self, map_inst):
        self.map, self.dim, self.portals = map_inst, 1, [Portal(x, y) for x, y in [(settings.MAP_WIDTH//4-64, settings.MAP_HEIGHT//4-64), (3*settings.MAP_WIDTH//4-64, settings.MAP_HEIGHT//4-64), (settings.MAP_WIDTH//4-64, 3*settings.MAP_HEIGHT//4-64), (3*settings.MAP_WIDTH//4-64, 3*settings.MAP_HEIGHT//4-64)]]
        self.oven = PizzaOven(settings.MAP_WIDTH//2-60, settings.MAP_HEIGHT//2-60)
        self.toms, self.cheese, self.doughs, self.weaps = [], [], [], [DrumItem(settings.MAP_WIDTH//2+150, settings.MAP_HEIGHT//2+50)]
        self.spawn()
        self.in_p, self.effs, self.cd = False, [], 0
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
        for _ in range(20): self.toms.append(Tomato(random.randint(0, settings.MAP_WIDTH-60), random.randint(0, settings.MAP_HEIGHT-60)))
        for _ in range(10): self.cheese.append(CheeseOre(random.randint(0, settings.MAP_WIDTH-80), random.randint(0, settings.MAP_HEIGHT-80)))
        for _ in range(15): self.doughs.append(Dough(random.randint(0, settings.MAP_WIDTH-80), random.randint(0, settings.MAP_HEIGHT-80)))

    def trigger_weapon(self, p):
        if p.weapon == "drum_weapon" and self.cd <= 0:
            self.effs.append(Shockwave(p))
            self.cd = 1.0
            if self.sounds: random.choice(self.sounds).play()
            if self.dim == 0:
                for i in self.cheese + self.doughs:
                    if math.hypot(p.rect.centerx-i.rect.centerx, p.rect.centery-i.rect.centery) < 200:
                        if i.take_damage(1):
                            if i in self.cheese: self.cheese.remove(i)
                            else: self.doughs.remove(i)
                            p.inventory.add_item(i.type)
            return True
        return False

    def update(self, p, dt):
        self.cd = max(0, self.cd - dt)
        for po in self.portals: po.update(dt)
        for e in self.effs[:]:
            e.update(dt)
            if e.done: self.effs.remove(e)
        coll = False
        for po in self.portals:
            if p.rect.colliderect(po.rect):
                coll = True
                if not self.in_p and p.rect.colliderect(po.get_hitbox()):
                    self.dim, self.in_p = 1 - self.dim, True
                    return True
                break
        if not coll: self.in_p = False
        if self.dim == 1:
            self.oven.update(p.rect)
            for w in self.weaps[:]:
                if p.rect.colliderect(w.rect):
                    p.weapon = w.type
                    self.weaps.remove(w)
            for t in self.toms[:]:
                if p.rect.colliderect(t.rect) and p.inventory.add_item("tomato"): self.toms.remove(t)
        return False

    def draw(self, s, ox, oy):
        self.map.draw(s, ox, oy, self.dim)
        items = (self.cheese + self.doughs) if self.dim == 0 else (self.toms + self.weaps)
        for i in items: i.draw(s, ox, oy)
        if self.dim == 1: self.oven.draw(s, ox, oy)
        for po in self.portals: po.draw(s, ox, oy)
        for e in self.effs: e.draw(s, ox, oy)
