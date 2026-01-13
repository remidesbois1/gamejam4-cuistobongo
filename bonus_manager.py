import pygame, random, math
import settings
from effects import NoteParticle
from item import Drop
from enemy import TomatoEnemy

class Bomb:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, 48, 48)
        self.rect.center = (x, y)
        try:
             self.image = pygame.transform.scale(pygame.image.load("assets/BOMB.png").convert_alpha(), (48, 48))
        except:
             self.image = pygame.Surface((48, 48))
             self.image.fill((50, 50, 50))
             pygame.draw.circle(self.image, (0, 0, 0), (24, 24), 24)
             
        self.state = 'WAITING' # WAITING, ATTACHED
        self.timer = 0
        self.fuse_time = 4.0
        self.target_player = None
        self.dim = 1 # Start with normal

    def update(self, dt, player, world):
        if self.state == 'WAITING':
            if player.rect.colliderect(self.rect) and world.dim == self.dim:
                self.state = 'ATTACHED'
                self.target_player = player
                try: self.s_fuse = pygame.mixer.Sound("assets/fuse.mp3"); self.s_fuse.play()
                except: pass
                
        elif self.state == 'ATTACHED':
            self.timer += dt
            self.rect.centerx = self.target_player.rect.centerx
            self.rect.bottom = self.target_player.rect.top - 10
            
            if self.timer >= self.fuse_time:
                self.explode(world)
                return True
        
        return False

    def explode(self, world):
        ex_x, ex_y = self.rect.center
        radius = 300
        
        # Explosion Visuals - Saxophone Style
        c = pygame.Color(0,0,0)
        c.hsva = (random.randint(0, 360), 100, 100, 100)
        col = (c.r, c.g, c.b)
        
        for _ in range(50): 
            world.effs.append(NoteParticle(ex_x, ex_y, col))
        
        # Destroy Enemies
        to_remove = []
        for e in world.enemy_manager.enemies:
            dx, dy = e.rect.centerx - ex_x, e.rect.centery - ex_y
            if math.hypot(dx, dy) < radius:
                if e.dim == world.dim: 
                    to_remove.append(e)
        
        for e in to_remove:
            if isinstance(e, TomatoEnemy):
                world.res_manager.drops.append(Drop(e.rect.x, e.rect.y, "tomato"))
            world.enemy_manager.enemies.remove(e)
            
        # Destroy Resources
        to_min = []
        for r in world.res_manager.res:
             if r.exists_in_dim(world.dim):
                 dx, dy = r.rect.centerx - ex_x, r.rect.centery - ex_y
                 if math.hypot(dx, dy) < radius:
                     to_min.append(r)
        
        for r in to_min:
            world.res_manager.drops.append(Drop(r.rect.x, r.rect.y, r.drop_type))
            world.res_manager.res.remove(r)
            
        # Sound
        try: 
            s = pygame.mixer.Sound("assets/tir.wav")
            s.set_volume(0.4)
            s.play()
        except: pass

    def draw(self, surface, cam_x, cam_y, current_dim):
        if self.dim != current_dim and self.state == 'WAITING': return
        
        if self.state == 'ATTACHED':
             off_x = math.sin(pygame.time.get_ticks() * 0.05) * 3
             surface.blit(self.image, (self.rect.x - cam_x + off_x, self.rect.y - cam_y))
        else:
             surface.blit(self.image, (self.rect.x - cam_x, self.rect.y - cam_y))


class Bonus:
    def __init__(self, name, description, func, icon_path):
        self.name = name
        self.description = description
        self.func = func
        try: self.icon = pygame.transform.scale(pygame.image.load(icon_path).convert_alpha(), (128, 128))
        except: self.icon = None
    
    def apply(self, world, manager):
        self.func(world, manager)

class BonusManager:
    def __init__(self, world):
        self.world = world
        self.active_bonus = None
        self.bombs = []
        self.bonuses = [
            Bonus("Bombes Culinaires", "Nettoyez la zone !", self.bonus_bombs, "assets/BOMB.png"),
        ]
        
    def new_round(self, bonus=None):
        self.active_bonus = None
        self.bombs.clear()
        
        if bonus:
            self.active_bonus = bonus
            bonus.apply(self.world, self)
            
    def update(self, dt, player):
        for b in self.bombs[:]:
            if b.update(dt, player, self.world):
                self.bombs.remove(b)
                
    def draw(self, surface, cam_x, cam_y):
        for b in self.bombs:
            b.draw(surface, cam_x, cam_y, self.world.dim)
            
    def bonus_bombs(self, world, manager):
        count = random.randint(settings.BOMBS_COUNT_MIN, settings.BOMBS_COUNT_MAX)
        w, h = world.map.width, world.map.height
        for _ in range(count):
            for _ in range(50):
                 ex, ey = random.uniform(300, w - 300), random.uniform(300, h - 300)
                 if world.is_safe(ex, ey, 50):
                     b = Bomb(ex, ey)
                     b.dim = random.choice([0, 1])
                     manager.bombs.append(b)
                     break
