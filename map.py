import pygame, settings, random

class Map:
    def __init__(self):
        self.width, self.height, self.tiles = settings.MAP_WIDTH, settings.MAP_HEIGHT, {0: [], 1: []}
        for p in ["assets/grass1.png", "assets/grass2.png", "assets/grass.png", "assets/grass4.png", "assets/grass5.png"]:
            try:
                base = pygame.transform.scale(pygame.image.load(p).convert(), (128, 128))
                green, gray = base.copy(), pygame.transform.grayscale(base)
                gray.set_alpha(80); green.blit(gray, (0, 0)); self.tiles[1].append(green)
                pink = gray.copy(); pink.set_alpha(255); ps = pygame.Surface((128, 128)); ps.fill((235, 140, 180)); pink.blit(ps, (0, 0), special_flags=pygame.BLEND_MULT); self.tiles[0].append(pink)
            except: pass
        self.cols, self.rows = (self.width // 128) + 1, (self.height // 128) + 1
        self.grid = [[random.randint(0, len(self.tiles[1])-1) if self.tiles[1] else 0 for _ in range(self.cols)] for _ in range(self.rows)]

    def draw(self, surf, ox, oy, dim):
        sc, sr = max(0, int(ox // 128)), max(0, int(oy // 128))
        ec, er = min(self.cols, int((ox + settings.SCREEN_WIDTH) // 128) + 1), min(self.rows, int((oy + settings.SCREEN_HEIGHT) // 128) + 1)
        if not self.tiles[dim]: return
        for r in range(sr, er):
            for c in range(sc, ec): surf.blit(self.tiles[dim][self.grid[r][c] % len(self.tiles[dim])], (c * 128 - ox, r * 128 - oy))