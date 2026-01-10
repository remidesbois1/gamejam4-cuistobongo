import pygame, math, settings, random

class Upgrade:
    def __init__(self, key, name, desc, cost, val, icon):
        self.key, self.name, self.desc, self.cost, self.val, self.icon = key, name, desc, cost, val, icon

    def apply(self, game):
        if self.key == "speed": game.player.vel += self.val
        elif self.key == "cap": game.player.inventory.cap += self.val
        elif self.key == "atk_speed": game.world.cd_limit = max(0.1, game.world.cd_limit - self.val)
        elif self.key == "damage": game.world.damage += self.val
        elif self.key == "time": game.om.time_mult += self.val
        self.cost = int(self.cost * 1.6) + 1

class ShopMenu:
    def __init__(self, font):
        self.font, self.title_f, self.small_f = font, pygame.font.Font("assets/Handpixies.ttf", 40), pygame.font.Font("assets/Handpixies.ttf", 22)
        self.idx, self.timer = 0, 0
        self.pool = [
            Upgrade("speed", "Vitesse", "+50 Vitesse", 3, 50, "speed"),
            Upgrade("cap", "Sac à dos", "+1 Capacité", 5, 1, "cap"),
            Upgrade("atk_speed", "Tambour", "-0.1s Recharge", 4, 0.1, "atk_speed"),
            Upgrade("damage", "Force", "+1 Dégâts", 4, 1, "damage"),
            Upgrade("time", "Patience", "+20% Temps", 3, 0.2, "time")
        ]
        self.active, self.icons = [], {}
        try:
            m = {"speed": "assets/grass.png", "cap": "assets/dough.png", "atk_speed": "assets/drum.png", 
                 "damage": "assets/shockwave.png", "time": "assets/pizza.png", "pizza": "assets/pizza_marguerita.png"}
            for k, p in m.items(): self.icons[k] = pygame.transform.scale(pygame.image.load(p).convert_alpha(), (80, 80))
        except: pass
        self.refresh_active()

    def refresh_active(self):
        self.active = random.sample(self.pool, 3)

    def handle_input(self, e, game):
        if e.type == pygame.KEYDOWN:
            if e.key in [pygame.K_LEFT, pygame.K_a]: self.idx = (self.idx - 1) % 3
            elif e.key in [pygame.K_RIGHT, pygame.K_d]: self.idx = (self.idx + 1) % 3
            elif e.key == pygame.K_e:
                up = self.active[self.idx]
                if game.pizzas_made >= up.cost:
                    game.pizzas_made -= up.cost
                    up.apply(game)
                    # Replace with a new one not currently active
                    others = [u for u in self.pool if u not in self.active]
                    if others: self.active[self.idx] = random.choice(others)

    def draw(self, surf, game):
        self.timer += 0.05
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 15, 20, 200))
        surf.blit(overlay, (0, 0))
        rect = pygame.Rect(settings.SCREEN_WIDTH//2-450, settings.SCREEN_HEIGHT//2-250, 900, 500)
        pygame.draw.rect(surf, (30, 35, 50), rect, border_radius=20)
        pygame.draw.rect(surf, (100, 110, 140), rect, 3, border_radius=20)
        title = self.title_f.render("PAUSE CUISINE - AMÉLIORATIONS", True, (255, 215, 100))
        surf.blit(title, (rect.centerx - title.get_width()//2, rect.y + 30))
        t_txt = self.small_f.render(f"Reprise dans: {max(0, int(game.wave_timer))}s", True, (255, 255, 255))
        surf.blit(t_txt, (rect.centerx - t_txt.get_width()//2, rect.y + 80))
        if "pizza" in self.icons:
            ic = pygame.transform.scale(self.icons["pizza"], (50, 50))
            surf.blit(ic, (rect.right - 140, rect.y + 30))
            p_txt = self.title_f.render(f"x {game.pizzas_made}", True, (255, 255, 255))
            surf.blit(p_txt, (rect.right - 85, rect.y + 30))
        for i, up in enumerate(self.active):
            card_r = pygame.Rect(rect.x + 60 + i*280, rect.y + 140, 240, 300)
            pygame.draw.rect(surf, (50, 55, 75) if i != self.idx else (70, 75, 100), card_r, border_radius=15)
            if i == self.idx:
                v = 2 + abs(int(math.sin(self.timer*2)*4))
                pygame.draw.rect(surf, (0, 200, 255), card_r.inflate(v, v), 3, border_radius=15)
            if up.icon in self.icons: surf.blit(self.icons[up.icon], (card_r.centerx - 40, card_r.y + 30))
            n_t = self.small_f.render(up.name, True, (255, 255, 255))
            surf.blit(n_t, (card_r.centerx - n_t.get_width()//2, card_r.y + 130))
            d_t = self.small_f.render(up.desc, True, (200, 200, 200))
            surf.blit(d_t, (card_r.centerx - d_t.get_width()//2, card_r.y + 170))
            pr_t = self.small_f.render(f"{up.cost} Pizzas", True, (100, 255, 100) if game.pizzas_made >= up.cost else (255, 100, 100))
            surf.blit(pr_t, (card_r.centerx - pr_t.get_width()//2, card_r.y + 230))
            if i == self.idx:
                buy_t = self.small_f.render("Appuyer sur E", True, (255, 215, 100))
                surf.blit(buy_t, (card_r.centerx - buy_t.get_width()//2, card_r.bottom + 20))
