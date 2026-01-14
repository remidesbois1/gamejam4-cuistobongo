import pygame, settings, math
from recipe import RECIPES

class PizzaCard:
    @staticmethod
    @staticmethod
    def render(surf, o, rect, menu, inv, is_active):
        draw_rect = rect.copy()
        
        # Scale up selected card
        if menu.is_open and is_active:
            draw_rect = draw_rect.inflate(20, 20)

        if o and o.timer <= 10:
            off_x = math.sin(menu.timer * 50) * 3
            off_y = math.cos(menu.timer * 42) * 3
            draw_rect.x += int(off_x)
            draw_rect.y += int(off_y)

        if menu.bg_paper:
            surf.blit(pygame.transform.scale(menu.bg_paper, draw_rect.size), draw_rect)
        else:
            pygame.draw.rect(surf, (40,45,60) if not o else ((60,65,85) if (menu.is_open and is_active) else (50,55,75)), draw_rect, border_radius=10)
            
        if o and o.timer <= 25:
            intensity = (25 - o.timer) / 25.0
            alpha = int(intensity * 120 * (0.6 + 0.4 * math.sin(menu.timer * 10)))
            overlay = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(overlay, (255, 0, 0, alpha), (0, 0, draw_rect.w, draw_rect.h), border_radius=10)
            surf.blit(overlay, draw_rect)

        txt_col = (50, 30, 10) if menu.bg_paper else (255, 230, 0)
        
        if not o:
            t = menu.small.render(settings.TEXT_WAITING if menu.is_open else settings.TEXT_EMPTY, True, (100,100,120) if menu.bg_paper else (80,85,110))
            surf.blit(t, (draw_rect.centerx-t.get_width()//2, draw_rect.centery-t.get_height()//2)); return

        iy = draw_rect.y + (20 if menu.is_open else 10)
        img = menu.icons.get(o.recipe.image if menu.is_open else o.recipe.image+"_s")
        if img: surf.blit(img, (draw_rect.centerx-img.get_width()//2, iy))
        
        if menu.is_open:
            n = menu.nums.render(o.recipe.nom, True, txt_col)
            surf.blit(n, (draw_rect.centerx - n.get_width()//2, iy + 90))
        
        p = max(0, o.timer / o.max_time)
        by = iy + (125 if menu.is_open else 45)
        pygame.draw.rect(surf, (60,60,80), (draw_rect.x+20, by, draw_rect.w-40, 6), border_radius=3)
        pygame.draw.rect(surf, (255,200,0) if p > 0.3 else (255,50,50), (draw_rect.x+20, by, int((draw_rect.w-40)*p), 6), border_radius=3)
        
        if menu.is_open:
            st = menu.small.render(f"{settings.TEXT_SCORE}: {int(o.recipe.points * max(0.5, p))} pts", True, txt_col)
            surf.blit(st, (draw_rect.centerx-st.get_width()//2, iy+135))

        ings = [ing for ing in ["dough", "tomato", "cheese"] if o.recipe.ingredients.get(ing, 0) > 0]
        iscl, ispc = (48 if menu.is_open else 32), (58 if menu.is_open else 40)
        iy_ing, x = iy + (175 if menu.is_open else 60), draw_rect.centerx - (len(ings)*ispc - (ispc-iscl))//2
        for i_name in ings:
            surf.blit(pygame.transform.scale(menu.icons[i_name], (iscl, iscl)), (x, iy_ing))
            need = o.recipe.ingredients[i_name]
            has = inv.counts[i_name]
            
            txt_str = f"x{need}"
            for ox, oy in [(-2,0), (2,0), (0,-2), (0,2)]:
                out = menu.nums.render(txt_str, True, (255, 255, 255))
                surf.blit(out, (x + iscl//2 - out.get_width()//2 + ox, iy_ing + iscl + oy - 5))
            
            q_col = (200, 0, 0) if has < need else (0, 0, 0)
            qty = menu.nums.render(txt_str, True, q_col)
            surf.blit(qty, (x + iscl//2 - qty.get_width()//2, iy_ing + iscl - 5))
            
            if menu.is_open:
                col = (0, 180, 0) if has >= need else (220, 0, 0)
                cur = menu.small.render(f"({has})", True, col)
                surf.blit(cur, (x + iscl//2 - cur.get_width()//2, iy_ing - 18))

            x += ispc

        if menu.is_open and inv.has_ingredients(o.recipe.ingredients):
            pygame.draw.rect(surf, (255,180,0), (draw_rect.x, draw_rect.bottom-40, draw_rect.w, 40), border_radius=10)
            vt = menu.small.render(settings.TEXT_VALIDATE, True, (0,0,0)); surf.blit(vt, (draw_rect.centerx-vt.get_width()//2, draw_rect.bottom-30))

class RecipeMenu:
    def __init__(self, font):
        self.font, self.icons, self.is_open, self.idx, self.timer = font, {}, False, 0, 0
        self.titles, self.small, self.nums = pygame.font.Font("assets/Handpixies.ttf", 32), pygame.font.Font("assets/Handpixies.ttf", 18), pygame.font.Font("assets/Handpixies.ttf", 20)
        try:
            m = {"tomato": "assets/tomato-icon.png", "cheese": "assets/fromage-icon.png", "dough": "assets/dough.png"}
            for k, p in m.items(): self.icons[k] = pygame.image.load(p).convert_alpha()
            for r in RECIPES:
                img = pygame.image.load(r.image).convert_alpha()
                self.icons[r.image], self.icons[r.image + "_s"] = pygame.transform.scale(img, (96,96)), pygame.transform.scale(img, (40,40))
            self.bg_panel = pygame.image.load("assets/recipe_menu.png").convert_alpha()
            self.bg_paper = pygame.image.load("assets/ui_paper.png").convert_alpha()
        except: 
            self.bg_panel = None
            self.bg_paper = None

        self.cpos, self.opos = pygame.Vector2(30, settings.SCREEN_HEIGHT-190), pygame.Vector2(settings.SCREEN_WIDTH//2-420, settings.SCREEN_HEIGHT//2-220)
        self.pos, self.target = pygame.Vector2(self.cpos), self.cpos

    def toggle(self): self.is_open = not self.is_open; self.target = self.opos if self.is_open else self.cpos
    def update(self, dt): self.pos += (self.target - self.pos) * 0.12; self.timer += dt * 5
    def handle_input(self, e, p, om):
        if not self.is_open or e.type != pygame.KEYDOWN: return None
        if e.key in settings.KEYS_LEFT: self.idx = (self.idx - 1) % 3
        elif e.key in settings.KEYS_RIGHT: self.idx = (self.idx + 1) % 3
        elif e.key in settings.KEYS_VALIDATE:
            if om.active_orders[self.idx] is None:
                self.toggle()
                return None
            
            res = om.complete_order(self.idx, p.inventory)
            if res and res > 0:
                return res
            else:
                self.toggle()
                return None
        return None

    def draw(self, surf, inv, om):
        bw, bh = (840, 440) if self.is_open else (380, 170)
        rect = pygame.Rect(self.pos.x, self.pos.y, bw, bh)
        
        if self.bg_panel:
            surf.blit(pygame.transform.scale(self.bg_panel, (bw, bh)), rect)
        else:
            s = pygame.Surface((bw, bh), pygame.SRCALPHA); pygame.draw.rect(s, (30,35,50,235), (0,0,bw,bh), border_radius=15)
            surf.blit(s, rect); pygame.draw.rect(surf, (100,110,140), rect, 2, border_radius=15)
            
        if self.is_open: surf.blit(self.titles.render(settings.TEXT_OVEN_TITLE, True, settings.CLR_TEXT_GOLD), (rect.x+30, rect.y+20))
        cw, ch = (240, 310) if self.is_open else (110, 125)
        sx, sy = rect.x + (40 if self.is_open else 20), rect.y + (80 if self.is_open else 25)
        for i, o in enumerate(om.active_orders):
            PizzaCard.render(surf, o, pygame.Rect(sx + i*(cw+(20 if self.is_open else 10)), sy, cw, ch), self, inv, i == self.idx)
        if self.is_open:
            ax = sx + self.idx*(cw+20) + cw//2
            ap = [(ax-20, sy-45+math.sin(self.timer*2)*5), (ax+20, sy-45+math.sin(self.timer*2)*5), (ax, sy-20+math.sin(self.timer*2)*5)]
            pygame.draw.polygon(surf, (255,230,0), ap); pygame.draw.polygon(surf, (255,255,255), ap, 2)
