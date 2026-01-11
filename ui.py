import pygame, settings, math

class UI:
    def __init__(self, font):
        self.font, self.count_f, self.icons = pygame.font.Font("assets/Handpixies.ttf", 20), pygame.font.Font("assets/Handpixies.ttf", 22), {}
        self.large_font = pygame.font.Font("assets/Handpixies.ttf", 36)
        try:
            m = {"tomato": "assets/tomato-icon.png", "cheese": "assets/fromage-icon.png", "dough": "assets/dough.png", "drum_weapon": "assets/drum.png", "pizza_stat": "assets/pizza_marguerita.png"}
            for k, p in m.items(): self.icons[k] = pygame.transform.scale(pygame.image.load(p).convert_alpha(), (40, 40))
            self.bg_panel = pygame.image.load("assets/ui_panel.png").convert_alpha()
        except: 
            self.bg_panel = None

    def draw(self, surface, inv, p_made, wave_num, wave_timer, hp, max_hp, weapon=None, round_p=0, p_goal=1):
        # Timer & Wave - Center Top
        time_str = f"{int(wave_timer//60):02d}:{int(wave_timer%60):02d}"
        main_text = f"VAGUE {wave_num}   -   {time_str}"
        
        tw, th = self.large_font.size(main_text)
        
        # Fixed Dimensions
        bw, bh = 350, th + 30
        b_rect = pygame.Rect(settings.SCREEN_WIDTH//2 - bw//2, 12, bw, bh)
        
        # Background for Timer/Wave
        if self.bg_panel:
            surface.blit(pygame.transform.scale(self.bg_panel, b_rect.size), b_rect)
        else:
            s_bg = pygame.Surface(b_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(s_bg, (30, 35, 50, 200), (0,0,b_rect.w, b_rect.h), border_radius=15)
            surface.blit(s_bg, b_rect.topleft)
            pygame.draw.rect(surface, (100, 110, 140), b_rect, 2, border_radius=15)

        # Text
        txt = self.large_font.render(main_text, True, (255, 230, 200))
        surface.blit(txt, (settings.SCREEN_WIDTH//2 - tw//2, b_rect.centery - th//2))

        
        # Goal/Pizza UI
        prect = pygame.Rect(20, 20, 140, 70)
        if self.bg_panel:
            surface.blit(pygame.transform.scale(self.bg_panel, prect.size), prect)
        else:
            ps = pygame.Surface(prect.size, pygame.SRCALPHA)
            pygame.draw.rect(ps, (30, 35, 50, 180), (0,0,prect.w,prect.h), border_radius=12)
            surface.blit(ps, prect.topleft)
            pygame.draw.rect(surface, (100, 110, 140), prect, 2, border_radius=12)

        if "pizza_stat" in self.icons:
            surface.blit(self.icons["pizza_stat"], (prect.x + 15, prect.y + 15))
            clr = (50, 255, 50) if round_p >= p_goal else (255, 255, 255)
            txt = self.count_f.render(f"{round_p}/{p_goal}", True, clr)
            surface.blit(txt, (prect.x + 65, prect.y + 23))

        rect = pygame.Rect(settings.SCREEN_WIDTH - 240, 20, 220, 70)
        if self.bg_panel:
            surface.blit(pygame.transform.scale(self.bg_panel, rect.size), rect)
        else:
            s = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(s, (30, 35, 50, 180), (0,0,rect.w,rect.h), border_radius=12)
            surface.blit(s, rect.topleft)
            pygame.draw.rect(surface, (100, 110, 140), rect, 2, border_radius=12)

        for i, t in enumerate(["cheese", "tomato", "dough"]):
            x, y = rect.x + 20 + i*68, rect.y + 15
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
    def draw_arrow(self, surface, p_rect, oven_rect):
        dx, dy = oven_rect.centerx - p_rect.centerx, oven_rect.centery - p_rect.centery
        if math.hypot(dx, dy) < 400: return
        angle = math.atan2(dy, dx)
        cx, cy = settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2
        ax, ay = cx + math.cos(angle) * 150, cy + math.sin(angle) * 150
        pts = [
            (ax + math.cos(angle) * 20, ay + math.sin(angle) * 20),
            (ax + math.cos(angle + 2.6) * 15, ay + math.sin(angle + 2.6) * 15),
            (ax + math.cos(angle - 2.6) * 15, ay + math.sin(angle - 2.6) * 15)
        ]
        pygame.draw.polygon(surface, (255, 50, 50), pts)
        pygame.draw.polygon(surface, (255, 255, 255), pts, 2)
