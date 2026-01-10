import pygame, pygame_gui, settings

class Menu:
    def __init__(self, screen):
        self.screen, self.manager = screen, pygame_gui.UIManager((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), 'theme.json')
        self.panel = pygame_gui.elements.UIPanel(pygame.Rect((settings.SCREEN_WIDTH//2-300, settings.SCREEN_HEIGHT//2-200), (600, 400)), manager=self.manager, object_id='#main_panel')
        pygame_gui.elements.UILabel(pygame.Rect((0, 40), (600, 80)), 'PIZZA', self.manager, self.panel, object_id='#main_title')
        pygame_gui.elements.UILabel(pygame.Rect((0, 110), (600, 30)), "GameJam4", self.manager, self.panel, object_id='#sub_title')
        self.play = pygame_gui.elements.UIButton(pygame.Rect((200, 190), (200, 50)), 'COMMENCER', self.manager, self.panel, object_id='#play_button')
        self.quit = pygame_gui.elements.UIButton(pygame.Rect((200, 260), (200, 50)), 'QUITTER', self.manager, self.panel, object_id='#quit_button')

    def handle_events(self, e):
        self.manager.process_events(e)
        if e.type == pygame_gui.UI_BUTTON_PRESSED:
            if e.ui_element == self.play: return "START"
            if e.ui_element == self.quit: return "QUIT"
        return None

    def update(self, dt): self.manager.update(dt)
    def draw(self):
        self.screen.fill((15, 15, 20))
        self.manager.draw_ui(self.screen)
