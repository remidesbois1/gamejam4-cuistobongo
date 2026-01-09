from item import Item

class Portal(Item):
    def __init__(self, x, y):
        # Portals are now larger (128x128)
        super().__init__(x, y, "assets/portal.png", size=128)
