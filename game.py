import pygame, sys, settings, random, math, json
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
        self.last_bonus = None
        self.death_timer = 0
        self.roulette_menu = None
        self.game_over_timer = 0
        self.input_active = False
        self.input_name = ""
        self.input_focus = 0 # 0: Text, 1: Button
        self.cheated = False
        
        try: self.death_screen_img = pygame.transform.scale(pygame.image.load("assets/death_screen.png").convert(), (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        except: self.death_screen_img = None
        
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

        try:
            self.music_drug = pygame.mixer.Sound("assets/super_power.mp3")
        except:
            self.music_drug = None
            
        self.mus_chan_n = None
        self.mus_chan_u = None
        self.mus_chan_drug = None
        self.is_fast = False
        self.music_start_time = 0
        self.tutorial_stage = 0

    def start(self, sandbox=False):
        self.sandbox = sandbox
        self.tutorial_stage = 0
        pygame.mixer.stop()
        self.map, self.pizzas_made = Map(), 0
        self.om = OrderManager()
        self.player = Player(settings.MAP_WIDTH//2+settings.PLAYER_SIZE, settings.MAP_HEIGHT//2-settings.PLAYER_SIZE//2, self.map)
        
        # Force weapon to Bomgo (drum) for first round
        self.player.weapon = "drum_weapon"
        self.last_weapon = self.player.weapon
        self.last_bonus = None
        self.cheated = False
        
        self.world = WorldManager(self.map)
        self.malus_manager = MalusManager(self.world)
        self.bonus_manager = BonusManager(self.world)
        self.camera = Camera(settings.MAP_WIDTH, settings.MAP_HEIGHT)
        self.ui, self.recipe_menu, self.shop_menu, self.roulette_menu = UI(self.font), RecipeMenu(self.font), ShopMenu(self.font), RouletteMenu(self.font)
        self.ui.game_ptr = self
        self.score, self.f_a, self.wave_timer, self.wave_num, self.state = 0, 0, settings.WAVE_DURATION, 1, 'PLAYING'
        self.pizza_goal, self.round_p = settings.INITIAL_PIZZA_GOAL, 0
        self.extra_enemies = 0
        
        self.is_fast = False
        if self.music_normal and self.music_upside:
            self.start_music()

        self.malus_manager.new_round(malus="NO_MALUS")

    def start_tutorial(self):
        self.stop_music()
        self.map, self.pizzas_made = Map(), 0
        self.om = OrderManager()
        self.player = Player(settings.MAP_WIDTH//2+settings.PLAYER_SIZE, settings.MAP_HEIGHT//2-settings.PLAYER_SIZE//2, self.map)
        
        self.player.weapon = "drum_weapon"
        self.last_weapon = "drum_weapon"
        self.last_bonus = None
        self.cheated = False
        
        self.world = WorldManager(self.map)
        self.world.spawn(tutorial_stage=1)
        self.malus_manager = MalusManager(self.world)
        self.bonus_manager = BonusManager(self.world)
        
        self.camera = Camera(settings.MAP_WIDTH, settings.MAP_HEIGHT)
        self.ui, self.recipe_menu, self.shop_menu, self.roulette_menu = UI(self.font), RecipeMenu(self.font), ShopMenu(self.font), RouletteMenu(self.font)
        self.ui.game_ptr = self
        
        self.score, self.f_a, self.wave_timer, self.wave_num = 0, 0, 999999, 1
        self.state = 'TUTORIAL'
        self.tutorial_stage = 1
        self.tutorial_text_idx = 0
        self.pizza_goal, self.round_p = 0, 0
        self.sandbox = False
        
        self.malus_manager.new_round(malus="NO_MALUS")
        
        # if self.music_normal and self.music_upside:
        #     self.start_music()
    
    def get_slice(self, sound, pct):
        try:
            arr = pygame.sndarray.array(sound)
            idx = int(pct * len(arr))
            if idx >= len(arr): idx = 0
            return pygame.sndarray.make_sound(arr[idx:])
        except: return None

    def stop_music(self):
        if self.mus_chan_n:
            self.mus_chan_n.stop()
            self.mus_chan_n = None
        if self.mus_chan_u:
            self.mus_chan_u.stop()
            self.mus_chan_u = None
        if self.mus_chan_drug:
            self.mus_chan_drug.stop()
            self.mus_chan_drug = None
            
        self.current_n_loop = None
        self.current_u_loop = None

    def reset_bonus_effects(self):
        if self.bonus_manager: self.bonus_manager.pill_effect_timer = 0
        if self.player: self.player.speed_multiplier = 1.0
        if self.world: self.world.cd_limit_multiplier = 1.0

    def start_music(self, fast=False):
        self.stop_music()
        self.is_fast = fast
        
        target_n = self.music_normal_fast if fast else self.music_normal
        target_u = self.music_upside_fast if fast else self.music_upside

        if target_n and target_u:
            self.mus_chan_n = target_n.play(loops=-1)
            self.mus_chan_u = target_u.play(loops=-1)
            self.music_start_time = pygame.time.get_ticks()
            
            vol_n = settings.MUSIC_VOLUME if self.world and self.world.dim == 1 else 0.0
            vol_u = settings.MUSIC_VOLUME if self.world and self.world.dim == 0 else 0.0
            
            if self.mus_chan_n: self.mus_chan_n.set_volume(vol_n)
            if self.mus_chan_u: self.mus_chan_u.set_volume(vol_u)

    def switch_music_speed(self, fast):
        self.is_fast = fast
        vol_n = self.mus_chan_n.get_volume() if self.mus_chan_n else settings.MUSIC_VOLUME
        vol_u = self.mus_chan_u.get_volume() if self.mus_chan_u else 0.0
        
        pct = 0.0
        if self.mus_chan_n and self.music_normal:
             pos_ms = pygame.time.get_ticks() - self.music_start_time
             if pos_ms < 0: pos_ms = 0
             
             prev_fast = not fast
             base_len = self.music_normal_fast.get_length() if prev_fast else self.music_normal.get_length()
             if base_len > 0:
                 pct = (pos_ms / 1000.0) % base_len / base_len
        
        self.stop_music()
        
        target_n = self.music_normal_fast if fast else self.music_normal
        target_u = self.music_upside_fast if fast else self.music_upside
        
        if target_n and target_u:
            slice_n = self.get_slice(target_n, pct)
            slice_u = self.get_slice(target_u, pct)
            
            if slice_n and slice_u:
                self.mus_chan_n = slice_n.play()
                self.mus_chan_u = slice_u.play()
                
                self.mus_chan_n.queue(target_n)
                self.mus_chan_u.queue(target_u)
                
                self.current_n_loop = target_n
                self.current_u_loop = target_u
                
                new_len = target_n.get_length()
                if new_len > 0:
                     new_pos_ms = pct * new_len * 1000.0
                     self.music_start_time = pygame.time.get_ticks() - new_pos_ms
            else:
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
            
            if self.state == 'GAME_OVER':
                if e.type == pygame.KEYDOWN:
                    if not self.input_active:
                         # Wait for initial press
                         if self.game_over_timer > 2.0 and e.key in settings.KEYS_VALIDATE:
                             if not self.cheated and not self.sandbox:
                                 self.input_active = True
                                 self.input_name = ""
                                 self.input_focus = 0
                             else:
                                 self.state = 'MENU'
                                 self.game_over_timer = 0
                                 pygame.mixer.stop()
                    else:
                         # Input Dialog Logic
                         if e.key in settings.KEYS_DOWN: self.input_focus = 1
                         elif e.key in settings.KEYS_UP: self.input_focus = 0
                         
                         elif e.key in settings.KEYS_VALIDATE and self.input_focus == 1:
                              # Validated
                              try:
                                  try: 
                                      with open("score.json", "r") as f: scores = json.load(f)
                                  except: scores = []
                                  
                                  scores.append({"name": self.input_name if self.input_name.strip() else "Anonymous", "score": self.score, "wave": self.wave_num - 1})
                                  scores.sort(key=lambda x: x["score"], reverse=True)
                                  
                                  with open("score.json", "w") as f: json.dump(scores, f, indent=4)
                              except Exception as err: print(f"Score Save Error: {err}")
                              
                              self.state = 'MENU'
                              self.game_over_timer = 0
                              self.input_active = False # Reset
                              pygame.mixer.stop()
                              
                         elif self.input_focus == 0:
                              if e.key == pygame.K_BACKSPACE:
                                  self.input_name = self.input_name[:-1]
                              else:
                                  if len(self.input_name) < 12 and e.unicode.isprintable():
                                      self.input_name += e.unicode
                continue
                
            if e.type == pygame.KEYDOWN:
                self.cheat_buf = (self.cheat_buf + e.unicode).upper()[-10:]
                if "PIZZA" in self.cheat_buf: self.pizzas_made, self.round_p, self.cheat_buf, self.cheated = self.pizzas_made + 15, self.round_p + 15, "", True
                if "INV" in self.cheat_buf: 
                    for k in self.player.inventory.counts: self.player.inventory.counts[k] = self.player.inventory.cap
                    self.cheat_buf, self.cheated = "", True
                if "SKIP" in self.cheat_buf: 
                    self.round_p, self.wave_timer, self.cheat_buf, self.cheated = self.pizza_goal, 0, "", True
                    self.reset_bonus_effects()
                    pygame.mixer.stop()
                    self.stop_music()
                    self.is_fast = True
                if "OVER" in self.cheat_buf: 
                    self.state, self.cheat_buf, self.cheated = 'GAME_OVER', "", True
                    self.game_over_timer = 0
                    pygame.mixer.stop()
                if "KILL" in self.cheat_buf: self.player.health, self.cheat_buf, self.cheated = 0, "", True
                if "HEAL" in self.cheat_buf: self.player.health, self.cheat_buf, self.cheated = self.player.max_health, "", True
            if self.state == 'MENU':
                res = self.menu.handle_events(e)
                if res == "START": self.start(sandbox=False)
                elif res == "SANDBOX": self.start(sandbox=True)
                elif res == "TUTO": self.start_tutorial()
                elif res == "QUIT": self.running = False
            elif self.state == 'PLAYING':
                if self.recipe_menu.is_open:
                    p = self.recipe_menu.handle_input(e, self.player, self.om)
                    if p and p > 0: 
                        self.score, self.pizzas_made = self.score + p, self.pizzas_made + 1
                        self.round_p += 1
                elif e.type == pygame.KEYDOWN and e.key in settings.KEYS_INTERACT:
                    if self.world.oven.active: self.recipe_menu.toggle()
                    else: self.world.trigger_weapon(self.player)
            elif self.state == 'SHOP': self.shop_menu.handle_input(e, self)
            elif self.state == 'ROULETTE': self.roulette_menu.handle_input(e)
            elif self.state == 'TUTORIAL':
                if self.recipe_menu.is_open:
                    p = self.recipe_menu.handle_input(e, self.player, self.om)
                    if p and p > 0:
                        self.pizzas_made += 1
                elif e.type == pygame.KEYDOWN and e.key in settings.KEYS_INTERACT:
                    self.tutorial_text_idx = (self.tutorial_text_idx + 1) % 2
                    if self.world.oven.active: self.recipe_menu.toggle()
                    else: self.world.trigger_weapon(self.player)

    def update(self, dt):
        if self.state not in ['MENU', 'GAME_OVER'] and self.world and self.mus_chan_n and self.mus_chan_u:
            if hasattr(self, 'current_n_loop') and self.current_n_loop:
                if not self.mus_chan_n.get_queue():
                     if self.mus_chan_n.get_busy(): self.mus_chan_n.queue(self.current_n_loop)
                if not self.mus_chan_u.get_queue():
                     if self.mus_chan_u.get_busy(): self.mus_chan_u.queue(self.current_u_loop)

            target_n = settings.MUSIC_VOLUME if self.world.dim == 1 else 0.0
            target_u = settings.MUSIC_VOLUME if self.world.dim == 0 else 0.0
            self.mus_chan_n.set_volume(target_n)
            self.mus_chan_u.set_volume(target_u)

        if self.state == 'MENU': self.menu.update(dt)
        elif self.state == 'GAME_OVER': self.game_over_timer += dt
        elif self.state == 'DYING':
            self.death_timer += dt
            self.camera.update(self.player.rect, dt)
            if self.death_timer > settings.DEATH_ANIMATION_DURATION:
                 self.player.add_tomb(self.world.dim)
                 self.player.respawn(settings.MAP_WIDTH//2+settings.PLAYER_SIZE, settings.MAP_HEIGHT//2-settings.PLAYER_SIZE//2)
                 self.world.dim = 1
                 self.wave_timer -= settings.DEATH_PENALTY_TIME
                 self.pizzas_made //= settings.DEATH_PIZZA_PENALTY_DIVISOR
                 self.pizzas_made //= settings.DEATH_PIZZA_PENALTY_DIVISOR
                 self.pizzas_made //= settings.DEATH_PIZZA_PENALTY_DIVISOR
                 self.state = 'TUTORIAL' if self.tutorial_stage > 0 else 'PLAYING'
                 
                 # Fix Music Glitch (Double Playing)
                 pygame.mixer.stop()
                 self.stop_music()
                 # Recalculate if we should be fast
                 should_be_fast = (self.wave_timer <= settings.MUSIC_SPEEDUP_TIME)
                 if self.music_normal and self.music_upside:
                     self.start_music(fast=should_be_fast)
        elif self.state == 'PLAYING':
            # Drug Effect Logic
            if self.bonus_manager.pill_effect_timer > 0:
                self.player.speed_multiplier = settings.PILL_SPEED_MULTI
                self.world.cd_limit_multiplier = 1.0 / settings.PILL_ATTACK_SPEED_MULTI
                
                # Start Drug Music if not playing
                if not self.mus_chan_drug and self.music_drug:
                    if self.mus_chan_n: self.mus_chan_n.pause()
                    if self.mus_chan_u: self.mus_chan_u.pause()
                    self.mus_chan_drug = self.music_drug.play(loops=-1)
            else:
                self.player.speed_multiplier = 1.0
                self.world.cd_limit_multiplier = 1.0
                
                # Stop Drug Music if playing
                if self.mus_chan_drug:
                    self.mus_chan_drug.stop()
                    self.mus_chan_drug = None
                    if self.mus_chan_n: self.mus_chan_n.unpause()
                    if self.mus_chan_u: self.mus_chan_u.unpause()

                # Normal Speed Switch Logic
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
                pygame.mixer.stop()
                self.stop_music() # Clear references
                return
            
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
                if self.round_p >= self.pizza_goal or self.sandbox:
                    self.state, self.wave_timer, self.recipe_menu.is_open = 'SHOP', settings.SHOP_DURATION, False
                    self.recipe_menu.target = self.recipe_menu.cpos
                    self.om.reset_orders(); self.shop_menu.refresh_active()
                    
                    self.reset_bonus_effects()
                    pygame.mixer.stop()
                    self.stop_music()
                    
                else:
                    self.state = 'GAME_OVER'
                    self.reset_bonus_effects()
                    pygame.mixer.stop()
                    self.stop_music()

        elif self.state == 'TUTORIAL':
             if not self.recipe_menu.is_open: self.player.handle_input(dt)
             
             if self.player.health <= 0:
                self.player.on_death()
                self.state = 'DYING'
                self.death_timer = 0
                return

             if self.world.update(self.player, dt): self.f_a = 255
             
             if self.player.needs_shake:
                self.camera.start_shake(10, 0.3)
                self.player.needs_shake = False

             self.f_a = max(0, self.f_a - 1000 * dt)
             self.camera.update(self.player.rect, dt)
             self.recipe_menu.update(dt)
             self.om.update(dt, tutorial_mode=True)
             self.bonus_manager.update(dt, self.player)

             if self.recipe_menu.is_open and not self.world.oven.active: self.recipe_menu.toggle()
             
             if self.tutorial_stage == 1:
                 cheese = self.player.inventory.counts.get("cheese", 0)
                 dough = self.player.inventory.counts.get("dough", 0)
                 if cheese >= 1 and dough >= 1:
                     self.tutorial_stage = 2
                     self.tutorial_text_idx = 0
                     self.player.inventory.counts = {"cheese": 0, "tomato": 0, "dough": 0}
                     self.om.setup_tutorial_order()

             if self.tutorial_stage == 2:
                 # Check if pizza made (pizze_made increments in handle via handle_input for recipe_menu)
                 if self.pizzas_made >= 1:
                     self.tutorial_stage = 3
                     self.tutorial_text_idx = 0
                     self.player.inventory.counts = {"cheese": 0, "tomato": 0, "dough": 0}
                     self.player.weapon = "sax_weapon"
                     self.last_weapon = "sax_weapon"
                     self.world.spawn(tutorial_stage=3)
                     self.om.setup_tutorial_order(recipe_index=2) # Pizza Tomate

             if self.tutorial_stage == 3:
                if self.pizzas_made >= 2:
                     self.tutorial_stage = 4
                     self.tutorial_text_idx = 0
                     self.player.inventory.counts = {"cheese": 0, "tomato": 0, "dough": 0}
                     self.player.weapon = "pan_weapon"
                     self.last_weapon = "pan_weapon"
                     self.world.spawn(tutorial_stage=4)
                     self.om.setup_tutorial_order(recipe_index=0) # Pizza Margherita

             if self.tutorial_stage == 4:
                if self.pizzas_made >= 3:
                     self.tutorial_stage = 5
                     self.tutorial_text_idx = 0
                     self.player.inventory.counts = {"cheese": 0, "tomato": 0, "dough": 0}
                     self.world.spawn(tutorial_stage=5)
                     self.om.setup_tutorial_order(recipe_index=3, count=3) # Pizza Double Fromage

             if self.tutorial_stage == 5:
                if self.pizzas_made >= 6:
                     self.state = 'MENU'
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

                # Filter previous bonus
                avail_b = [b for b in self.bonus_manager.bonuses if b != self.last_bonus]
                if not avail_b: avail_b = self.bonus_manager.bonuses

                # Launch Roulette
                if self.sandbox:
                     self.roulette_menu.start_sandbox(self.malus_manager.maluses, w_opts, self.bonus_manager.bonuses)
                else:
                     self.roulette_menu.start(avail_m, avail_w, avail_b)

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
                 self.last_bonus = self.roulette_menu.selected_bonus
                 
                 # Restart music slow
                 self.start_music()


    def draw(self):
        if self.state == 'MENU': self.menu.draw()
        elif self.state == 'GAME_OVER':
            if self.death_screen_img:
                self.screen.blit(self.death_screen_img, (0, 0))
            else:
                self.screen.fill((50, 0, 0))
            
            w, h = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
            
            # Left-align all GAME OVER content
            center_x = w // 2 - 200 # Shift left
            
            # Game Over Title (Higher, Black Container)
            t1 = self.menu.title_font.render("GAME OVER", True, (255, 50, 50))
            title_rect = t1.get_rect(center=(center_x, h//2 - 200))
            
            # Title Background
            bg_rect = title_rect.inflate(60, 20)
            bs = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(bs, (0, 0, 0, 200), (0, 0, bg_rect.w, bg_rect.h), border_radius=15)
            self.screen.blit(bs, bg_rect.topleft)
            self.screen.blit(t1, title_rect)
            
            # Stats centered on the new axis
            # Score
            t_score = self.menu.title_font.render(f"SCORE: {self.score}", True, (255, 215, 0))
            self.screen.blit(t_score, (center_x - t_score.get_width()//2, h//2 - 80))

            # Waves & Pizzas
            stats_font = self.ui.large_font
            t_wave = stats_font.render(f"Vagues Survecues: {self.wave_num - 1}", True, (200, 200, 255))
            t_pizza = stats_font.render(f"Pizzas Fabriquees: {self.pizzas_made}", True, (255, 255, 255))
            
            self.screen.blit(t_wave, (center_x - t_wave.get_width()//2, h//2))
            self.screen.blit(t_pizza, (center_x - t_pizza.get_width()//2, h//2 + 50))

            # Input Dialog / Press Space
            if self.input_active:
                # Dialog Box
                d_w, d_h = 500, 300
                d_rect = pygame.Rect((w - d_w)//2, (h - d_h)//2, d_w, d_h)
                
                # Background
                if self.ui.bg_panel:
                    self.screen.blit(pygame.transform.scale(self.ui.bg_panel, (d_w, d_h)), d_rect)
                else:
                    pygame.draw.rect(self.screen, (30, 35, 50), d_rect, border_radius=15)
                    pygame.draw.rect(self.screen, (100, 110, 140), d_rect, 3, border_radius=15)
                
                # Title
                t_lbl = self.font.render("Entrez votre pseudo", True, (255, 255, 255))
                self.screen.blit(t_lbl, (d_rect.centerx - t_lbl.get_width()//2, d_rect.y + 40))
                
                # Input Field
                i_w, i_h = 300, 50
                i_rect = pygame.Rect((w - i_w)//2, d_rect.y + 110, i_w, i_h)
                col_i = (255, 215, 0) if self.input_focus == 0 else (100, 100, 100)
                pygame.draw.rect(self.screen, (20, 20, 30), i_rect, border_radius=8)
                pygame.draw.rect(self.screen, col_i, i_rect, 3, border_radius=8)
                
                t_name = self.font.render(self.input_name, True, (255, 255, 255))
                self.screen.blit(t_name, (i_rect.centerx - t_name.get_width()//2, i_rect.centery - t_name.get_height()//2))
                
                # Validate Button
                b_w, b_h = 160, 50
                b_rect = pygame.Rect((w - b_w)//2, d_rect.y + 200, b_w, b_h)
                col_b = (255, 215, 0) if self.input_focus == 1 else (60, 60, 60)
                pygame.draw.rect(self.screen, col_b, b_rect, border_radius=8)
                
                t_val = self.font.render("VALIDER", True, (0, 0, 0) if self.input_focus == 1 else (200, 200, 200))
                self.screen.blit(t_val, (b_rect.centerx - t_val.get_width()//2, b_rect.centery - t_val.get_height()//2))
                
            elif self.game_over_timer > 2.0:
                # Pulse alpha
                alpha = int(127 + 127 * math.sin(pygame.time.get_ticks() * 0.005))
                t2 = self.font.render(settings.TEXT_RETURN_MENU, True, (200, 200, 200))
                s2 = pygame.Surface(t2.get_size(), pygame.SRCALPHA)
                s2.blit(t2, (0,0))
                s2.set_alpha(alpha)
                self.screen.blit(s2, (center_x - t2.get_width()//2, h//2 + 150))
        else:
            self.world.draw(self.screen, self.camera.offset_x, self.camera.offset_y)
            if self.state == 'DYING':
                self.player.draw_death(self.screen, self.camera.offset_x, self.camera.offset_y, self.death_timer, self.world.dim)
                self.ui.draw_penalty_anim(self.screen, self.death_timer, self.wave_num, max(0, self.wave_timer))
            else:
                self.player.draw(self.screen, self.camera.offset_x, self.camera.offset_y, self.world.dim)
                self.bonus_manager.draw(self.screen, self.camera.offset_x, self.camera.offset_y, self.player)
            if self.f_a > 0: self.f_s.set_alpha(int(self.f_a)); self.screen.blit(self.f_s, (0, 0))
            
            if self.state != 'DYING':
                self.ui.draw(self.screen, self.player.inventory, self.score, self.wave_num, max(0, self.wave_timer), self.player.health, self.player.max_health, self.player.weapon, self.round_p, self.pizza_goal, self.malus_manager.current_malus, is_tutorial=(self.state == 'TUTORIAL'))
            
            if self.state != 'SHOP': self.recipe_menu.draw(self.screen, self.player.inventory, self.om)
            if self.world.dim == self.world.oven.dim: self.ui.draw_arrow(self.screen, self.player.rect, self.world.oven.rect)
            if self.state == 'SHOP': self.shop_menu.draw(self.screen, self)
            if self.state == 'ROULETTE': self.roulette_menu.draw(self.screen)
            
            if self.state == 'TUTORIAL':
                msgs = settings.TUTORIAL_TEXTS.get(self.tutorial_stage, ["", ""])
                txt = msgs[self.tutorial_text_idx] if self.tutorial_text_idx < len(msgs) else msgs[0]
                self.ui.draw_tutorial_panel(self.screen, txt, self.tutorial_text_idx, len(msgs))

        pygame.display.flip()
    def run(self):
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            self.handle(); self.update(dt); self.draw()
        if self.mus_chan_n: self.mus_chan_n.stop()
        if self.mus_chan_u: self.mus_chan_u.stop()
        pygame.quit(); sys.exit()