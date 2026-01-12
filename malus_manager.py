import pygame
import random
from enemy import Squid, TomatoEnemy

class Malus:
    def __init__(self, name, description, func, icon_path):
        self.name = name
        self.description = description
        self.func = func
        try: self.icon = pygame.transform.scale(pygame.image.load(icon_path).convert_alpha(), (128, 128))
        except: self.icon = None
    
    def apply(self, world):
        self.func(world)

class MalusManager:
    def __init__(self, world):
        self.world = world
        self.current_malus = None
        self.maluses = [
            Malus("Invasion Gluante", "Des calamars ? Ici ?", self.malus_squid_invasion, "assets/malus_squid.png"),
            Malus("Cuisine dans l'Inconnu", "Comment s'est il retrouvé là ?", self.malus_oven_dimension, "assets/malus_oven.png"),
            Malus("Calamars Gourmands", "Yamete !", self.malus_giant_squids, "assets/malus_giant.png"),
            Malus("Tomates Perdues", "Les récoltes dans l'Upside Down !", self.malus_alien_tomatoes, "assets/malus_tomato.png"),
            Malus("Objets Trouillards", "Je pue ou quoi ?", self.malus_fleeing_items, "assets/malus_run.png"),
            Malus("Portails Pompettes", "Ils n'auraient pas dû absorber cette bouteille de Jack !", self.malus_moving_portals, "assets/malus_portal.png")
        ]
    
    def new_round(self, malus=None):
        self.world.oven.dim = 1
        self.world.items_flee = False
        
        # Reset Portals
        for p in self.world.portals: p.moving = False
        
        # Reset Tomatoes to dim 1
        for en in self.world.enemy_manager.enemies:
            if isinstance(en, TomatoEnemy): en.dim = 1

        if malus == "NO_MALUS":
            self.current_malus = None
            return
            
        if malus:
            self.current_malus = malus
        else:
            self.current_malus = random.choice(self.maluses)
        
        self.current_malus.apply(self.world)
    
    def malus_squid_invasion(self, world):
        w, h = world.map.width, world.map.height
        for _ in range(5):
            for _ in range(50):
                ex, ey = random.uniform(300, w - 300), random.uniform(300, h - 300)
                if world.is_safe(ex, ey, 100):
                    world.enemy_manager.enemies.append(Squid(ex, ey, dim=1))
                    break

    def malus_oven_dimension(self, world):
        world.oven.dim = 0
    
    def malus_giant_squids(self, world):
        world.enemy_manager.enemies = [e for e in world.enemy_manager.enemies if not isinstance(e, Squid)]
        w, h = world.map.width, world.map.height
        for _ in range(8):
            for _ in range(50):
                ex, ey = random.uniform(300, w - 300), random.uniform(300, h - 300)
                if world.is_safe(ex, ey, 200):
                    world.enemy_manager.enemies.append(Squid(ex, ey, giant=True))
                    break

    def malus_alien_tomatoes(self, world):
        for en in world.enemy_manager.enemies:
            if isinstance(en, TomatoEnemy): en.dim = 0

    def malus_fleeing_items(self, world):
        world.items_flee = True

    def malus_moving_portals(self, world):
        for p in world.portals: p.moving = True
