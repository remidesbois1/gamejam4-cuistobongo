import pygame
import settings
import random

class Map:
    def __init__(self):
        self.width, self.height, self.size = settings.MAP_WIDTH, settings.MAP_HEIGHT, 128
        self.tiles = {0: [], 1: []}
        for p in ["assets/grass1.png", "assets/grass2.png", "assets/grass.png", "assets/grass4.png", "assets/grass5.png"]:
            try: self.tiles[1].append(pygame.transform.scale(pygame.image.load(p).convert(), (128, 128)))
            except: pass
        try: self.tiles[0].append(pygame.transform.scale(pygame.image.load("assets/grass-alternante.png").convert(), (128, 128)))
        except: pass
        
        self.cols, self.rows = (settings.MAP_WIDTH // 128) + 1, (settings.MAP_HEIGHT // 128) + 1
        self.grid = [[(random.randint(0, len(self.tiles[0])-1) if self.tiles[0] else 0, 
                       random.randint(0, len(self.tiles[1])-1) if self.tiles[1] else 0) 
                      for _ in range(self.cols)] for _ in range(self.rows)]

    def draw(self, surf, ox, oy, dim):
        sc, sr = max(0, int(ox // 128)), max(0, int(oy // 128))
        ec, er = min(self.cols, int((ox + settings.SCREEN_WIDTH) // 128) + 1), min(self.rows, int((oy + settings.SCREEN_HEIGHT) // 128) + 1)
        if not self.tiles[dim]: return
        for r in range(sr, er):
            for c in range(sc, ec):
                surf.blit(self.tiles[dim][self.grid[r][c][dim]], (c * 128 - ox, r * 128 - oy))