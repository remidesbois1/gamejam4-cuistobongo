import pygame
import random
import math
import settings
from item import Tomato, CheeseOre
from portal import Portal

class WorldManager:
    def __init__(self, map_instance):
        self.map = map_instance
        self.current_dim = 0 # 0: Cheese, 1: Tomato
        self.dim_names = ["DIMENSION FROMAGE", "DIMENSION TOMATE"]
        
        # Spawn Portals
        self.portals = [
            Portal(settings.MAP_WIDTH // 4 - 64, settings.MAP_HEIGHT // 4 - 64),
            Portal(3 * settings.MAP_WIDTH // 4 - 64, settings.MAP_HEIGHT // 4 - 64),
            Portal(settings.MAP_WIDTH // 4 - 64, 3 * settings.MAP_HEIGHT // 4 - 64),
            Portal(3 * settings.MAP_WIDTH // 4 - 64, 3 * settings.MAP_HEIGHT // 4 - 64)
        ]
        
        # Spawn items avoiding portals
        self.tomatoes = []
        self.cheese_ores = []
        self.spawn_collectibles()
        
        self.dim_switch_cooldown = 0

    def spawn_collectibles(self):
        min_dist_to_portal = 200
        
        # Spawn tomatoes
        count = 0
        while count < 20:
            rx = random.randint(0, settings.MAP_WIDTH - 32)
            ry = random.randint(0, settings.MAP_HEIGHT - 32)
            if self.is_far_from_portals(rx, ry, min_dist_to_portal):
                self.tomatoes.append(Tomato(rx, ry))
                count += 1
                
        # Spawn cheese ores
        count = 0
        while count < 10:
            rx = random.randint(0, settings.MAP_WIDTH - 48)
            ry = random.randint(0, settings.MAP_HEIGHT - 48)
            if self.is_far_from_portals(rx, ry, min_dist_to_portal):
                self.cheese_ores.append(CheeseOre(rx, ry))
                count += 1

    def is_far_from_portals(self, x, y, min_dist):
        for portal in self.portals:
            dist = math.hypot(x - portal.rect.centerx, y - portal.rect.centery)
            if dist < min_dist:
                return False
        return True

    def update(self, player_rect):
        if self.dim_switch_cooldown > 0:
            self.dim_switch_cooldown -= 1
        else:
            for portal in self.portals:
                if player_rect.colliderect(portal.rect):
                    self.current_dim = 1 - self.current_dim
                    self.dim_switch_cooldown = 60
                    return True # Dimension switched
        return False

    def draw(self, surface, offset_x, offset_y):
        # Draw map
        self.map.draw(surface, offset_x, offset_y, self.current_dim)
        
        # Draw collectibles for current dimension
        items_to_draw = self.cheese_ores if self.current_dim == 0 else self.tomatoes
        for item in items_to_draw:
            item.draw(surface, offset_x, offset_y)
            
        # Draw portals
        for portal in self.portals:
            portal.draw(surface, offset_x, offset_y)
