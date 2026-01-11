import settings, random

class Camera:
    def __init__(self, mw, mh):
        self.offset_x, self.offset_y, self.mw, self.mh = 0, 0, mw, mh
        self.shake_duration = 0
        self.shake_intensity = 0

    def start_shake(self, intensity, duration):
        self.shake_intensity = intensity
        self.shake_duration = duration

    def update(self, rect, dt=0):
        self.offset_x = max(0, min(rect.centerx - settings.SCREEN_WIDTH//2, self.mw - settings.SCREEN_WIDTH))
        self.offset_y = max(0, min(rect.centery - settings.SCREEN_HEIGHT//2, self.mh - settings.SCREEN_HEIGHT))
        
        if self.shake_duration > 0:
            self.shake_duration -= dt
            ox = random.uniform(-self.shake_intensity, self.shake_intensity)
            oy = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.offset_x += ox
            self.offset_y += oy
            if self.shake_duration <= 0:
                self.shake_duration = 0
