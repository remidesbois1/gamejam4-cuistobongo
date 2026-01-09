import pygame
import pygame_gui
import settings

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.manager = pygame_gui.UIManager((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), 'theme.json')
        
        self.play_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((settings.SCREEN_WIDTH // 2 - 100, settings.SCREEN_HEIGHT // 2 - 50), (200, 50)),
            text='PLAY',
            manager=self.manager
        )
        
        self.quit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((settings.SCREEN_WIDTH // 2 - 100, settings.SCREEN_HEIGHT // 2 + 20), (200, 50)),
            text='QUIT',
            manager=self.manager
        )
        
        # Title label
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((settings.SCREEN_WIDTH // 2 - 200, settings.SCREEN_HEIGHT // 2 - 150), (400, 80)),
            text='PANDA DIMENSIONS',
            manager=self.manager,
            object_id='#main_title'
        )

    def handle_events(self, event):
        self.manager.process_events(event)
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.play_button:
                return "START"
            if event.ui_element == self.quit_button:
                return "QUIT"
        return None

    def update(self, time_delta):
        self.manager.update(time_delta)

    def draw(self):
        self.screen.fill(settings.BLACK)
        self.manager.draw_ui(self.screen)
