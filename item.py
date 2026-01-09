import pygame
import settings

class Item:
    def __init__(self, x, y, image_path, size=32):
        self.rect = pygame.Rect(x, y, size, size)
        self.image_path = image_path
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (size, size))
        except pygame.error:
            self.image = None

    def draw(self, surface, offset_x, offset_y):
        draw_rect = self.rect.copy()
        draw_rect.x -= offset_x
        draw_rect.y -= offset_y
        
        # Only draw if on screen
        if -self.rect.width < draw_rect.x < settings.SCREEN_WIDTH and \
           -self.rect.height < draw_rect.y < settings.SCREEN_HEIGHT:
            if self.image:
                surface.blit(self.image, draw_rect)
            else:
                # Fallback colors
                color = (255, 0, 0) if "tomato" in self.image_path else (255, 255, 0)
                pygame.draw.rect(surface, color, draw_rect)

class Tomato(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/tomato.png", size=32)

class CheeseOre(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/cheese_ore.png", size=48)
