import pygame, settings, math, random

class UI:
    def __init__(self, font):
        self.font, self.count_f, self.icons = pygame.font.Font("assets/Handpixies.ttf", 20), pygame.font.Font("assets/Handpixies.ttf", 28), {}
        self.large_font = pygame.font.Font("assets/Handpixies.ttf", 36)
        
        m = {"tomato": "assets/tomato-icon.png", "cheese": "assets/fromage-icon.png", "dough": "assets/dough.png", "pizza_stat": "assets/pizza_marguerita.png"}
        for k, p in m.items(): self.icons[k] = pygame.transform.scale(pygame.image.load(p).convert_alpha(), (40, 40))
        
        self.bg_panel = pygame.image.load("assets/ui_panel.png").convert_alpha()
        self.game_ptr = None

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
        
        # Hurry Up Text
        if wave_timer <= settings.MUSIC_SPEEDUP_TIME and self.game_ptr and self.game_ptr.state == 'PLAYING':
             h_txt = self.large_font.render("Dépêchez-vous !!", True, (255, 50, 50))
             angle = math.sin(pygame.time.get_ticks() * 0.01) * 5
             rot_txt = pygame.transform.rotate(h_txt, angle)
             surface.blit(rot_txt, (settings.SCREEN_WIDTH//2 - rot_txt.get_width()//2, b_rect.bottom + 10))

        prect = pygame.Rect(20, 20, 150, 70)
        if self.bg_panel:
            surface.blit(pygame.transform.scale(self.bg_panel, prect.size), prect)

        # Goal
        surface.blit(self.icons["pizza_stat"], (prect.x + 15, prect.y + 15))
        clr = (50, 255, 50) if round_p >= p_goal else (255, 255, 255)
        txt = self.count_f.render(f"{round_p}/{p_goal}", True, clr)
        surface.blit(txt, (prect.x + 65, prect.y + 23))

        if malus:
            # Show only for first 20 seconds of the wave
            # wave_timer counts down from WAVE_DURATION.
            elapsed = settings.WAVE_DURATION - wave_timer
            if elapsed < 20:
                # Malus Panel (Top Right)
                mw, mh = 220, 150 # Taller panel
                m_rect = pygame.Rect(settings.SCREEN_WIDTH - 240, 100, mw, mh)
                
                if self.bg_panel:
                    surface.blit(pygame.transform.scale(self.bg_panel, m_rect.size), m_rect)
                
                # Icon
                if malus.icon:
                     # Scale icon
                     icon = pygame.transform.scale(malus.icon, (64, 64))
                     surface.blit(icon, (m_rect.centerx - 32, m_rect.y + 10))
                     
                # Title
                t_name = self.font.render(malus.name, True, (255, 100, 100))
                surface.blit(t_name, (m_rect.centerx - t_name.get_width()//2, m_rect.y + 80))
                
                # Desc (multiline)
                desc_font = pygame.font.Font("assets/Handpixies.ttf", 16)
                words = malus.description.split(' ')
                lines = []
                cur_line = ""
                for w in words:
                    test_line = cur_line + w + " "
                    if desc_font.size(test_line)[0] < mw - 20:
                        cur_line = test_line
                    else:
                        lines.append(cur_line)
                        cur_line = w + " "
                lines.append(cur_line)
                
                dy = m_rect.y + 105
                for l in lines:
                    t_desc = desc_font.render(l, True, (200, 200, 200))
                    surface.blit(t_desc, (m_rect.centerx - t_desc.get_width()//2, dy))
                    dy += 18

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

class RouletteSlot:
    def __init__(self, items, font, frame_title, tick_sound=None):
        self.items = items
        self.font = font
        self.frame_title = frame_title
        self.tick_sound = tick_sound
        self.current_idx = 0
        self.timer = 0
        self.speed = 0.05
        self.state = 'SPINNING'
        self.total_time = 0
        self.selected_item = None
        self.spin_duration = random.uniform(1.5, 2.5) # Random spin time for desync

    def update(self, dt):
        if self.state == 'SPINNING':
            self.total_time += dt
            self.timer += dt
            if self.timer > self.speed:
                self.timer = 0
                self.current_idx = (self.current_idx + 1) % len(self.items)
                if self.tick_sound: self.tick_sound.play()
            
            if self.total_time > self.spin_duration:
                self.state = 'SLOWING'
                self.speed = 0.05
        
        elif self.state == 'SLOWING':
            self.timer += dt
            if self.timer > self.speed:
                self.timer = 0
                self.current_idx = (self.current_idx + 1) % len(self.items)
                self.speed *= 1.2
                if self.tick_sound: self.tick_sound.play()
                
                if self.speed > 0.4:
                    self.state = 'SHOWING'
                    self.selected_item = self.items[self.current_idx]
                    self.timer = 0

        elif self.state == 'SHOWING':
            return True # Ready
        return False

    def draw(self, surf, center_x, center_y):
        # Frame Title
        t = self.font.render(self.frame_title, True, (0, 0, 0))
        surf.blit(t, (center_x - t.get_width()//2, center_y - 100))

        # Current Icon
        item = self.items[self.current_idx]
        
        # Draw frame
        pygame.draw.rect(surf, (0, 0, 0), (center_x - 70, center_y - 70, 140, 140), 4)
        
        icon = getattr(item, 'icon', None)
        if hasattr(item, 'get'): # wrapper dict support if needed
             icon = item.get('icon')

        if icon:
            surf.blit(icon, (center_x - 64, center_y - 64))
        
        # Name
        # Name
        color = (0, 0, 0) if self.state == 'SHOWING' else (100, 100, 100)
        name = getattr(item, 'name', '')
        
        words = name.split(' ')
        lines = []
        cur_line = ""
        max_width = 180
        
        for w in words:
             test_line = cur_line + w + " "
             if self.font.size(test_line)[0] < max_width:
                 cur_line = test_line
             else:
                 lines.append(cur_line)
                 cur_line = w + " "
        lines.append(cur_line)
        
        y_off = center_y + 80
        for l in lines:
            nm = self.font.render(l, True, color)
            surf.blit(nm, (center_x - nm.get_width()//2, y_off))
            y_off += self.font.get_height()
        
        # Removed Desc from roulette slot as requested

class RouletteMenu:
    def __init__(self, font):
        self.font = font
        self.active = False
        self.bg = None
        try: self.bg = pygame.transform.scale(pygame.image.load("assets/recipe_menu.png").convert_alpha(), (900, 500)) # Wider bg
        except: pass
        self.title_font = pygame.font.Font("assets/Handpixies.ttf", 48)
        self.malus_slot = None
        self.weapon_slot = None
        self.bonus_slot = None
        self.show_timer = 0
        self.tick_sound = None
        try: 
            self.tick_sound = pygame.mixer.Sound("assets/casino.wav")
            self.tick_sound.set_volume(0.3)
        except: pass

    def start(self, maluses, weapons, bonuses):
        self.active = True
        self.malus_slot = RouletteSlot(maluses, self.font, "Malus !", self.tick_sound)
        self.weapon_slot = RouletteSlot(weapons, self.font, "Arme !", self.tick_sound)
        self.bonus_slot = RouletteSlot(bonuses, self.font, "Bonus !", self.tick_sound)
        self.show_timer = 0

    @property
    def selected_malus(self):
        return self.malus_slot.selected_item if self.malus_slot else None
    
    @property
    def selected_weapon(self):
        return self.weapon_slot.selected_item if self.weapon_slot else None
        
    @property
    def selected_bonus(self):
        return self.bonus_slot.selected_item if self.bonus_slot else None

    def update(self, dt):
        if not self.active: return
        
        m_done = self.malus_slot.update(dt)
        w_done = self.weapon_slot.update(dt)
        b_done = self.bonus_slot.update(dt)
        
        if m_done and w_done and b_done:
            self.show_timer += dt
            if self.show_timer > 4.0: # Show result for 4 seconds (longer)
                self.active = False
                return True
        return False

    def draw(self, surf):
        if not self.active: return
        
        # Overlay
        overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surf.blit(overlay, (0, 0))
        
        cw, ch = surf.get_width(), surf.get_height()
        cx, cy = cw//2, ch//2

        if self.bg:
            r = self.bg.get_rect(center=(cx, cy))
            surf.blit(self.bg, r)
        else:
            pygame.draw.rect(surf, (255, 255, 255), (cx - 450, cy - 250, 900, 500))
        
        t = self.title_font.render("Roulette du Destin !", True, (0, 0, 0))
        surf.blit(t, (cx - t.get_width()//2, cy - 200))
        
        # Draw Slots (3 columns)
        if self.malus_slot: self.malus_slot.draw(surf, cx - 250, cy)
        if self.weapon_slot: self.weapon_slot.draw(surf, cx, cy)
        if self.bonus_slot: self.bonus_slot.draw(surf, cx + 250, cy)
