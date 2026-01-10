class Recette:
    def __init__(self, nom, ingredients, points, image):
        self.nom, self.ingredients, self.points, self.image = nom, ingredients, points, image

RECIPES = [
    Recette("Pizza Margherita", {"dough": 1, "tomato": 1, "cheese": 1}, 100, "assets/pizza_marguerita.png"),
    Recette("Pizza Vide", {"dough": 1, "tomato": 0, "cheese": 0}, 50, "assets/pizza_vide.png"),
    Recette("Pizza Tomate", {"dough": 1, "tomato": 2, "cheese": 0}, 80, "assets/pizza_tomate.png"),
    Recette("Pizza Double Fromage", {"dough": 1, "tomato": 0, "cheese": 2}, 120, "assets/pizza_fromage.png")
]
