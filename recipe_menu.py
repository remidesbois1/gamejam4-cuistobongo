import pygame, settings, math
from recipe import RECIPES

class PizzaCard:
    @staticmethod
    def render(surf, o, rect, menu, inv, is_active):
        pygame.draw.rect(surf, (40,45,60) if not o else ((60,65,85) if (menu.is_open and is_active) else (50,55,75)), rect, border_radius=10)
        if menu.is_open and is_active:
            v = 2 + abs(int(math.sin(menu.timer)*4))
            pygame.draw.rect(surf, (0,200,255), rect.inflate(v,v), 3, border_radius=10)
        if not o:
            t = menu.small.render("EN ATTENTE..." if menu.is_open else "VIDE", True, (80,85,110))
            surf.blit(t, (rect.centerx-t.get_width()//2, rect.centery-t.get_height()//2)); return

        iy = rect.y + (20 if menu.is_open else 10)
        img = menu.icons.get(o.recipe.image if menu.is_open else o.recipe.image+"_s")
        if img: surf.blit(img, (rect.centerx-img.get_width()//2, iy))
        
        if menu.is_open:
            n = menu.nums.render(o.recipe.nom, True, (255, 230, 0))
            surf.blit(n, (rect.centerx - n.get_width()//2, iy + 90))
        
        p = max(0, o.timer / o.max_time)
        by = iy + (125 if menu.is_open else 45)
        pygame.draw.rect(surf, (60,60,80), (rect.x+20, by, rect.w-40, 6), border_radius=3)
        pygame.draw.rect(surf, (255,200,0) if p > 0.3 else (255,50,50), (rect.x+20, by, int((rect.w-40)*p), 6), border_radius=3)
        
        if menu.is_open:
            st = menu.small.render(f"SCORE: {int(o.recipe.points * max(0.5, p))} pts", True, (255,230,0))
            surf.blit(st, (rect.centerx-st.get_width()//2, iy+135))

        ings = [ing for ing in ["dough", "tomato", "cheese"] if o.recipe.ingredients.get(ing, 0) > 0]
        iscl, ispc = (48 if menu.is_open else 32), (58 if menu.is_open else 40)
        iy_ing, x = iy + (160 if menu.is_open else 55), rect.centerx - (len(ings)*ispc - (ispc-iscl))//2
        for i_name in ings:
            surf.blit(pygame.transform.scale(menu.icons[i_name], (iscl, iscl)), (x, iy_ing))
            need = o.recipe.ingredients[i_name]
            cnt = f"{inv.counts[i_name]}/{need}" if menu.is_open else str(need)
            txt = (menu.nums if menu.is_open else menu.small).render(cnt, True, (100,255,100) if inv.counts[i_name]>=need else (255,100,100))
            tw, th = txt.get_size(); bx = pygame.Rect(x+iscl-tw-4, iy_ing+iscl-th-2, tw+6, th+4)
            s = pygame.Surface(bx.size, pygame.SRCALPHA); pygame.draw.rect(s, (20,25,40,160), (0,0,bx.w,bx.h), border_radius=4)
            surf.blit(s, bx.topleft); pygame.draw.rect(surf, (80,90,110), bx, 1, border_radius=4)
            surf.blit(txt, (bx.centerx-tw//2, bx.centery-th//2)); x += ispc

        if menu.is_open and inv.has_ingredients(o.recipe.ingredients):
            pygame.draw.rect(surf, (255,180,0), (rect.x, rect.bottom-40, rect.w, 40), border_radius=10)
            vt = menu.small.render("VALIDER !", True, (0,0,0)); surf.blit(vt, (rect.centerx-vt.get_width()//2, rect.bottom-30))

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
        except: pass
        self.cpos, self.opos = pygame.Vector2(30, settings.SCREEN_HEIGHT-190), pygame.Vector2(settings.SCREEN_WIDTH//2-400, settings.SCREEN_HEIGHT//2-220)
        self.pos, self.target = pygame.Vector2(self.cpos), self.cpos

    def toggle(self): self.is_open = not self.is_open; self.target = self.opos if self.is_open else self.cpos
    def update(self, dt): self.pos += (self.target - self.pos) * 0.12; self.timer += dt * 5
    def handle_input(self, e, p, om):
        if not self.is_open or e.type != pygame.KEYDOWN: return None
        if e.key in [pygame.K_LEFT, pygame.K_a]: self.idx = (self.idx - 1) % 3
        elif e.key in [pygame.K_RIGHT, pygame.K_d]: self.idx = (self.idx + 1) % 3
        elif e.key == pygame.K_e:
            res = om.complete_order(self.idx, p.inventory); self.toggle(); return res
        return None

    def draw(self, surf, inv, om):
        bw, bh = (800, 420) if self.is_open else (360, 160)
        rect = pygame.Rect(self.pos.x, self.pos.y, bw, bh)
        s = pygame.Surface((bw, bh), pygame.SRCALPHA); pygame.draw.rect(s, (30,35,50,235), (0,0,bw,bh), border_radius=15)
        surf.blit(s, rect); pygame.draw.rect(surf, (100,110,140), rect, 2, border_radius=15)
        if self.is_open: surf.blit(self.titles.render("FOUR À PIZZA", True, (255,215,100)), (rect.x+30, rect.y+20))
        cw, ch = (230, 300) if self.is_open else (105, 120)
        sx, sy = rect.x + (40 if self.is_open else 20), rect.y + (80 if self.is_open else 25)
        for i, o in enumerate(om.active_orders):
            PizzaCard.render(surf, o, pygame.Rect(sx + i*(cw+(20 if self.is_open else 10)), sy, cw, ch), self, inv, i == self.idx)
        if self.is_open:
            ax = sx + self.idx*(cw+20) + cw//2
            ap = [(ax-20, sy-45+math.sin(self.timer*2)*5), (ax+20, sy-45+math.sin(self.timer*2)*5), (ax, sy-20+math.sin(self.timer*2)*5)]
            pygame.draw.polygon(surf, (255,230,0), ap); pygame.draw.polygon(surf, (255,255,255), ap, 2)
