import pygame, settings, math
from recipe import RECIPES

class RecipeMenu:
    def __init__(self, font):
        self.font = font
        self.title_f = pygame.font.SysFont("Arial", 32, True)
        self.small_f = pygame.font.SysFont("Arial", 18, True)
        self.num_f = pygame.font.SysFont("Arial", 20, True)
        self.is_open, self.icons, self.idx, self.timer = False, {}, 0, 0
        try:
            for n in ["tomato", "cheese_ore", "dough"]:
                self.icons[n.replace("_ore","")] = pygame.image.load(f"assets/{n}.png").convert_alpha()
            for r in RECIPES:
                img = pygame.image.load(r.image).convert_alpha()
                self.icons[r.image] = pygame.transform.scale(img, (96, 96))
                self.icons[r.image + "_s"] = pygame.transform.scale(img, (40, 40))
        except: pass
        self.cpos = pygame.Vector2(30, settings.SCREEN_HEIGHT - 190)
        self.opos = pygame.Vector2(settings.SCREEN_WIDTH//2-400, settings.SCREEN_HEIGHT//2-220)
        self.pos = pygame.Vector2(self.cpos)
        self.target = self.cpos

    def toggle(self):
        self.is_open = not self.is_open
        self.target = self.opos if self.is_open else self.cpos

    def update(self, dt):
        self.pos += (self.target - self.pos) * 0.12
        self.timer += dt * 5

    def handle_input(self, event, p, om):
        if not self.is_open: return None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT: self.idx = (self.idx - 1) % 3
            elif event.key == pygame.K_RIGHT: self.idx = (self.idx + 1) % 3
            elif event.key == pygame.K_e:
                res = om.complete_order(self.idx, p.inventory)
                self.toggle()
                return res
        return None

    def draw(self, surf, inv, om):
        bw, bh = (800, 420) if self.is_open else (360, 160)
        rect = pygame.Rect(self.pos.x, self.pos.y, bw, bh)
        bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(bg, (30,35,50,235), (0,0,bw,bh), border_radius=15)
        surf.blit(bg, rect)
        pygame.draw.rect(surf, (100,110,140), rect, 2, border_radius=15)
        
        if self.is_open:
            t = self.title_f.render("FOUR À PIZZA - COMMANDES EN COURS", True, (255,215,100))
            surf.blit(t, (rect.x + 30, rect.y + 20))
            
        box_w, box_h = (230, 300) if self.is_open else (105, 120)
        sx, sy = rect.x + (40 if self.is_open else 20), rect.y + (80 if self.is_open else 25)
        
        for i, r in enumerate(om.active_orders):
            br = pygame.Rect(sx + i*(box_w+(20 if self.is_open else 10)), sy, box_w, box_h)
            pygame.draw.rect(surf, (40,45,60) if not r else ((60,65,85) if (self.is_open and i==self.idx) else (50,55,75)), br, border_radius=10)
            if self.is_open and i==self.idx:
                v = 2 + abs(int(math.sin(self.timer)*4))
                pygame.draw.rect(surf, (0,200,255), br.inflate(v,v), 3, border_radius=10)
            
            if not r:
                txt = self.small_f.render("EN ATTENTE..." if self.is_open else "VIDE", True, (80,85,110))
                surf.blit(txt, (br.centerx-txt.get_width()//2, br.centery-txt.get_height()//2))
                continue
            
            p_img = self.icons.get(r.image if self.is_open else r.image+"_s")
            iy = br.y + (20 if self.is_open else 10)
            if p_img: surf.blit(p_img, (br.centerx-p_img.get_width()//2, iy))
            
            ings = [ing for ing in ["dough", "tomato", "cheese"] if r.ingredients.get(ing, 0) > 0]
            iscl, ispc = (48, 58) if self.is_open else (32, 38)
            iy_ing = iy + (140 if self.is_open else 55)
            curr_x = br.centerx - (len(ings)*ispc - (ispc-iscl))//2
            
            for ing in ings:
                if ing in self.icons:
                    icon = pygame.transform.scale(self.icons[ing], (iscl, iscl))
                    surf.blit(icon, (curr_x, iy_ing))
                    cnt = f"{inv.counts[ing]}/{r.ingredients[ing]}" if self.is_open else str(r.ingredients[ing])
                    ts = (self.num_f if self.is_open else self.small_f).render(cnt, True, (100,255,100) if inv.counts[ing]>=r.ingredients[ing] else (255,100,100))
                    tw, th = ts.get_size()
                    tr = pygame.Rect(curr_x + iscl - tw - 4, iy_ing + iscl - th - 2, tw + 6, th + 4)
                    ns = pygame.Surface(tr.size, pygame.SRCALPHA)
                    pygame.draw.rect(ns, (20,25,40,160), (0,0,tr.w,tr.h), border_radius=4)
                    surf.blit(ns, tr.topleft)
                    pygame.draw.rect(surf, (80,90,110), tr, 1, border_radius=4)
                    surf.blit(ts, (tr.centerx-tw//2, tr.centery-th//2))
                curr_x += ispc
            
            if self.is_open and inv.has_ingredients(r.ingredients):
                pygame.draw.rect(surf, (255,180,0), (br.x, br.bottom-40, box_w, 40), border_radius=10)
                ct = self.small_f.render("VALIDER COMMANDE !", True, (0,0,0))
                surf.blit(ct, (br.centerx-ct.get_width()//2, br.bottom-30))
        
        if self.is_open:
            ax = sx + self.idx*(box_w+20) + box_w//2
            ap = [(ax-20, sy-45+math.sin(self.timer*2)*5), (ax+20, sy-45+math.sin(self.timer*2)*5), (ax, sy-20+math.sin(self.timer*2)*5)]
            pygame.draw.polygon(surf, (255,230,0), ap)
            pygame.draw.polygon(surf, (255,255,255), ap, 2)
