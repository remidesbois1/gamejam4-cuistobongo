import random, math, pygame, numpy as np, settings
from portal import Portal
from oven import PizzaOven
from effects import Shockwave
from enemy_manager import EnemyManager
from resource_manager import ResourceManager
from item import DrumItem

class WorldManager:
    def __init__(self, map_inst):
        self.map, self.dim = map_inst, 1
        w, h = settings.MAP_WIDTH, settings.MAP_HEIGHT
        ps = [(w//2-800, h//2-600), (w//2+800, h//2-600), (w//2-800, h//2+600), (w//2+800, h//2+600)]
        self.portals = [Portal(x, y) for x, y in ps]
        self.oven = PizzaOven(w//2-60, h//2-60)
        self.weaps = []
        
        self.enemy_manager = EnemyManager()
        self.res_manager = ResourceManager()
        self.spawn()
        
        self.in_p, self.effs, self.cd, self.cd_limit, self.damage = False, [], 0, 0.4, 1
        self.sounds = []
        try:
            pygame.mixer.init()
            s = pygame.mixer.Sound("assets/tambour.wav")
            for r in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5]:
                a = pygame.sndarray.array(s)
                self.sounds.append(pygame.sndarray.make_sound(a[np.round(np.linspace(0, len(a)-1, int(len(a)/r))).astype(int)]))
            for snd in self.sounds: snd.set_volume(0.4)
        except: pass

    def is_safe(self, x, y, size):
        for p in self.portals:
            if math.hypot(x - p.rect.centerx, y - p.rect.centery) < 220: return False
        if math.hypot(x - self.oven.rect.centerx, y - self.oven.rect.centery) < 250: return False
        if not self.res_manager.is_safe(x, y, size): return False
        return True

    def spawn(self):
        w, h = settings.MAP_WIDTH, settings.MAP_HEIGHT
        self.res_manager.spawn(self.is_safe, w, h)
        self.enemy_manager.spawn(self.is_safe, w, h)

    def trigger_weapon(self, p):
        if p.weapon == "drum_weapon" and self.cd <= 0:
            self.effs.append(Shockwave(p)); self.cd = self.cd_limit
            if self.sounds: random.choice(self.sounds).play()
            
            self.res_manager.check_hit(p, self.damage, self.dim)
            if self.dim == 0:
                self.enemy_manager.check_hit(p, 10)
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
        
        if self.dim == 1:
            self.oven.update(p.rect)
            for w in self.weaps[:]:
                if p.rect.colliderect(w.rect): p.weapon, _ = w.type, self.weaps.remove(w)
        
        self.res_manager.update(dt, p, self.dim)
        self.enemy_manager.update(dt, p, self.dim)
        return False

    def draw(self, s, ox, oy):
        self.map.draw(s, ox, oy, self.dim)
        self.res_manager.draw(s, ox, oy, self.dim)
        
        if self.dim == 1: 
            self.oven.draw(s, ox, oy)
            [w.draw(s, ox, oy) for w in self.weaps]
        else:
            self.enemy_manager.draw(s, ox, oy, self.dim)
            
        for po in self.portals: po.draw(s, ox, oy)
        for e in self.effs: e.draw(s, ox, oy)
