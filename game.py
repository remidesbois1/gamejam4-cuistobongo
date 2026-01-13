import pygame, sys, settings, random
import numpy as np
from map import Map
from player import Player
from camera import Camera
from world import WorldManager
from menu import Menu
from ui import UI, RouletteMenu
from recipe_menu import RecipeMenu
from order_manager import OrderManager
from shop_menu import ShopMenu
from malus_manager import MalusManager
from bonus_manager import BonusManager

def make_fast_sound(sound):
    try:
        arr = pygame.sndarray.array(sound)
        # Resample for speed (fewer samples)
        new_len = int(len(arr) / settings.MUSIC_SPEED_FACTOR)
        indices = np.linspace(0, len(arr)-1, new_len).astype(int)
        fast_arr = arr[indices]
        return pygame.sndarray.make_sound(fast_arr)
    except:
        return None

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.clock, self.running, self.state = pygame.time.Clock(), True, 'MENU'
        self.menu = Menu(self.screen)
        self.world, self.camera, self.recipe_menu, self.om = None, None, None, OrderManager()
        self.score, self.f_a = 0, 0
        self.f_s = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.f_s.fill((0, 0, 0))
        self.font, self.cheat_buf = pygame.font.Font(settings.FONT_NAME, 36), ""
        self.shop_menu = None
        self.malus_manager = None
        self.last_weapon = None
        self.death_timer = 0
        self.roulette_menu = None
        
        # Music
        try:
            self.music_normal = pygame.mixer.Sound("assets/normal_music.mp3")
            self.music_upside = pygame.mixer.Sound("assets/upside_down_music.mp3")
            
            # Generate Fast Versions
            self.music_normal_fast = make_fast_sound(self.music_normal)
            self.music_upside_fast = make_fast_sound(self.music_upside)
        except:
            self.music_normal = None
            self.music_upside = None
            self.music_normal_fast = None
            self.music_upside_fast = None
            
        self.mus_chan_n = None
        self.mus_chan_u = None
        self.is_fast = False
        self.music_start_time = 0

    def start(self):
        pygame.mixer.stop()
        self.map, self.pizzas_made = Map(), 0
        self.om = OrderManager()
        self.player = Player(settings.MAP_WIDTH//2+settings.PLAYER_SIZE, settings.MAP_HEIGHT//2-settings.PLAYER_SIZE//2, self.map)
        
        # Force weapon to Bomgo (drum) for first round
        self.player.weapon = "drum_weapon"
        self.last_weapon = self.player.weapon
        
        self.world = WorldManager(self.map)
        self.malus_manager = MalusManager(self.world)
        self.bonus_manager = BonusManager(self.world)
        self.camera = Camera(settings.MAP_WIDTH, settings.MAP_HEIGHT)
        self.ui, self.recipe_menu, self.shop_menu, self.roulette_menu = UI(self.font), RecipeMenu(self.font), ShopMenu(self.font), RouletteMenu(self.font)
        self.score, self.f_a, self.wave_timer, self.wave_num, self.state = 0, 0, settings.WAVE_DURATION, 1, 'PLAYING'
        self.pizza_goal, self.round_p = settings.INITIAL_PIZZA_GOAL, 0
        self.extra_enemies = 0
        
        # Start Music (Normal Speed)
        self.is_fast = False
        if self.music_normal and self.music_upside:
            if self.mus_chan_n: self.mus_chan_n.stop()
            if self.mus_chan_u: self.mus_chan_u.stop()
            
            self.mus_chan_n = self.music_normal.play(loops=-1)
            self.mus_chan_u = self.music_upside.play(loops=-1)
            self.music_start_time = pygame.time.get_ticks()
            if self.mus_chan_u: self.mus_chan_u.set_volume(0)

        # Start game with NO MALUS
        self.malus_manager.new_round(malus="NO_MALUS")
    
    def get_slice(self, sound, pct):
        try:
            arr = pygame.sndarray.array(sound)
            idx = int(pct * len(arr))
            # Ensure idx is within bounds and aligned for stereo if needed (pygame handles shape)
            if idx >= len(arr): idx = 0
            return pygame.sndarray.make_sound(arr[idx:])
        except: return None

    def switch_music_speed(self, fast):
        self.is_fast = fast
        vol_n = self.mus_chan_n.get_volume() if self.mus_chan_n else settings.MUSIC_VOLUME
        vol_u = self.mus_chan_u.get_volume() if self.mus_chan_u else 0.0
        
        # Calculate current position percentage
        pct = 0.0
        if self.mus_chan_n and self.music_normal:
             # get_pos returns ms since play start. Assuming loops=-1, it increases indefinitely?
             # actually get_pos returns time since START of playback, wrapping depends on impl.
             # but usually for infinite loop it just counts up. 
             # safeset is modulus length.
             pos_ms = pygame.time.get_ticks() - self.music_start_time
             if pos_ms < 0: pos_ms = 0
             
             # Current track length in ms
             curr_track = self.music_normal_fast if (not fast and self.is_fast) else (self.music_normal if not self.is_fast else self.music_normal_fast)
             # Wait, self.is_fast is already set to new value.
             # previous state was not fast.
             
             # If we were slow: length is normal length.
             # If we were fast: length is fast length.
             
             prev_fast = not fast
             base_len = self.music_normal_fast.get_length() if prev_fast else self.music_normal.get_length()
             if base_len > 0:
                 pct = (pos_ms / 1000.0) % base_len / base_len

        
        if self.mus_chan_n: self.mus_chan_n.stop()
        if self.mus_chan_u: self.mus_chan_u.stop()
        
        target_n = self.music_normal_fast if fast else self.music_normal
        target_u = self.music_upside_fast if fast else self.music_upside
        
        if target_n and target_u:
            # Create slices starting from pct
            slice_n = self.get_slice(target_n, pct)
            slice_u = self.get_slice(target_u, pct)
            
            if slice_n and slice_u:
                self.mus_chan_n = slice_n.play()
                self.mus_chan_u = slice_u.play()
                
                # Queue the full loop
                self.mus_chan_n.queue(target_n)
                self.mus_chan_u.queue(target_u)
                
                # Flag to maintain loop in update
                self.current_n_loop = target_n
                self.current_u_loop = target_u
                
                # Update start time for next sync
                new_len = target_n.get_length()
                if new_len > 0:
                     new_pos_ms = pct * new_len * 1000.0
                     self.music_start_time = pygame.time.get_ticks() - new_pos_ms
            else:
                # Fallback
                self.mus_chan_n = target_n.play(loops=-1)
                self.mus_chan_u = target_u.play(loops=-1)
                self.current_n_loop = None
                self.current_u_loop = None
                self.music_start_time = pygame.time.get_ticks()

            if self.mus_chan_n: self.mus_chan_n.set_volume(vol_n)
            if self.mus_chan_u: self.mus_chan_u.set_volume(vol_u)

    def handle(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT: self.running = False
            
            if self.state == 'DYING': continue
            
            if e.type == pygame.KEYDOWN and self.state == 'GAME_OVER' and e.key == pygame.K_SPACE:
                self.state = 'MENU'
                pygame.mixer.stop()
                continue
                
            if e.type == pygame.KEYDOWN:
                self.cheat_buf = (self.cheat_buf + e.unicode).upper()[-10:]
                if "PIZZA" in self.cheat_buf: self.pizzas_made, self.round_p, self.cheat_buf = self.pizzas_made + 15, self.round_p + 15, ""
                if "INV" in self.cheat_buf: 
                    for k in self.player.inventory.counts: self.player.inventory.counts[k] = self.player.inventory.cap
                    self.cheat_buf = ""
                if "SKIP" in self.cheat_buf: 
                    self.round_p, self.wave_timer, self.cheat_buf = self.pizza_goal, 0, ""
                    pygame.mixer.stop()
                if "OVER" in self.cheat_buf: 
                    self.state, self.cheat_buf = 'GAME_OVER', ""
                    pygame.mixer.stop()
                if "KILL" in self.cheat_buf: self.player.health, self.cheat_buf = 0, ""
                if "HEAL" in self.cheat_buf: self.player.health, self.cheat_buf = self.player.max_health, ""
            if self.state == 'MENU':
                res = self.menu.handle_events(e)
                if res == "START": self.start()
                elif res == "QUIT": self.running = False
            elif self.state == 'PLAYING':
                if self.recipe_menu.is_open:
                    p = self.recipe_menu.handle_input(e, self.player, self.om)
                    if p and p > 0: 
                        self.score, self.pizzas_made = self.score + p, self.pizzas_made + 1
                        self.round_p += 1
                elif e.type == pygame.KEYDOWN and (e.key == pygame.K_e or e.key == pygame.K_SPACE):
                    if self.world.oven.active: self.recipe_menu.toggle()
                    else: self.world.trigger_weapon(self.player)
            elif self.state == 'SHOP': self.shop_menu.handle_input(e, self)

    def update(self, dt):
        # Music Sync
        if self.state not in ['MENU', 'GAME_OVER'] and self.world and self.mus_chan_n and self.mus_chan_u:
            # Check loop queue maintenance
            if hasattr(self, 'current_n_loop') and self.current_n_loop:
                if not self.mus_chan_n.get_queue():
                     # Only queue if channel is busy (playing)
                     if self.mus_chan_n.get_busy(): self.mus_chan_n.queue(self.current_n_loop)
                if not self.mus_chan_u.get_queue():
                     if self.mus_chan_u.get_busy(): self.mus_chan_u.queue(self.current_u_loop)

            # dim 1 = normal, dim 0 = alien
            target_n = settings.MUSIC_VOLUME if self.world.dim == 1 else 0.0
            target_u = settings.MUSIC_VOLUME if self.world.dim == 0 else 0.0
            self.mus_chan_n.set_volume(target_n)
            self.mus_chan_u.set_volume(target_u)

        if self.state == 'MENU': self.menu.update(dt)
        elif self.state == 'GAME_OVER': pass
        elif self.state == 'DYING':
            self.death_timer += dt
            self.camera.update(self.player.rect, dt) # keep cam aimed
            if self.death_timer > settings.DEATH_ANIMATION_DURATION:
                 self.player.add_tomb(self.world.dim)
                 self.player.respawn(settings.MAP_WIDTH//2+settings.PLAYER_SIZE, settings.MAP_HEIGHT//2-settings.PLAYER_SIZE//2)
                 self.world.dim = 1
                 self.wave_timer -= settings.DEATH_PENALTY_TIME
                 self.pizzas_made //= settings.DEATH_PIZZA_PENALTY_DIVISOR
                 self.state = 'PLAYING'
        elif self.state == 'PLAYING':
            # Speed check
            if self.wave_timer > 0:
                if self.wave_timer <= settings.MUSIC_SPEEDUP_TIME and not self.is_fast:
                    self.switch_music_speed(True)
                elif self.wave_timer > settings.MUSIC_SPEEDUP_TIME and self.is_fast:
                    self.switch_music_speed(False)

            if not self.recipe_menu.is_open: self.player.handle_input(dt)
            if self.player.health <= 0:
                self.player.on_death()
                self.state = 'DYING'
                self.death_timer = 0
                return # Skip rest of update
            
            if self.world.update(self.player, dt): self.f_a = 255
            
            if self.player.needs_shake:
                self.camera.start_shake(10, 0.3)
                self.player.needs_shake = False

            self.f_a, self.wave_timer = max(0, self.f_a - 1000 * dt), self.wave_timer - dt
            self.camera.update(self.player.rect, dt)
            self.recipe_menu.update(dt)
            self.score += self.om.update(dt)
            self.bonus_manager.update(dt, self.player)
            if self.recipe_menu.is_open and not self.world.oven.active: self.recipe_menu.toggle()
            if self.wave_timer <= 0:
                if self.round_p >= self.pizza_goal:
                    self.state, self.wave_timer, self.recipe_menu.is_open = 'SHOP', settings.SHOP_DURATION, False
                    self.recipe_menu.target = self.recipe_menu.cpos
                    self.om.reset_orders(); self.shop_menu.refresh_active()
                    
                    # Reset music to slow/stop
                    if self.mus_chan_n: self.mus_chan_n.stop()
                    if self.mus_chan_u: self.mus_chan_u.stop()
                    
                else:
                    self.state = 'GAME_OVER'
                    pygame.mixer.stop()

        elif self.state == 'SHOP':
            if self.wave_timer <= 0:
                self.state = 'ROULETTE'
                
                # Helpers for weapon icons/names
                class WeaponOpt:
                    def __init__(self, name, id, icon_path):
                        self.name = name
                        self.full_id = id
                        try: self.icon = pygame.transform.scale(pygame.image.load(icon_path).convert_alpha(), (128, 128))
                        except: self.icon = None
                w_opts = [
                    WeaponOpt("Bongo", "drum_weapon", "assets/bongo.png"),
                    WeaponOpt("Flûte de Pan", "pan_weapon", "assets/flute_of_pan.png"),
                    WeaponOpt("Saxophone", "sax_weapon", "assets/saxo.png")
                ]
                
                # Filter previous weapon
                avail_w = [w for w in w_opts if w.full_id != self.last_weapon]
                if not avail_w: avail_w = w_opts

                # Filter previous malus
                avail_m = [m for m in self.malus_manager.maluses if m != self.malus_manager.current_malus]
                if not avail_m: avail_m = self.malus_manager.maluses

                # Launch Roulette
                self.roulette_menu.start(avail_m, avail_w, self.bonus_manager.bonuses)

        elif self.state == 'ROULETTE':
             if self.roulette_menu.update(dt):
                 # Roulette finished
                 self.state, self.wave_timer, self.wave_num = 'PLAYING', settings.WAVE_DURATION, self.wave_num + 1
                 
                 # Pizza Goal / Scaling
                 if self.pizza_goal < 10:
                      self.pizza_goal += settings.PIZZA_GOAL_INCREMENT
                      if self.pizza_goal > 10: self.pizza_goal = 10
                 else:
                      self.extra_enemies += 1
                      
                 self.round_p = 0
                 
                 self.world.dim = 1
                 self.player.respawn(settings.MAP_WIDTH//2+settings.PLAYER_SIZE, settings.MAP_HEIGHT//2-settings.PLAYER_SIZE//2)
                 
                 # Set Weapon
                 sel_weap = self.roulette_menu.selected_weapon
                 if sel_weap:
                     self.player.weapon = sel_weap.full_id
                     self.last_weapon = self.player.weapon
                 
                 self.world.spawn(extra=self.extra_enemies)
                 self.world.enemy_manager.projectiles.clear()
                 self.world.res_manager.drops.clear()
                 
                 # Apply Malus
                 self.malus_manager.new_round(self.roulette_menu.selected_malus)
                 
                 # Apply Bonus
                 self.bonus_manager.new_round(self.roulette_menu.selected_bonus)
                 
                 # Restart music slow
                 self.switch_music_speed(False)


    def draw(self):
        if self.state == 'MENU': self.menu.draw()
        elif self.state == 'GAME_OVER':
            self.screen.fill((50, 0, 0))
            t1 = self.font.render("GAME OVER", True, (255, 255, 255))
            t2 = self.font.render(f"SCORE: {self.score}", True, (255, 215, 0))
            t3 = self.font.render("PRESS SPACE TO RETURN TO MENU", True, (200, 200, 200))
            w, h = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
            self.screen.blit(t1, (w//2 - t1.get_width()//2, h//2 - 100))
            self.screen.blit(t2, (w//2 - t2.get_width()//2, h//2))
            self.screen.blit(t3, (w//2 - t3.get_width()//2, h//2 + 100))
        else:
            self.world.draw(self.screen, self.camera.offset_x, self.camera.offset_y)
            if self.state == 'DYING':
                self.player.draw_death(self.screen, self.camera.offset_x, self.camera.offset_y, self.death_timer, self.world.dim)
                self.ui.draw_penalty_anim(self.screen, self.death_timer, self.wave_num, max(0, self.wave_timer))
            else:
                self.player.draw(self.screen, self.camera.offset_x, self.camera.offset_y, self.world.dim)
                self.bonus_manager.draw(self.screen, self.camera.offset_x, self.camera.offset_y)
            if self.f_a > 0: self.f_s.set_alpha(int(self.f_a)); self.screen.blit(self.f_s, (0, 0))
            score_txt = self.font.render(f"SCORE : {self.score}", True, (255,255,255))
            self.screen.blit(score_txt, (settings.SCREEN_WIDTH//2 - score_txt.get_width()//2, 20))
            
            if self.state != 'DYING':
                self.ui.draw(self.screen, self.player.inventory, self.pizzas_made, self.wave_num, max(0, self.wave_timer), self.player.health, self.player.max_health, self.player.weapon, self.round_p, self.pizza_goal, self.malus_manager.current_malus)
            
            if self.state != 'SHOP': self.recipe_menu.draw(self.screen, self.player.inventory, self.om)
            if self.world.dim == self.world.oven.dim: self.ui.draw_arrow(self.screen, self.player.rect, self.world.oven.rect)
            if self.state == 'SHOP': self.shop_menu.draw(self.screen, self)
            if self.state == 'ROULETTE': self.roulette_menu.draw(self.screen)
        pygame.display.flip()
    def run(self):
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            self.handle(); self.update(dt); self.draw()
        if self.mus_chan_n: self.mus_chan_n.stop()
        if self.mus_chan_u: self.mus_chan_u.stop()
        pygame.quit(); sys.exit()