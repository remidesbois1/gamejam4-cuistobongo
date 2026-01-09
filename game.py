import pygame
import sys
import settings
from map import Map
from player import Player
from camera import Camera
from world import WorldManager
from menu import Menu

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game States: 'MENU', 'PLAYING'
        self.state = 'MENU'
        
        self.menu = Menu(self.screen)
        
        # Game elements (initially None, will be initialized on game start)
        self.map = None
        self.player = None
        self.world = None
        self.camera = None
        self.tints = []
        self.font = pygame.font.SysFont("Arial", 36, bold=True)

    def start_game(self):
        self.map = Map()
        start_x = settings.MAP_WIDTH // 2 - 24
        start_y = settings.MAP_HEIGHT // 2 - 24
        self.player = Player(start_x, start_y, self.map)
        
        self.world = WorldManager(self.map)
        self.camera = Camera(settings.MAP_WIDTH, settings.MAP_HEIGHT)
        
        # Create tint surfaces
        self.tints = []
        for color in [settings.TINT_CHEESE, settings.TINT_TOMATO]:
            s = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill(color)
            self.tints.append(s)
            
        self.state = 'PLAYING'

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if self.state == 'MENU':
                menu_action = self.menu.handle_events(event)
                if menu_action == "START":
                    self.start_game()
                elif menu_action == "QUIT":
                    self.running = False
            elif self.state == 'PLAYING':
                # Game logic events are mostly polling (keys), 
                # but we could add pause here later
                pass

    def update(self, time_delta):
        if self.state == 'MENU':
            self.menu.update(time_delta)
        elif self.state == 'PLAYING':
            self.player.handle_input()
            self.world.update(self.player.rect)
            self.camera.update(self.player.rect)

    def draw(self):
        if self.state == 'MENU':
            self.menu.draw()
        elif self.state == 'PLAYING':
            self.world.draw(self.screen, self.camera.offset_x, self.camera.offset_y)
            self.player.draw(self.screen, self.camera.offset_x, self.camera.offset_y)

            # Apply dimension tint
            self.screen.blit(self.tints[self.world.current_dim], (0, 0))
            
            # Draw HUD
            text_color = settings.WHITE
            text_surf = self.font.render(self.world.dim_names[self.world.current_dim], True, text_color)
            self.screen.blit(text_surf, (20, 20))

        pygame.display.flip()

    def run(self):
        while self.running:
            time_delta = self.clock.tick(settings.FPS) / 1000.0
            self.handle_events()
            self.update(time_delta)
            self.draw()
        
        pygame.quit()
        sys.exit()