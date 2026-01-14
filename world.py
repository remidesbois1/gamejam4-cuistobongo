import random, math, pygame, numpy as np, settings
from portal import Portal
from oven import PizzaOven
from effects import Shockwave, MusicNote, ExplodingNote, NoteParticle
from enemy_manager import EnemyManager
from resource_manager import ResourceManager
from item import DrumItem, PanItem, SaxItem


class WorldManager:
    def __init__(self, map_inst):
        self.map, self.dim = map_inst, 1
        w, h = settings.MAP_WIDTH, settings.MAP_HEIGHT
        ps = [(w//2-800, h//2-600), (w//2+800, h//2-600), (w//2-800, h//2+600), (w//2+800, h//2+600)]
        self.portals = [Portal(x, y) for x, y in ps]
        self.oven = PizzaOven(w//2-60, h//2-60)
        self.weaps = []
        self.items_flee = False
        
        self.enemy_manager = EnemyManager()
        self.res_manager = ResourceManager()
        self.spawn()
        
        self.in_p, self.effs, self.cd, self.cd_limit, self.damage = False, [], 0, 0.4, 1
        self.cd_limit_multiplier = 1.0
        self.sounds, self.pan_sounds = [], []
        try:
            pygame.mixer.init()
            # Drum
            s = pygame.mixer.Sound("assets/tambour.wav")
            for r in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5]:
                a = pygame.sndarray.array(s)
                self.sounds.append(pygame.sndarray.make_sound(a[np.round(np.linspace(0, len(a)-1, int(len(a)/r))).astype(int)]))
            for snd in self.sounds: snd.set_volume(0.4)
            
            # Flute
            f = pygame.mixer.Sound("assets/flute.mp3")
            for r in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5]:
                a = pygame.sndarray.array(f)
                self.pan_sounds.append(pygame.sndarray.make_sound(a[np.round(np.linspace(0, len(a)-1, int(len(a)/r))).astype(int)]))
            for snd in self.pan_sounds: snd.set_volume(0.5)
            # Sax
            sx = pygame.mixer.Sound("assets/saxo.wav")
            self.sax_sounds = []
            for r in [0.8, 1.0, 1.2]:
                 a = pygame.sndarray.array(sx)
                 self.sax_sounds.append(pygame.sndarray.make_sound(a[np.round(np.linspace(0, len(a)-1, int(len(a)/r))).astype(int)]))
            for snd in self.sax_sounds: snd.set_volume(0.4)
        except: pass

    def is_safe(self, x, y, size):
        for p in self.portals:
            if math.hypot(x - p.rect.centerx, y - p.rect.centery) < 220: return False
        if math.hypot(x - self.oven.rect.centerx, y - self.oven.rect.centery) < 250: return False
        if not self.res_manager.is_safe(x, y, size): return False
        return True

    def spawn(self, extra=0, tutorial_stage=0):
        w, h = settings.MAP_WIDTH, settings.MAP_HEIGHT
        self.res_manager.spawn(self.is_safe, w, h)
        self.enemy_manager.spawn(self.is_safe, w, h, extra=extra, tutorial_stage=tutorial_stage)

    def trigger_weapon(self, p):
        if self.cd > 0: return False
        
        limit = self.cd_limit * self.cd_limit_multiplier
        
        if p.weapon == "drum_weapon":
            self.effs.append(Shockwave(p)); self.cd = limit
            if self.sounds: random.choice(self.sounds).play()
            
            self.res_manager.check_hit(p.rect.center, self.damage, self.dim)
            self.enemy_manager.check_hit(p.rect.center, 10, self.dim)
            return True
            
        elif p.weapon == "pan_weapon":
            self.cd = max(0.2, limit * 2.5)
            p.start_dash(p.last_dir)
            if self.pan_sounds: random.choice(self.pan_sounds).play()
            return True

        elif p.weapon == "sax_weapon":
            self.cd = max(0.2, limit * 2.5)
            self.effs.append(ExplodingNote(p.rect.centerx, p.rect.centery, p.last_dir))
            if self.sax_sounds: random.choice(self.sax_sounds).play() 
            return True
        
        return False

    def update(self, p, dt):
        self.cd, coll = max(0, self.cd - dt), False
        for po in self.portals: po.update(dt)
        for e in self.effs[:]:
            e.update(dt)
            
            if isinstance(e, ExplodingNote) and e.explode_triggered:
                self.res_manager.check_hit((e.pos.x, e.pos.y), 3, self.dim, radius=180)
                self.enemy_manager.check_hit((e.pos.x, e.pos.y), 35, self.dim, radius=180)
                for _ in range(22): self.effs.append(NoteParticle(e.pos.x, e.pos.y, e.color))

            if e.done: self.effs.remove(e)
            
        if p.dash_timer > 0:
            if random.random() < 0.3: self.effs.append(MusicNote(p.rect.centerx, p.rect.centery))
            self.res_manager.check_hit(p.rect.center, 2, self.dim, radius=100)
            self.enemy_manager.check_hit(p.rect.center, 20, self.dim, radius=100)

        for po in self.portals:
            if p.rect.colliderect(po.rect):
                coll = True
                if not self.in_p and p.rect.colliderect(po.get_hitbox()): self.dim, self.in_p = 1 - self.dim, True; return True
                break
        if not coll: self.in_p = False
        
        if self.dim == self.oven.dim:
            self.oven.update(p.rect)
        else:
            self.oven.active = False
        
        self.res_manager.update(dt, p, self.dim, items_flee=self.items_flee)
        self.enemy_manager.update(dt, p, self.dim, portals=self.portals, oven_pos=pygame.Vector2(self.oven.rect.center), oven_dim=self.oven.dim, items_flee=self.items_flee)
        return False

    def draw(self, s, ox, oy):
        self.map.draw(s, ox, oy, self.dim)
        self.res_manager.draw(s, ox, oy, self.dim)
        
        if self.dim == self.oven.dim: 
            self.oven.draw(s, ox, oy)
            [w.draw(s, ox, oy) for w in self.weaps]
            
        self.enemy_manager.draw(s, ox, oy, self.dim)
            
        for po in self.portals: po.draw(s, ox, oy)
        for e in self.effs: e.draw(s, ox, oy)
