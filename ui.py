import pygame, settings, math, random

class UI:
    def __init__(self, font):
        self.font, self.count_f, self.icons = pygame.font.Font("assets/Handpixies.ttf", 20), pygame.font.Font("assets/Handpixies.ttf", 28), {}
        self.large_font = pygame.font.Font("assets/Handpixies.ttf", 36)
        
        m = {"tomato": "assets/tomato-icon.png", "cheese": "assets/fromage-icon.png", "dough": "assets/dough.png", "pizza_stat": "assets/pizza_marguerita.png"}
        for k, p in m.items(): self.icons[k] = pygame.transform.scale(pygame.image.load(p).convert_alpha(), (40, 40))
        
        self.bg_panel = pygame.image.load("assets/ui_panel.png").convert_alpha()

    def draw(self, surface, inv, p_made, wave_num, wave_timer, hp, max_hp, weapon=None, round_p=0, p_goal=1, malus=None):
        time_str = f"{int(wave_timer//60):02d}:{int(wave_timer%60):02d}"
        main_text = f"VAGUE {wave_num}   -   {time_str}"
        
        tw, th = self.large_font.size(main_text)
        
        bw, bh = 350, th + 30
        b_rect = pygame.Rect(settings.SCREEN_WIDTH//2 - bw//2, 12, bw, bh)
        
        if self.bg_panel:
            surface.blit(pygame.transform.scale(self.bg_panel, b_rect.size), b_rect)

        # Text
        txt = self.large_font.render(main_text, True, settings.CLR_TEXT_CREAM)
        surface.blit(txt, (settings.SCREEN_WIDTH//2 - tw//2, b_rect.centery - th//2))

        prect = pygame.Rect(20, 20, 150, 70)
        if self.bg_panel:
            surface.blit(pygame.transform.scale(self.bg_panel, prect.size), prect)

        # Goal
        surface.blit(self.icons["pizza_stat"], (prect.x + 15, prect.y + 15))
        clr = (50, 255, 50) if round_p >= p_goal else (255, 255, 255)
        txt = self.count_f.render(f"{round_p}/{p_goal}", True, clr)
        surface.blit(txt, (prect.x + 65, prect.y + 23))

        if malus:
            # Malus Panel (Top Right, below inventory items logic if any, but let's put it top right specifically)
            # Actually inventory is at top right. Let's move inventory panel down or put malus below it.
            # Inventory is at settings.SCREEN_WIDTH - 240, 20
            
            # Put malus to the left of inventory or below.
            # Let's put it below for now.
            mw, mh = 220, 60
            m_rect = pygame.Rect(settings.SCREEN_WIDTH - 240, 100, mw, mh)
            
            if self.bg_panel:
                surface.blit(pygame.transform.scale(self.bg_panel, m_rect.size), m_rect)
            
            # Title
            t_name = self.font.render(malus.name, True, (255, 100, 100))
            surface.blit(t_name, (m_rect.centerx - t_name.get_width()//2, m_rect.y + 10))
            
            # Desc
            # Simple word wap or just small text
            t_desc = pygame.font.Font("assets/Handpixies.ttf", 16).render(malus.description, True, (200, 200, 200))
            surface.blit(t_desc, (m_rect.centerx - t_desc.get_width()//2, m_rect.y + 35))

        rect = pygame.Rect(settings.SCREEN_WIDTH - 240, 20, 220, 70)
        if self.bg_panel:
            surface.blit(pygame.transform.scale(self.bg_panel, rect.size), rect)

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

    def draw_penalty_anim(self, surface, death_timer, wave_num, wave_timer):
        start_y = 12
        center_y = settings.SCREEN_HEIGHT // 2 - 40
        
        current_y = start_y
        if death_timer > 1.5:
            t = min(1.0, (death_timer - 1.5) / 0.8)
            t = t * t * (3 - 2 * t)
            current_y = start_y + (center_y - start_y) * t
            
        shake_x, shake_y = 0, 0
        display_time = wave_timer
        
        if death_timer > 4.0:
            drain_prog = min(1.0, (death_timer - 4.0) / 1.5)
            display_time = max(0, wave_timer - 30 * drain_prog)
            if drain_prog < 1.0:
                 shake_x = random.randint(-2, 2)
                 shake_y = random.randint(-2, 2)

        main_text = f"{settings.TEXT_WAVE} {wave_num}   -   {int(display_time//60):02d}:{int(display_time%60):02d}"
        tw, th = self.large_font.size(main_text)
        bw, bh = 350, th + 30
        b_rect = pygame.Rect(settings.SCREEN_WIDTH//2 - bw//2 + shake_x, int(current_y) + shake_y, bw, bh)
        
        if self.bg_panel:
            surface.blit(pygame.transform.scale(self.bg_panel, b_rect.size), b_rect)

        txt = self.large_font.render(main_text, True, settings.CLR_TEXT_CREAM)
        surface.blit(txt, (settings.SCREEN_WIDTH//2 - tw//2 + shake_x, b_rect.centery - th//2 + shake_y))
        
        if death_timer > 2.5:
            fly_t = min(1.0, (death_timer - 2.5) / 1.5)
            
            start_x = settings.SCREEN_WIDTH + 150
            end_x = settings.SCREEN_WIDTH//2 + 190 
            
            t = fly_t * fly_t * (3 - 2 * fly_t)
            cur_x = start_x + (end_x - start_x) * t
            
            self.large_font.set_bold(True)
            pen_txt = self.large_font.render("-30s", True, (160, 0, 0))
            self.large_font.set_bold(False)
            surface.blit(pen_txt, (cur_x, b_rect.centery - pen_txt.get_height()//2))
