import pygame, pygame_gui, settings, math

class Menu:
    def __init__(self, screen):
        self.screen, self.manager = screen, pygame_gui.UIManager((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), 'theme.json')
        
        # Background
        try: self.bg = pygame.transform.scale(pygame.image.load("assets/menu_bg.png").convert(), (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        except: 
            self.bg = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
            self.bg.fill((20, 20, 30))

        # Fonts
        try: 
            self.font = pygame.font.Font("assets/Handpixies.ttf", 50)
            self.story_font = pygame.font.Font("assets/Handpixies.ttf", 32)
            self.title_font = pygame.font.Font("assets/Handpixies.ttf", 80)
        except: 
            self.font = pygame.font.SysFont("Arial", 50)
            self.story_font = pygame.font.SysFont("Arial", 32)
            self.title_font = pygame.font.SysFont("Arial", 80)

        # Navigation
        self.options = [
            {"label": "JOUER", "action": "START"},
            {"label": "HISTOIRE", "action": "STORY"},
            {"label": "TUTO", "action": "TUTO"},
            {"label": "QUITTER", "action": "QUIT"}
        ]
        self.selection = 0
        self.in_story = False
        
        cx = settings.SCREEN_WIDTH // 2
        sy = 450
        for i, opt in enumerate(self.options):
            txt = self.font.render(opt["label"], True, (255, 255, 255))
            opt["rect"] = txt.get_rect(center=(cx, sy + i * 70))

        self.panel_rect = pygame.Rect(0, 0, 900, 500)
        self.panel_rect.center = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2)
        
        self.view_rect = pygame.Rect(0, 0, 800, 300)
        self.view_rect.midtop = (self.panel_rect.centerx, self.panel_rect.top + 90)
        
        self.back_rect = pygame.Rect(0, 0, 200, 50)
        self.back_rect.midbottom = (self.panel_rect.centerx, self.panel_rect.bottom - 30)

        self.lore_raw = "Ancien cuisto du legendaire pirate Jackass-Parrow, Cuisto Bongo a vu son destin basculer le jour ou son capitaine l'a accidentellement mutile d'un coup de canon. Pour reparer son erreur, un ami proche du pirate lui greffa des protheses mecaniques habitees par une entite demoniaque.<br><br>Le pacte est terrible : si cette jambe mecanique n'est pas constamment rassasiee, l'entite prend le controle de Bongo pour massacrer tout ce qui bouge. Exile sur une terre de portails dimensionnels, Bongo n'a plus qu'un seul but : cuisiner des pizzas a l'infini pour endormir la bete qui sommeille en lui."
        self.story_lines = self.wrap_text(self.lore_raw.replace("<br>", "\n"), self.story_font, self.view_rect.width - 20)
        
        self.scroll_y = 0
        self.line_h = 35
        self.total_h = len(self.story_lines) * self.line_h
        self.max_scroll = max(0, self.total_h - self.view_rect.height)
        
        self.mute_rect = pygame.Rect(settings.SCREEN_WIDTH - 160, settings.SCREEN_HEIGHT - 60, 140, 40)

    def wrap_text(self, text, font, inner_width):
        lines = []
        for paragraph in text.split('\n'):
            words = paragraph.split(' ')
            if not words or (len(words) == 1 and not words[0]):
                lines.append("")
                continue
            curr_line = words[0]
            for word in words[1:]:
                if font.size(curr_line + " " + word)[0] < inner_width:
                    curr_line += " " + word
                else:
                    lines.append(curr_line)
                    curr_line = word
            lines.append(curr_line)
        return lines

    def handle_events(self, e):
        
        if self.in_story:
            if e.type == pygame.KEYDOWN:
                if e.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_e]: self.in_story = False
                if e.key == pygame.K_UP: self.scroll_y -= 30
                if e.key == pygame.K_DOWN: self.scroll_y += 30
            elif e.type == pygame.MOUSEWHEEL:
                self.scroll_y -= e.y * 30
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.back_rect.collidepoint(e.pos): self.in_story = False
            
            self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
            
        else:
            self.manager.process_events(e)
            if e.type == pygame.KEYDOWN:
                if e.key in [pygame.K_UP, pygame.K_z]: self.selection = (self.selection - 1) % len(self.options)
                if e.key in [pygame.K_DOWN, pygame.K_s]: self.selection = (self.selection + 1) % len(self.options)
                if e.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]:
                    return self.trigger(self.options[self.selection]["action"])
            elif e.type == pygame.MOUSEMOTION:
                for i, opt in enumerate(self.options):
                    if opt["rect"].collidepoint(e.pos): self.selection = i
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, opt in enumerate(self.options):
                    if opt["rect"].collidepoint(e.pos): return self.trigger(opt["action"])
                if hasattr(self, 'mute_rect') and self.mute_rect.collidepoint(e.pos):
                    settings.MUSIC_VOLUME = 0.5 if settings.MUSIC_VOLUME == 0 else 0
        return None

    def trigger(self, action):
        if action == "START": return "START"
        if action == "QUIT": return "QUIT"
        if action == "STORY": self.in_story = True
        return None

    def update(self, dt): 
        if not self.in_story:
            self.manager.update(dt)

    def draw(self):
        self.screen.blit(self.bg, (0, 0))
        
        if self.in_story:
            overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            
            pygame.draw.rect(self.screen, (30, 25, 40), self.panel_rect, border_radius=20)
            pygame.draw.rect(self.screen, (255, 215, 0), self.panel_rect, 4, border_radius=20)
            
            t = self.font.render("HISTOIRE", True, (255, 180, 50))
            self.screen.blit(t, (self.panel_rect.centerx - t.get_width()//2, self.panel_rect.y + 30))
            
            self.screen.set_clip(self.view_rect)
            for i, line in enumerate(self.story_lines):
                y = self.view_rect.y + i * self.line_h - self.scroll_y
                if y + self.line_h < self.view_rect.y or y > self.view_rect.bottom: continue
                
                s = self.story_font.render(line, True, (220, 220, 220))
                self.screen.blit(s, (self.view_rect.centerx - s.get_width()//2, y))
            self.screen.set_clip(None)
            
            if self.max_scroll > 0:
                sb_h = self.view_rect.height
                th_h = max(30, sb_h * (sb_h / max(sb_h, self.total_h)))
                th_y = self.view_rect.y + (self.scroll_y / self.max_scroll) * (sb_h - th_h)
                
                sb_rect = pygame.Rect(self.view_rect.right + 5, self.view_rect.y, 6, sb_h)
                th_rect = pygame.Rect(self.view_rect.right + 5, th_y, 6, th_h)
                pygame.draw.rect(self.screen, (50, 50, 60), sb_rect, border_radius=3)
                pygame.draw.rect(self.screen, (200, 180, 50), th_rect, border_radius=3)

            mx, my = pygame.mouse.get_pos()
            hov = self.back_rect.collidepoint((mx, my))
            col = (255, 50, 50) if hov else (200, 200, 200)
            
            pygame.draw.rect(self.screen, (50, 10, 10) if hov else (30, 30, 30), self.back_rect, border_radius=10)
            pygame.draw.rect(self.screen, col, self.back_rect, 2, border_radius=10)
            
            bt = self.font.render("RETOUR", True, col)
            self.screen.blit(bt, (self.back_rect.centerx - bt.get_width()//2, self.back_rect.centery - bt.get_height()//2))

        else:
            for i, opt in enumerate(self.options):
                col = (255, 215, 0) if i == self.selection else (255, 255, 255)
                
                bg_rect = opt["rect"].inflate(60, 20)
                bs = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
                bg_col = (50, 0, 0, 180) if i == self.selection else (20, 20, 30, 150)
                pygame.draw.rect(bs, bg_col, (0,0,bg_rect.w, bg_rect.h), border_radius=15)
                if i == self.selection:
                    pygame.draw.rect(bs, (255, 215, 0), (0,0,bg_rect.w, bg_rect.h), 2, border_radius=15)
                self.screen.blit(bs, bg_rect.topleft)

                shad = self.font.render(opt["label"], True, (0, 0, 0))
                self.screen.blit(shad, (opt["rect"].x + 2, opt["rect"].y + 2))
                txt = self.font.render(opt["label"], True, col)
                self.screen.blit(txt, opt["rect"])
                
                if i == self.selection:
                    cursor = self.font.render(">", True, (255, 215, 0))
                    off = math.sin(pygame.time.get_ticks() * 0.01) * 5
                    self.screen.blit(cursor, (opt["rect"].x - 40 + off, opt["rect"].y))

            # Mute Button
            if hasattr(self, 'mute_rect'):
                 mx, my = pygame.mouse.get_pos()
                 hov = self.mute_rect.collidepoint((mx, my))
                 bg_col = (100, 50, 50) if hov else (50, 30, 30)
                 if settings.MUSIC_VOLUME == 0: bg_col = (50, 50, 50) # Muted style
                 
                 pygame.draw.rect(self.screen, bg_col, self.mute_rect, border_radius=10)
                 pygame.draw.rect(self.screen, (200, 200, 200), self.mute_rect, 2, border_radius=10)
                 
                 txt_str = "SON: OFF" if settings.MUSIC_VOLUME == 0 else "SON: ON"
                 mt = self.story_font.render(txt_str, True, (255, 255, 255))
                 self.screen.blit(mt, (self.mute_rect.centerx - mt.get_width()//2, self.mute_rect.centery - mt.get_height()//2))
