import pygame, sys, settings
from map import Map
from player import Player
from camera import Camera
from world import WorldManager
from menu import Menu
from ui import UI
from recipe_menu import RecipeMenu
from order_manager import OrderManager

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
        self.font = pygame.font.SysFont("Arial", 36, True)

    def start(self):
        self.map = Map()
        self.player = Player(settings.MAP_WIDTH//2+80, settings.MAP_HEIGHT//2-40, self.map)
        self.world = WorldManager(self.map)
        self.camera = Camera(settings.MAP_WIDTH, settings.MAP_HEIGHT)
        self.ui, self.recipe_menu, self.score, self.f_a = UI(self.font), RecipeMenu(self.font), 0, 0
        self.state = 'PLAYING'

    def handle(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT: self.running = False
            if self.state == 'MENU':
                res = self.menu.handle_events(e)
                if res == "START": self.start()
                elif res == "QUIT": self.running = False
            elif self.state == 'PLAYING':
                if self.recipe_menu.is_open:
                    p = self.recipe_menu.handle_input(e, self.player, self.om)
                    if p: self.score += p
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_e:
                    if self.world.oven.active: self.recipe_menu.toggle()
                    else: self.world.trigger_weapon(self.player)

    def update(self, dt):
        if self.state == 'MENU': self.menu.update(dt)
        else:
            if not self.recipe_menu.is_open: self.player.handle_input(dt)
            if self.world.update(self.player, dt): self.f_a = 255
            self.f_a = max(0, self.f_a - 1000 * dt)
            self.camera.update(self.player.rect)
            self.recipe_menu.update(dt)
            self.om.update(dt)
            if self.recipe_menu.is_open and not self.world.oven.active: self.recipe_menu.toggle()

    def draw(self):
        if self.state == 'MENU': self.menu.draw()
        else:
            self.world.draw(self.screen, self.camera.offset_x, self.camera.offset_y)
            self.player.draw(self.screen, self.camera.offset_x, self.camera.offset_y)
            if self.f_a > 0:
                self.f_s.set_alpha(int(self.f_a))
                self.screen.blit(self.f_s, (0, 0))
            score_txt = self.font.render(f"SCORE : {self.score}", True, (255,255,255))
            self.screen.blit(score_txt, (settings.SCREEN_WIDTH//2 - score_txt.get_width()//2, 20))
            self.ui.draw(self.screen, self.player.inventory, self.player.weapon)
            self.recipe_menu.draw(self.screen, self.player.inventory, self.om)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            self.handle()
            self.update(dt)
            self.draw()
        pygame.quit(); sys.exit()