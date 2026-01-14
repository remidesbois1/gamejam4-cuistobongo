import pygame, math, settings, random

class Upgrade:
    def __init__(self, key, name, desc, cost, val, icon, scale=1):
        self.key, self.name, self.desc, self.cost, self.val, self.icon, self.scale = key, name, desc, cost, val, icon, scale

    def apply(self, game):
        if self.key == "speed": game.player.vel += self.val
        elif self.key == "cap": game.player.inventory.cap += self.val
        elif self.key == "atk_speed": game.world.cd_limit = max(0.1, game.world.cd_limit - self.val)
        elif self.key == "health": 
            game.player.max_health += self.val
            game.player.health = min(game.player.health + self.val, game.player.max_health)
        elif self.key == "time": game.om.time_mult += self.val
        
        self.cost += self.scale
        if self.cost > 10: self.cost = 10

class ShopMenu:
    def __init__(self, font):
        self.font, self.title_f, self.small_f = font, pygame.font.Font("assets/Handpixies.ttf", 40), pygame.font.Font("assets/Handpixies.ttf", 22)
        self.idx, self.timer = 0, 0
        self.pool = []
        for k, v in settings.UPGRADE_DEFS.items():
            scale = 1
            self.pool.append(Upgrade(k, v["name"], v["desc"], v["cost"], v["val"], k, scale))
        self.active, self.icons = [], {}
        
        m = {"speed": "assets/vitesse_upgrade.png", "cap": "assets/backpack.png", "atk_speed": "assets/attaque_speed_upgrade.png", 
             "health": "assets/force_upgrade.png", "time": "assets/time_upgrade.png", "pizza": "assets/pizza_marguerita.png"}
        for k, p in m.items(): 
            try: self.icons[k] = pygame.transform.scale(pygame.image.load(p).convert_alpha(), (80, 80))
            except: pass
            
        self.btn_bg = None
        try: self.btn_bg = pygame.transform.scale(pygame.image.load("assets/stone2.png").convert_alpha(), (200, 60))
        except: pass
            
        self.bg_panel = pygame.image.load("assets/ui_panel.png").convert_alpha()
        self.bg_paper = pygame.image.load("assets/ui_paper.png").convert_alpha()

        self.refresh_active()

    def refresh_active(self):
        self.active = random.sample(self.pool, 3)

    def handle_input(self, e, game):
        can_buy = any(game.pizzas_made >= u.cost for u in self.active)
        limit = 3 if can_buy else 4

        if e.type == pygame.KEYDOWN:
            if e.key in settings.KEYS_LEFT: self.idx = (self.idx - 1) % limit
            elif e.key in settings.KEYS_RIGHT: self.idx = (self.idx + 1) % limit
            elif e.key in settings.KEYS_DOWN: 
                if not can_buy: self.idx = 3
            elif e.key in settings.KEYS_UP and self.idx == 3: self.idx = 1
            elif e.key in settings.KEYS_VALIDATE:
                if self.idx == 3:
                     # Button Pass
                     if not can_buy: game.wave_timer = 0
                else:
                    up = self.active[self.idx]
                    if game.pizzas_made >= up.cost:
                        game.pizzas_made -= up.cost
                        up.apply(game)
                        
                        others = [u for u in self.pool if u not in self.active]
                        if others: self.active[self.idx] = random.choice(others)
                        
                        can_buy = any(game.pizzas_made >= u.cost for u in self.active)
                        if not can_buy: self.idx = 3

    def draw(self, surf, game):
        self.timer += 0.05
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 15, 20, 200))
        surf.blit(overlay, (0, 0))
        rect = pygame.Rect(settings.SCREEN_WIDTH//2-450, settings.SCREEN_HEIGHT//2-250, 900, 500)
        
        if self.bg_panel:
            surf.blit(pygame.transform.scale(self.bg_panel, rect.size), rect)
            
        title = self.title_f.render(settings.TEXT_SHOP_TITLE, True, settings.CLR_TEXT_GOLD)
        surf.blit(title, (rect.centerx - title.get_width()//2, rect.y + 30))
        if "pizza" in self.icons:
            ic = pygame.transform.scale(self.icons["pizza"], (50, 50))
            surf.blit(ic, (rect.right - 140, rect.y + 30))
            p_txt = self.title_f.render(f"x {game.pizzas_made}", True, settings.CLR_TEXT_MAIN)
            surf.blit(p_txt, (rect.right - 85, rect.y + 30))
        
        txt_col = (50, 30, 10)
        for i, up in enumerate(self.active):
            card_r = pygame.Rect(rect.x + 60 + i*280, rect.y + 140, 240, 300)
            
            if self.bg_paper:
                 surf.blit(pygame.transform.scale(self.bg_paper, card_r.size), card_r)
            else:
                 pygame.draw.rect(surf, settings.CLR_CARD_BG if i != self.idx else settings.CLR_CARD_ACTIVE, card_r, border_radius=15)
            
            if i == self.idx:
                v = 2 + abs(int(math.sin(self.timer*2)*4))
                pygame.draw.rect(surf, (0, 200, 255), card_r.inflate(v, v), 3, border_radius=15)
            if up.icon in self.icons: surf.blit(self.icons[up.icon], (card_r.centerx - 40, card_r.y + 30))
            n_t = self.small_f.render(up.name, True, txt_col)
            surf.blit(n_t, (card_r.centerx - n_t.get_width()//2, card_r.y + 130))
            d_t = self.small_f.render(up.desc, True, (100, 80, 60))
            surf.blit(d_t, (card_r.centerx - d_t.get_width()//2, card_r.y + 170))
            pr_t = self.small_f.render(f"{up.cost} Pizzas", True, (0, 150, 0) if game.pizzas_made >= up.cost else (200, 0, 0))
            surf.blit(pr_t, (card_r.centerx - pr_t.get_width()//2, card_r.y + 230))
            if i == self.idx:
                buy_t = self.small_f.render(settings.TEXT_SHOP_BUY, True, settings.CLR_TEXT_GOLD)
                surf.blit(buy_t, (card_r.centerx - buy_t.get_width()//2, card_r.bottom + 20))
        
        can_buy = any(game.pizzas_made >= u.cost for u in self.active)
        quit_rect = pygame.Rect(rect.centerx - 100, rect.bottom - 70, 200, 60)
        is_sel = (self.idx == 3)
        
        if self.btn_bg:
            if can_buy:
                # Disabled state (grayscale or dimmed)
                disabled_bg = self.btn_bg.copy()
                disabled_bg.fill((100, 100, 100), special_flags=pygame.BLEND_MULT)
                surf.blit(disabled_bg, quit_rect)
            else:
                surf.blit(self.btn_bg, quit_rect)
                if is_sel: surf.blit(self.btn_bg, quit_rect, special_flags=pygame.BLEND_ADD)
        else:
            col = (100, 100, 100) if can_buy else settings.CLR_BTN_RED
            if not can_buy and is_sel: col = settings.CLR_BTN_RED_HOVER
            pygame.draw.rect(surf, col, quit_rect, border_radius=10)
        
        if is_sel and not can_buy:
             v = 2 + abs(int(math.sin(self.timer*2)*4))
             pygame.draw.rect(surf, (255, 215, 0), quit_rect.inflate(v, v), 3, border_radius=10)
        
        q_txt_col = (150, 150, 150) if can_buy else settings.CLR_TEXT_MAIN
        q_txt = self.small_f.render(settings.TEXT_SKIP_BTN, True, q_txt_col)
        surf.blit(q_txt, (quit_rect.centerx - q_txt.get_width()//2, quit_rect.centery - q_txt.get_height()//2))
