import pygame, settings

class UI:
    def __init__(self, font):
        self.font, self.count_f, self.icons = pygame.font.SysFont("Arial", 20, True), pygame.font.SysFont("Arial", 22, True), {}
        try:
            m = {"tomato": "assets/tomato-icon.png", "cheese": "assets/fromage-icon.png", "dough": "assets/dough.png", "drum_weapon": "assets/drum.png", "pizza_stat": "assets/pizza_marguerita.png"}
            for k, p in m.items(): self.icons[k] = pygame.transform.scale(pygame.image.load(p).convert_alpha(), (40, 40))
        except: pass

    def draw(self, surface, inv, p_made, wave_num, wave_timer, weapon=None):
        w_txt = self.font.render(f"VAGUE {wave_num}", True, (255, 215, 100))
        surface.blit(w_txt, (settings.SCREEN_WIDTH//2 - w_txt.get_width()//2, 70))
        t_txt = self.font.render(f"{int(wave_timer//60):02d}:{int(wave_timer%60):02d}", True, (255, 255, 255))
        surface.blit(t_txt, (settings.SCREEN_WIDTH//2 - t_txt.get_width()//2, 100))
        prect = pygame.Rect(20, 20, 100, 60)
        ps = pygame.Surface(prect.size, pygame.SRCALPHA)
        pygame.draw.rect(ps, (30, 35, 50, 180), (0,0,prect.w,prect.h), border_radius=12)
        surface.blit(ps, prect.topleft)
        pygame.draw.rect(surface, (100, 110, 140), prect, 2, border_radius=12)
        if "pizza_stat" in self.icons:
            surface.blit(self.icons["pizza_stat"], (prect.x + 10, prect.y + 10))
            txt = self.count_f.render(str(p_made), True, (255, 255, 255))
            surface.blit(txt, (prect.x + 55, prect.y + 18))
        rect = pygame.Rect(settings.SCREEN_WIDTH - 225, 20, 205, 60)
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (30, 35, 50, 180), (0,0,rect.w,rect.h), border_radius=12)
        surface.blit(s, rect.topleft)
        pygame.draw.rect(surface, (100, 110, 140), rect, 2, border_radius=12)
        for i, t in enumerate(["cheese", "tomato", "dough"]):
            x, y = rect.x + 10 + i*65, rect.y + 10
            if t in self.icons:
                surface.blit(self.icons[t], (x, y))
                clr = (255, 80, 80) if inv.is_full(t) else (255, 255, 255)
                ts = self.font.render(str(inv.counts[t]), True, clr)
                tw, th = ts.get_size()
                bx, by, bw, bh = x + 40 - max(22, tw+6) + 5, y + 40 - th + 3, max(22, tw+6), th + 2
                ns = pygame.Surface((bw, bh), pygame.SRCALPHA)
                pygame.draw.rect(ns, (20, 25, 40, 160), (0,0,bw,bh), border_radius=5)
                surface.blit(ns, (bx, by))
                surface.blit(ts, (bx + bw//2 - tw//2, by + bh//2 - th//2))
        if weapon and weapon in self.icons:
            wr = pygame.Rect(rect.right - 40, rect.bottom + 10, 40, 40)
            ws = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.rect(ws, (30, 35, 50, 180), (0,0,40,40), border_radius=8)
            surface.blit(ws, wr.topleft)
            surface.blit(self.icons[weapon], wr.topleft)
