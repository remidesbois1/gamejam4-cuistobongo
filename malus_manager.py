import random
from enemy import Squid

class Malus:
    def __init__(self, name, description, func):
        self.name = name
        self.description = description
        self.func = func
    
    def apply(self, world):
        self.func(world)

class MalusManager:
    def __init__(self, world):
        self.world = world
        self.current_malus = None
        self.maluses = [
            Malus("Invasion Gluante", "Des calamars ? Ici ?", self.malus_squid_invasion)
        ]
    
    def new_round(self):
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
