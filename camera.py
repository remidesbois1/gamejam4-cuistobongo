import settings

class Camera:
    def __init__(self, mw, mh):
        self.offset_x, self.offset_y, self.mw, self.mh = 0, 0, mw, mh

    def update(self, rect):
        self.offset_x = max(0, min(rect.centerx - settings.SCREEN_WIDTH//2, self.mw - settings.SCREEN_WIDTH))
        self.offset_y = max(0, min(rect.centery - settings.SCREEN_HEIGHT//2, self.mh - settings.SCREEN_HEIGHT))
