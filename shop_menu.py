import pygame, math, settings

class ShopMenu:
    def __init__(self, font):
        self.font, self.title_f, self.small_f = font, pygame.font.SysFont("Arial", 40, True), pygame.font.SysFont("Arial", 22, True)
        self.idx, self.timer = 0, 0
        self.upgrades = [
            {"name": "Vitesse", "key": "speed", "cost": 3, "val": 50, "desc": "+50 Vitesse"},
            {"name": "Sac à dos", "key": "cap", "cost": 5, "val": 1, "desc": "+1 Capacité"},
            {"name": "Tambour", "key": "atk_speed", "cost": 4, "val": 0.1, "desc": "-0.1s Recharge"}
        ]
        self.icons = {}
        try:
            m = {"speed": "assets/grass.png", "cap": "assets/dough.png", "atk_speed": "assets/drum.png", "pizza": "assets/pizza_marguerita.png"}
            for k, p in m.items(): self.icons[k] = pygame.transform.scale(pygame.image.load(p).convert_alpha(), (80, 80))
        except: pass

    def handle_input(self, event, game):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT: self.idx = (self.idx - 1) % 3
            elif event.key == pygame.K_RIGHT: self.idx = (self.idx + 1) % 3
            elif event.key == pygame.K_e:
                up = self.upgrades[self.idx]
                if game.pizzas_made >= up["cost"]:
                    game.pizzas_made -= up["cost"]
                    if up["key"] == "speed": game.player.vel += up["val"]
                    elif up["key"] == "cap": game.player.inventory.cap += up["val"]
                    elif up["key"] == "atk_speed": game.world.cd_limit = max(0.2, game.world.cd_limit - up["val"])
                    up["cost"] = int(up["cost"] * 1.5) + 1

    def draw(self, surf, game):
        self.timer += 0.05
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 15, 20, 200))
        surf.blit(overlay, (0, 0))
        bw, bh = 900, 500
        rect = pygame.Rect(settings.SCREEN_WIDTH//2-450, settings.SCREEN_HEIGHT//2-250, bw, bh)
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
            surf.blit(p_txt, (rect.right - 80, rect.y + 30))
        for i, up in enumerate(self.upgrades):
            card_r = pygame.Rect(rect.x + 60 + i*280, rect.y + 140, 240, 300)
            pygame.draw.rect(surf, (50, 55, 75) if i != self.idx else (70, 75, 100), card_r, border_radius=15)
            if i == self.idx:
                v = 2 + abs(int(math.sin(self.timer*2)*4))
                pygame.draw.rect(surf, (0, 200, 255), card_r.inflate(v, v), 3, border_radius=15)
            if up["key"] in self.icons: surf.blit(self.icons[up["key"]], (card_r.centerx - 40, card_r.y + 30))
            n_t = self.small_f.render(up["name"], True, (255, 255, 255))
            surf.blit(n_t, (card_r.centerx - n_t.get_width()//2, card_r.y + 130))
            d_t = self.small_f.render(up["desc"], True, (200, 200, 200))
            surf.blit(d_t, (card_r.centerx - d_t.get_width()//2, card_r.y + 170))
            pr_t = self.small_f.render(f"{up['cost']} Pizzas", True, (100, 255, 100) if game.pizzas_made >= up["cost"] else (255, 100, 100))
            surf.blit(pr_t, (card_r.centerx - pr_t.get_width()//2, card_r.y + 230))
            if i == self.idx:
                buy_t = self.small_f.render("Appuyer sur E", True, (255, 215, 100))
                surf.blit(buy_t, (card_r.centerx - buy_t.get_width()//2, card_r.bottom + 20))
