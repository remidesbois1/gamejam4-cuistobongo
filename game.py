import pygame, sys, settings
from map import Map
from player import Player
from camera import Camera
from world import WorldManager
from menu import Menu
from ui import UI
from recipe_menu import RecipeMenu
from order_manager import OrderManager
from shop_menu import ShopMenu

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
        self.font, self.cheat_buf = pygame.font.Font("assets/Handpixies.ttf", 36), ""
        self.shop_menu = None

    def start(self):
        self.map, self.pizzas_made = Map(), 0
        self.player = Player(settings.MAP_WIDTH//2+80, settings.MAP_HEIGHT//2-40, self.map)
        self.world = WorldManager(self.map)
        self.camera = Camera(settings.MAP_WIDTH, settings.MAP_HEIGHT)
        self.ui, self.recipe_menu, self.shop_menu = UI(self.font), RecipeMenu(self.font), ShopMenu(self.font)
        self.score, self.f_a, self.wave_timer, self.wave_num, self.state = 0, 0, 90, 1, 'PLAYING'

    def handle(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT: self.running = False
            if e.type == pygame.KEYDOWN:
                self.cheat_buf = (self.cheat_buf + e.unicode).upper()[-10:]
                if "PIZZA" in self.cheat_buf: self.pizzas_made, self.cheat_buf = self.pizzas_made + 15, ""
                if "INV" in self.cheat_buf: 
                    for k in self.player.inventory.counts: self.player.inventory.counts[k] = self.player.inventory.cap
                    self.cheat_buf = ""
                if "SKIP" in self.cheat_buf: self.wave_timer, self.cheat_buf = 0, ""
            if self.state == 'MENU':
                res = self.menu.handle_events(e)
                if res == "START": self.start()
                elif res == "QUIT": self.running = False
            elif self.state == 'PLAYING':
                if self.recipe_menu.is_open:
                    p = self.recipe_menu.handle_input(e, self.player, self.om)
                    if p and p > 0: self.score, self.pizzas_made = self.score + p, self.pizzas_made + 1
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_e:
                    if self.world.oven.active: self.recipe_menu.toggle()
                    else: self.world.trigger_weapon(self.player)
            elif self.state == 'SHOP': self.shop_menu.handle_input(e, self)

    def update(self, dt):
        if self.state == 'MENU': self.menu.update(dt)
        elif self.state == 'PLAYING':
            if not self.recipe_menu.is_open: self.player.handle_input(dt)
            if self.player.health <= 0:
                self.player.respawn(settings.MAP_WIDTH//2+80, settings.MAP_HEIGHT//2-40)
                self.world.dim = 1
                self.wave_timer -= 30
                self.pizzas_made //= 2
            if self.world.update(self.player, dt): self.f_a = 255
            self.f_a, self.wave_timer = max(0, self.f_a - 1000 * dt), self.wave_timer - dt
            self.camera.update(self.player.rect)
            self.recipe_menu.update(dt)
            self.score += self.om.update(dt)
            if self.recipe_menu.is_open and not self.world.oven.active: self.recipe_menu.toggle()
            if self.wave_timer <= 0:
                self.state, self.wave_timer, self.recipe_menu.is_open = 'SHOP', 20, False
                self.recipe_menu.target = self.recipe_menu.cpos
                self.om.reset_orders(); self.shop_menu.refresh_active()
        elif self.state == 'SHOP':
            self.wave_timer -= dt
            if self.wave_timer <= 0: 
                self.state, self.wave_timer, self.wave_num = 'PLAYING', 90, self.wave_num + 1
                self.world.dim = 1
                self.player.respawn(settings.MAP_WIDTH//2+80, settings.MAP_HEIGHT//2-40)
                self.world.spawn()
                self.world.enemy_manager.projectiles.clear()
                self.world.res_manager.drops.clear()

    def draw(self):
        if self.state == 'MENU': self.menu.draw()
        else:
            self.world.draw(self.screen, self.camera.offset_x, self.camera.offset_y)
            self.player.draw(self.screen, self.camera.offset_x, self.camera.offset_y)
            if self.f_a > 0: self.f_s.set_alpha(int(self.f_a)); self.screen.blit(self.f_s, (0, 0))
            score_txt = self.font.render(f"SCORE : {self.score}", True, (255,255,255))
            self.screen.blit(score_txt, (settings.SCREEN_WIDTH//2 - score_txt.get_width()//2, 20))
            self.ui.draw(self.screen, self.player.inventory, self.pizzas_made, self.wave_num, max(0, self.wave_timer), self.player.health, self.player.max_health, self.player.weapon)
            if self.state != 'SHOP': self.recipe_menu.draw(self.screen, self.player.inventory, self.om)
            if self.world.dim == 1: self.ui.draw_arrow(self.screen, self.player.rect, self.world.oven.rect)
            if self.state == 'SHOP': self.shop_menu.draw(self.screen, self)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            self.handle(); self.update(dt); self.draw()
        pygame.quit(); sys.exit()