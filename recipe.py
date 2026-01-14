class Recette:
    def __init__(self, nom, ingredients, points, image, time_limit):
        self.nom, self.ingredients, self.points, self.image, self.time_limit = nom, ingredients, points, image, time_limit

RECIPES = [
    Recette("Pizza Margherita", {"dough": 1, "tomato": 1, "cheese": 1}, 100, "assets/pizza_marguerita.png", 50),
    Recette("Pizza Vide", {"dough": 1, "tomato": 0, "cheese": 0}, 50, "assets/pizza_vide.png", 30),
    Recette("Pizza Tomate", {"dough": 1, "tomato": 2, "cheese": 0}, 100, "assets/pizza_tomate.png", 50),
    Recette("Pizza Double Fromage", {"dough": 1, "tomato": 0, "cheese": 2}, 80, "assets/pizza_fromage.png", 40)
]
