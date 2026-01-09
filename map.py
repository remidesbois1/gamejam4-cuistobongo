import pygame
import settings

class Map:
    def __init__(self):
        self.width = settings.MAP_WIDTH
        self.height = settings.MAP_HEIGHT

    def draw(self, surface, offset_x, offset_y, current_dim):
        if current_dim == 0: # Cheese
            bg_color = settings.DIM_CHEESE_BG
            grid_color = settings.DIM_CHEESE_GRID
        else: # Tomato
            bg_color = settings.DIM_TOMATO_BG
            grid_color = settings.DIM_TOMATO_GRID

        surface.fill(bg_color)
        
        # Draw a grid to visualize movement
        for x in range(0, self.width + settings.TILE_SIZE, settings.TILE_SIZE):
            pygame.draw.line(surface, grid_color, (x - offset_x, 0), (x - offset_x, settings.SCREEN_HEIGHT))
        for y in range(0, self.height + settings.TILE_SIZE, settings.TILE_SIZE):
            pygame.draw.line(surface, grid_color, (0, y - offset_y), (settings.SCREEN_WIDTH, y - offset_y))