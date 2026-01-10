class Inventory:
    def __init__(self, cap=2):
        self.cap, self.counts = cap, {"cheese": 0, "tomato": 0, "dough": 0}

    def add_item(self, t):
        if self.counts[t] < self.cap:
            self.counts[t] += 1
            return True
        return False

    def is_full(self, t): return self.counts[t] >= self.cap

    def has_ingredients(self, ings):
        return all(self.counts.get(k, 0) >= v for k, v in ings.items())

    def remove_ingredients(self, ings):
        if self.has_ingredients(ings):
            for k, v in ings.items(): self.counts[k] -= v
            return True
        return False
