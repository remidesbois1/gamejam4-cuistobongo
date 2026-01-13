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
        self.pills = []
        self.pill_effect_timer = 0
        self.bonuses = [
            Bonus("Bombes de l'Abbaye", "Évacuez la gare de Reims !!", self.bonus_bombs, "assets/BOMB.png"),
            Bonus("Cinquième Sens", "Indique la direction des ingrédients !", self.bonus_compass, "assets/Boussole.png"),
            Bonus("Here we go !", "Échange la vision contre la vitesse !", self.bonus_pills, "assets/Drug.png")
        ]
        
    def new_round(self, bonus=None):
        self.active_bonus = None
        self.bombs.clear()
        self.pills.clear()
        self.pill_effect_timer = 0
        
        if bonus:
            self.active_bonus = bonus
            bonus.apply(self.world, self)
            
    def update(self, dt, player):
        for b in self.bombs[:]:
            if b.update(dt, player, self.world):
                self.bombs.remove(b)
        
        self.pill_effect_timer = max(0, self.pill_effect_timer - dt)
        for p in self.pills[:]:
            if p.update(dt, player, self):
                self.pills.remove(p)
                
    def draw(self, surface, cam_x, cam_y, player):
        for b in self.bombs:
            b.draw(surface, cam_x, cam_y, self.world.dim)
            
        for p in self.pills:
            p.draw(surface, cam_x, cam_y, self.world.dim)
            
        if self.pill_effect_timer > 0:
            overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
            hue = (pygame.time.get_ticks() * 0.1) % 360
            color = pygame.Color(0,0,0)
            color.hsva = (hue, 100, 100, 100)
            overlay.fill(color)
            overlay.set_alpha(25) 
            surface.blit(overlay, (0, 0), special_flags=pygame.BLEND_ADD)
            
        if self.active_bonus and self.active_bonus.name == "Boussole s'affole":
            self.draw_compass(surface, player)

    def draw_compass(self, surface, player):
        targets = []
        p_center = player.rect.center
        
        if self.world.dim == 1:
            nearest, min_dist = None, 999999
            for e in self.world.enemy_manager.enemies:
                if isinstance(e, TomatoEnemy) and e.dim == 1:
                    d = math.hypot(e.rect.centerx - p_center[0], e.rect.centery - p_center[1])
                    if d < min_dist: nearest, min_dist = e, d
            if nearest: targets.append((nearest.rect.center, (255, 50, 50)))
            
        else:
            n_cheese, d_cheese = None, 999999
            n_tree, d_tree = None, 999999
            
            for r in self.world.res_manager.res:
                if r.exists_in_dim(0):
                     d = math.hypot(r.rect.centerx - p_center[0], r.rect.centery - p_center[1])
                     if r.drop_type == "cheese":
                         if d < d_cheese: n_cheese, d_cheese = r, d
                     elif r.drop_type == "dough":
                         if d < d_tree: n_tree, d_tree = r, d
                         
            if n_cheese: targets.append((n_cheese.rect.center, (255, 255, 50)))
            if n_tree: targets.append((n_tree.rect.center, (180, 50, 255)))

        for t_pos, col in targets:
            self.draw_arrow(surface, p_center, t_pos, col)

    def draw_arrow(self, surface, p_pos, t_pos, color):
        dx, dy = t_pos[0] - p_pos[0], t_pos[1] - p_pos[1]
        dist = math.hypot(dx, dy)
        if dist < 300: return
        
        angle = math.atan2(dy, dx)
        cx, cy = settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2
        ax, ay = cx + math.cos(angle) * 150, cy + math.sin(angle) * 150
        pts = [
            (ax + math.cos(angle) * 20, ay + math.sin(angle) * 20),
            (ax + math.cos(angle + 2.6) * 15, ay + math.sin(angle + 2.6) * 15),
            (ax + math.cos(angle - 2.6) * 15, ay + math.sin(angle - 2.6) * 15)
        ]
        pygame.draw.polygon(surface, color, pts)
        pygame.draw.polygon(surface, (255, 255, 255), pts, 2)

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

    def bonus_compass(self, world, manager):
        pass

    def bonus_pills(self, world, manager):
        count = random.randint(settings.PILL_COUNT_MIN, settings.PILL_COUNT_MAX)
        w, h = world.map.width, world.map.height
        for _ in range(count):
            for _ in range(50):
                 ex, ey = random.uniform(300, w - 300), random.uniform(300, h - 300)
                 if world.is_safe(ex, ey, 50):
                     manager.pills.append(Pill(ex, ey))
                     break

class Pill:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, 32, 32)
        self.rect.center = (x, y)
        try: self.image = pygame.transform.scale(pygame.image.load("assets/Drug.png").convert_alpha(), (48, 48))
        except: self.image = None
        self.bob_timer = random.random() * 6.28
        
    def update(self, dt, player, manager):
        self.bob_timer += dt * 5
        if player.rect.colliderect(self.rect):
             manager.pill_effect_timer = settings.PILL_DURATION_TIME
             return True # Consumed
        return False
        
    def draw(self, surface, cam_x, cam_y, dim):
        s = pygame.Surface((24, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 80), (0, 0, 24, 10))
        surface.blit(s, (self.rect.centerx - 12 - cam_x, self.rect.bottom - 5 - cam_y))

        off_y = math.sin(self.bob_timer) * 5
        pos = (self.rect.centerx - 24 - cam_x, self.rect.centery - 24 - cam_y + off_y)
        
        if self.image:
            surface.blit(self.image, pos)
        else:
            pygame.draw.ellipse(surface, (255, 100, 200), (pos[0], pos[1], 32, 32))
            pygame.draw.ellipse(surface, (255, 255, 255), (pos[0], pos[1], 32, 32), 2)
