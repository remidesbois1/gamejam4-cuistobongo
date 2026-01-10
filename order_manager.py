import random
from recipe import RECIPES

class Order:
    def __init__(self, recipe, time_mult=1.0):
        self.recipe, self.max_time = recipe, recipe.time_limit * time_mult
        self.timer = self.max_time

class OrderManager:
    def __init__(self, max_slots=3):
        self.max_slots, self.time_mult = max_slots, 1.0
        self.reset_orders()

    def reset_orders(self):
        self.active_orders = [None] * self.max_slots
        self.active_orders[0] = Order(random.choice(RECIPES), self.time_mult)
        self.spawn_timer = 0

    def update(self, dt):
        score_change = 0
        for i in range(len(self.active_orders)):
            o = self.active_orders[i]
            if o:
                o.timer -= dt
                if o.timer <= 0:
                    score_change, self.active_orders[i] = score_change - int(o.recipe.points * 0.5), None
        if None in self.active_orders:
            self.spawn_timer += dt
            if self.spawn_timer >= 5.0:
                self.spawn_timer = 0
                for i in range(len(self.active_orders)):
                    if self.active_orders[i] is None:
                        self.active_orders[i] = Order(random.choice(RECIPES), self.time_mult)
                        break
        return score_change

    def complete_order(self, idx, inv):
        o = self.active_orders[idx]
        if o and inv.remove_ingredients(o.recipe.ingredients):
            points, self.active_orders[idx] = int(o.recipe.points * max(0.5, o.timer / o.max_time)), None
            return points
        return 0
