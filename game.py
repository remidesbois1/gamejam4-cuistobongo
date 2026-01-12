import pygame, sys, settings, random
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

    def start(self):
        self.map, self.pizzas_made = Map(), 0
        self.player = Player(settings.MAP_WIDTH//2+settings.PLAYER_SIZE, settings.MAP_HEIGHT//2-settings.PLAYER_SIZE//2, self.map)
        
        # Force weapon to Bomgo (drum) for first round
        self.player.weapon = "drum_weapon"
        self.last_weapon = self.player.weapon
        
        self.world = WorldManager(self.map)
        self.malus_manager = MalusManager(self.world)
        self.camera = Camera(settings.MAP_WIDTH, settings.MAP_HEIGHT)
        self.ui, self.recipe_menu, self.shop_menu, self.roulette_menu = UI(self.font), RecipeMenu(self.font), ShopMenu(self.font), RouletteMenu(self.font)
        self.score, self.f_a, self.wave_timer, self.wave_num, self.state = 0, 0, settings.WAVE_DURATION, 1, 'PLAYING'
        self.pizza_goal, self.round_p = settings.INITIAL_PIZZA_GOAL, 0
        
        # Start game with NO MALUS
        self.malus_manager.new_round(malus="NO_MALUS")

    def handle(self):
        if self.state == 'DYING': return
        for e in pygame.event.get():
            if e.type == pygame.QUIT: self.running = False
            if e.type == pygame.KEYDOWN and self.state == 'GAME_OVER' and e.key == pygame.K_SPACE:
                self.state = 'MENU'
                continue
            if e.type == pygame.KEYDOWN:
                self.cheat_buf = (self.cheat_buf + e.unicode).upper()[-10:]
                if "PIZZA" in self.cheat_buf: self.pizzas_made, self.round_p, self.cheat_buf = self.pizzas_made + 15, self.round_p + 15, ""
                if "INV" in self.cheat_buf: 
                    for k in self.player.inventory.counts: self.player.inventory.counts[k] = self.player.inventory.cap
                    self.cheat_buf = ""
                if "SKIP" in self.cheat_buf: self.round_p, self.wave_timer, self.cheat_buf = self.pizza_goal, 0, ""
                if "OVER" in self.cheat_buf: self.state, self.cheat_buf = 'GAME_OVER', ""
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
            if self.recipe_menu.is_open and not self.world.oven.active: self.recipe_menu.toggle()
            if self.wave_timer <= 0:
                if self.round_p >= self.pizza_goal:
                    self.state, self.wave_timer, self.recipe_menu.is_open = 'SHOP', settings.SHOP_DURATION, False
                    self.recipe_menu.target = self.recipe_menu.cpos
                    self.om.reset_orders(); self.shop_menu.refresh_active()
                else:
                    self.state = 'GAME_OVER'
        elif self.state == 'SHOP':
            self.wave_timer -= dt
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
                
                # Clone maluses for third roulette as placeholder
                self.roulette_menu.start(self.malus_manager.maluses, w_opts, self.malus_manager.maluses)

        elif self.state == 'ROULETTE':
             if self.roulette_menu.update(dt):
                 # Roulette finished
                 self.state, self.wave_timer, self.wave_num = 'PLAYING', settings.WAVE_DURATION, self.wave_num + 1
                 self.pizza_goal += settings.PIZZA_GOAL_INCREMENT
                 self.round_p = 0
                 
                 self.world.dim = 1
                 self.player.respawn(settings.MAP_WIDTH//2+settings.PLAYER_SIZE, settings.MAP_HEIGHT//2-settings.PLAYER_SIZE//2)
                 
                 # Set Weapon
                 sel_weap = self.roulette_menu.selected_weapon
                 if sel_weap:
                     self.player.weapon = sel_weap.full_id
                     self.last_weapon = self.player.weapon
                 
                 self.world.spawn()
                 self.world.enemy_manager.projectiles.clear()
                 self.world.res_manager.drops.clear()
                 
                 # Apply Malus
                 self.malus_manager.new_round(self.roulette_menu.selected_malus)

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
            if self.f_a > 0: self.f_s.set_alpha(int(self.f_a)); self.screen.blit(self.f_s, (0, 0))
            score_txt = self.font.render(f"SCORE : {self.score}", True, (255,255,255))
            self.screen.blit(score_txt, (settings.SCREEN_WIDTH//2 - score_txt.get_width()//2, 20))
            
            if self.state != 'DYING':
                self.ui.draw(self.screen, self.player.inventory, self.pizzas_made, self.wave_num, max(0, self.wave_timer), self.player.health, self.player.max_health, self.player.weapon, self.round_p, self.pizza_goal, self.malus_manager.current_malus)
            
            if self.state != 'SHOP': self.recipe_menu.draw(self.screen, self.player.inventory, self.om)
            if self.world.dim == 1: self.ui.draw_arrow(self.screen, self.player.rect, self.world.oven.rect)
            if self.state == 'SHOP': self.shop_menu.draw(self.screen, self)
            if self.state == 'ROULETTE': self.roulette_menu.draw(self.screen)
        pygame.display.flip()
    def run(self):
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            self.handle(); self.update(dt); self.draw()
        pygame.quit(); sys.exit()