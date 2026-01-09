import pygame
import settings

class Map:
    def __init__(self):
        self.width = settings.SCREEN_WIDTH
        self.height = settings.SCREEN_HEIGHT

    def draw(self, surface):
        surface.fill(settings.BLACK)