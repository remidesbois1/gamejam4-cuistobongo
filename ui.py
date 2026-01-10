import pygame
import settings

class UI:
    def __init__(self, font):
        self.font = pygame.font.SysFont("Arial", 20, True)
        self.icons = {}
        try:
            for n in ["tomato", "cheese_ore", "dough", "drum"]:
                img = pygame.image.load(f"assets/{n}.png").convert_alpha()
                self.icons[n.replace("_ore","").replace("drum","drum_weapon")] = pygame.transform.scale(img, (40, 40))
        except: pass

    def draw(self, surface, inv, weapon=None):
        items = ["cheese", "tomato", "dough"]
        rect = pygame.Rect(settings.SCREEN_WIDTH - 225, 20, 205, 60)
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (30, 35, 50, 180), (0,0,rect.w,rect.h), border_radius=12)
        surface.blit(s, rect.topleft)
        pygame.draw.rect(surface, (100, 110, 140), rect, 2, border_radius=12)

        for i, t in enumerate(items):
            x, y = rect.x + 10 + i*65, rect.y + 10
            if t in self.icons:
                surface.blit(self.icons[t], (x, y))
                cnt = str(inv.counts[t])
                clr = (255, 80, 80) if inv.is_full(t) else (255, 255, 255)
                ts = self.font.render(cnt, True, clr)
                tw, th = ts.get_size()
                bx, by, bw, bh = x + 40 - max(22, tw+6) + 5, y + 40 - th + 3, max(22, tw+6), th + 2
                ns = pygame.Surface((bw, bh), pygame.SRCALPHA)
                pygame.draw.rect(ns, (20, 25, 40, 160), (0,0,bw,bh), border_radius=5)
                surface.blit(ns, (bx, by))
                pygame.draw.rect(surface, (100, 110, 140), (bx, by, bw, bh), 1, border_radius=5)
                surface.blit(ts, (bx + bw//2 - tw//2, by + bh//2 - th//2))
        
        if weapon in self.icons:
            wr = pygame.Rect(rect.right - 40, rect.bottom + 10, 40, 40)
            ws = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.rect(ws, (30, 35, 50, 180), (0,0,40,40), border_radius=8)
            surface.blit(ws, wr.topleft)
            pygame.draw.rect(surface, (100, 110, 140), wr, 1, border_radius=8)
            surface.blit(self.icons[weapon], (wr.x + 20 - 20, wr.y + 20 - 20))
