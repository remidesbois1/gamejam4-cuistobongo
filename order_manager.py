import random
from recipe import RECIPES

class OrderManager:
    def __init__(self, max_slots=3):
        self.active_orders = [None] * max_slots
        self.active_orders[0] = random.choice(RECIPES)
        self.timer = 0

    def update(self, dt):
        if None in self.active_orders:
            self.timer += dt
            if self.timer >= 5.0:
                self.timer = 0
                for i in range(len(self.active_orders)):
                    if self.active_orders[i] is None:
                        self.active_orders[i] = random.choice(RECIPES)
                        break

    def complete_order(self, idx, inv):
        r = self.active_orders[idx]
        if r and inv.remove_ingredients(r.ingredients):
            self.active_orders[idx] = None
            return r.points
        return 0
