import pygame
import settings

class Camera:
    def __init__(self, map_width, map_height):
        self.offset_x = 0
        self.offset_y = 0
        self.map_width = map_width
        self.map_height = map_height

    def update(self, target_rect):
        self.offset_x = target_rect.centerx - settings.SCREEN_WIDTH // 2
        self.offset_y = target_rect.centery - settings.SCREEN_HEIGHT // 2

        # Clamp camera to map boundaries
        self.offset_x = max(0, min(self.offset_x, self.map_width - settings.SCREEN_WIDTH))
        self.offset_y = max(0, min(self.offset_y, self.map_height - settings.SCREEN_HEIGHT))

    def apply(self, rect):
        return rect.move(-self.offset_x, -self.offset_y)
