import pygame
import sys
import settings
from map import Map
from player import Player

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.map = Map()
        start_x = settings.SCREEN_WIDTH // 2 - 16
        start_y = settings.SCREEN_HEIGHT // 2 - 16
        self.player = Player(start_x, start_y, self.map)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        self.player.handle_input()

    def draw(self):
        self.map.draw(self.screen)
        self.player.draw(self.screen)
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(settings.FPS)
        
        pygame.quit()
        sys.exit()