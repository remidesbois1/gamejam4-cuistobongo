import pygame, pygame_gui, settings, math, json

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

        self.options = [
            {"label": "JOUER", "action": "START"},
            {"label": "HISTOIRE", "action": "STORY"},
            {"label": "TUTO", "action": "TUTO"},
            {"label": "SANDBOX", "action": "SANDBOX"},
            {"label": "SCOREBOARD", "action": "SCORES"},
            {"label": "QUITTER", "action": "QUIT"}
        ]
        self.selection = 0
        self.in_story = False
        self.in_scores = False
        
        cx = settings.SCREEN_WIDTH // 2
        sy = 400

        start_x = settings.MENU_OFFSET_X
        unit_w = 240
        unit_h = 75
        gap = 15
        
        total_h = 4 * unit_h + 3 * gap
        start_y = (settings.SCREEN_HEIGHT - total_h) // 2 + settings.MENU_OFFSET_Y

        self.options[0]["rect"] = pygame.Rect(start_x, start_y, 2 * unit_w + gap, unit_h)
        
        self.options[1]["rect"] = pygame.Rect(start_x, start_y + unit_h + gap, unit_w, unit_h)
        self.options[2]["rect"] = pygame.Rect(start_x + unit_w + gap, start_y + unit_h + gap, unit_w, unit_h)
        
        self.options[3]["rect"] = pygame.Rect(start_x, start_y + 2*(unit_h + gap), unit_w, unit_h)
        self.options[4]["rect"] = pygame.Rect(start_x + unit_w + gap, start_y + 2*(unit_h + gap), unit_w, unit_h)
        

        self.options[5]["rect"] = pygame.Rect(start_x, start_y + 3*(unit_h + gap), 2 * unit_w + gap, unit_h)

        self.panel_rect = pygame.Rect(0, 0, 900, 500)
        self.panel_rect.center = (settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT // 2)
        
        self.view_rect = pygame.Rect(0, 0, 800, 300)
        self.view_rect.midtop = (self.panel_rect.centerx, self.panel_rect.top + 90)
        
        self.back_rect = pygame.Rect(0, 0, 200, 50)
        self.back_rect.midbottom = (self.panel_rect.centerx, self.panel_rect.bottom - 30)

        self.lore_raw = "Ancien cuistot du légendaire pirate Jackass-Parrow, Cuisto Bongo a vu son destin basculer le jour où son capitaine l'a accidentellement mutilé d'un coup de canon. Pour réparer son erreur, un ami proche du pirate lui greffa des prothèses mécaniques habitées par une entité. \nSi l'entité mécanique n'est pas constamment rassasiée, elle finira par prendre le contrôle de Bongo pour massacrer tout ce qui bouge. Exilé sur une terre lointaine envahie par une dimension parallèle, Bongo essaye désormais de survivre en cumulant ses deux passions, les pizzas et la musique. C'est donc armé de son bongo ainsi que de son saxophone et de sa flûte de pan qu'il décida de vivre le restant de ses jours, en faisant des allers-retours entre les portails dimensionnels et son fourneau afin de concocter une quantité suffisante pour nourrir la machine."
        self.story_lines = self.wrap_text(self.lore_raw, self.story_font, self.view_rect.width - 20)
        
        self.scroll_y = 0
        self.line_h = 35
        self.total_h = len(self.story_lines) * self.line_h
        self.max_scroll = max(0, self.total_h - self.view_rect.height)
        
        self.mute_rect = pygame.Rect(80, settings.SCREEN_HEIGHT - 60, 140, 40)

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
                if e.key in settings.KEYS_CANCEL: self.in_story = False
                if e.key in settings.KEYS_UP: self.scroll_y -= 30
                if e.key in settings.KEYS_DOWN: self.scroll_y += 30
            elif e.type == pygame.MOUSEWHEEL:
                self.scroll_y -= e.y * 30
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.back_rect.collidepoint(e.pos): self.in_story = False
            
            self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
            
        elif self.in_scores:
            if e.type == pygame.KEYDOWN:
                if e.key in settings.KEYS_CANCEL: self.in_scores = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.back_rect.collidepoint(e.pos): self.in_scores = False
            
        else:
            self.manager.process_events(e)
            if e.type == pygame.KEYDOWN:
                if e.key in settings.KEYS_UP:
                    if self.selection == 0: self.selection = 5
                    elif self.selection in [1, 2]: self.selection = 0
                    elif self.selection == 3: self.selection = 1
                    elif self.selection == 4: self.selection = 2
                    elif self.selection == 5: self.selection = 3 # defaulting to left
                    
                elif e.key in settings.KEYS_DOWN:
                    if self.selection == 0: self.selection = 1
                    elif self.selection == 1: self.selection = 3
                    elif self.selection == 2: self.selection = 4
                    elif self.selection in [3, 4]: self.selection = 5
                    elif self.selection == 5: self.selection = 0

                elif e.key in settings.KEYS_LEFT:
                    if self.selection == 2: self.selection = 1
                    elif self.selection == 4: self.selection = 3
                    elif self.selection == 0: self.selection = 2
                    elif self.selection == 1: self.selection = 4
                    elif self.selection == 3: self.selection = 4 # wrap
                    elif self.selection == 5: self.selection = 4

                elif e.key in settings.KEYS_RIGHT:
                    if self.selection == 1: self.selection = 2
                    elif self.selection == 3: self.selection = 4
                    elif self.selection == 0: self.selection = 1
                    elif self.selection == 2: self.selection = 0
                    elif self.selection == 4: self.selection = 3 # wrap
                    elif self.selection == 5: self.selection = 3
                    
                if e.key in settings.KEYS_VALIDATE:
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
        if action == "SANDBOX": return "SANDBOX"
        if action == "TUTO": return "TUTO"
        if action == "STORY": self.in_story = True
        if action == "SCORES": self.in_scores = True
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

        elif self.in_scores:
            overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            
            # Panel
            pygame.draw.rect(self.screen, (30, 25, 40), self.panel_rect, border_radius=20)
            pygame.draw.rect(self.screen, (255, 215, 0), self.panel_rect, 4, border_radius=20)
            
            # Title
            t = self.font.render("TABLEAU DES SCORES", True, (255, 180, 50))
            self.screen.blit(t, (self.panel_rect.centerx - t.get_width()//2, self.panel_rect.y + 20))
            
            # Load Scores
            try:
                with open("score.json", "r") as f: scores = json.load(f)
                scores.sort(key=lambda x: x.get("score", 0), reverse=True)
            except: scores = []
            
            # Headers
            start_y = self.panel_rect.y + 90
            col_x = [self.panel_rect.x + 80, self.panel_rect.x + 200, self.panel_rect.x + 550, self.panel_rect.x + 750]
            
            headers = ["Rg", "Pseudo", "Score", "Vagues"]
            for i, h in enumerate(headers):
                 ht = self.story_font.render(h, True, (200, 200, 255))
                 self.screen.blit(ht, (col_x[i], start_y))
                 
            # Rows
            row_y = start_y + 40
            for i, s in enumerate(scores[:10]):
                y = row_y + i * 32
                col = (200, 255, 200) if i == 0 else ((255, 255, 220) if i < 3 else (200, 200, 200))
                
                # Rank
                self.screen.blit(self.story_font.render(f"#{i+1}", True, col), (col_x[0], y))
                # Name
                self.screen.blit(self.story_font.render(s.get("name", "???")[:12], True, col), (col_x[1], y))
                # Score
                self.screen.blit(self.story_font.render(str(s.get("score", 0)), True, col), (col_x[2], y))
                # Waves
                self.screen.blit(self.story_font.render(str(s.get("wave", 0)), True, col), (col_x[3], y))
            
            # Back Button
            mx, my = pygame.mouse.get_pos()
            hov = self.back_rect.collidepoint((mx, my))
            col = (255, 50, 50) if hov else (200, 200, 200)
            
            pygame.draw.rect(self.screen, (50, 10, 10) if hov else (30, 30, 30), self.back_rect, border_radius=10)
            pygame.draw.rect(self.screen, col, self.back_rect, 2, border_radius=10)
            
            bt = self.font.render("RETOUR", True, col)
            self.screen.blit(bt, (self.back_rect.centerx - bt.get_width()//2, self.back_rect.centery - bt.get_height()//2))

        else:
            for i, opt in enumerate(self.options):
                is_sel = (i == self.selection)
                label = opt["label"]
                
                rect = opt["rect"]
                bs = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                
                bg_color = (20, 20, 30, 150)
                text_color = (255, 255, 255)
                border_color = None
                
                if label == "JOUER":
                    if is_sel:
                        bg_color = (0, 100, 0, 200)
                        text_color = (50, 255, 50)
                        border_color = (50, 255, 50)
                    else:
                        bg_color = (0, 50, 0, 150)
                        text_color = (150, 255, 150)
                elif label == "QUITTER":
                    if is_sel:
                        bg_color = (100, 0, 0, 200)
                        text_color = (255, 50, 50)
                        border_color = (255, 50, 50)
                    else:
                        bg_color = (50, 0, 0, 150)
                        text_color = (255, 150, 150)
                else:
                    if is_sel:
                        bg_color = (50, 50, 70, 200)
                        text_color = (255, 215, 0)
                        border_color = (255, 215, 0)
                
                pygame.draw.rect(bs, bg_color, bs.get_rect(), border_radius=15)
                if border_color:
                    pygame.draw.rect(bs, border_color, bs.get_rect(), 3, border_radius=15)
                
                self.screen.blit(bs, rect.topleft)

                shad = self.font.render(label, True, (0, 0, 0))
                txt = self.font.render(label, True, text_color)
                
                if label == "SCOREBOARD":
                     shad = pygame.transform.scale_by(shad, 0.7)
                     txt = pygame.transform.scale_by(txt, 0.7)
                
                txt_rect = txt.get_rect(center=rect.center)
                shad_rect = shad.get_rect(center=(rect.centerx + 2, rect.centery + 2))
                
                self.screen.blit(shad, shad_rect)
                self.screen.blit(txt, txt_rect)
                
                if is_sel:
                    off = math.sin(pygame.time.get_ticks() * 0.01) * 5
                    cursor_col = text_color
                    cursor = self.font.render(">", True, cursor_col)
                    self.screen.blit(cursor, (rect.x - 30 + off, rect.centery - cursor.get_height()//2))

            if hasattr(self, 'mute_rect'):
                 mx, my = pygame.mouse.get_pos()
                 hov = self.mute_rect.collidepoint((mx, my))
                 ms = pygame.Surface((self.mute_rect.w, self.mute_rect.h), pygame.SRCALPHA)
                 mbg_col = (100, 50, 50, 200) if hov else (50, 30, 30, 150)
                 if settings.MUSIC_VOLUME == 0: mbg_col = (50, 50, 50, 150)
                 
                 pygame.draw.rect(ms, mbg_col, ms.get_rect(), border_radius=10)
                 pygame.draw.rect(ms, (200, 200, 200), ms.get_rect(), 2, border_radius=10)
                 self.screen.blit(ms, self.mute_rect.topleft)
                 
                 txt_str = "SON: OFF" if settings.MUSIC_VOLUME == 0 else "SON: ON"
                 mt = self.story_font.render(txt_str, True, (255, 255, 255))
                 self.screen.blit(mt, (self.mute_rect.centerx - mt.get_width()//2, self.mute_rect.centery - mt.get_height()//2))
