import pygame

# Graphics
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
FPS = 60
TILE_SIZE = 40
FONT_NAME = "assets/Handpixies.ttf"
MUSIC_VOLUME = 0.3
MENU_OFFSET_X = 327
MENU_OFFSET_Y = 120

# Colors
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
PLAYER_COLOR = (50, 150, 255)
MENU_TEXT_COLOR = (255, 255, 255)
MENU_HL_COLOR = (255, 215, 0)
UI_BG_COLOR = (30, 35, 50)
UI_BORDER_COLOR = (100, 110, 140)

# Map
MAP_WIDTH = 5120
MAP_HEIGHT = 3200

# Player
PLAYER_SIZE = 80
PLAYER_SPEED = 400
PLAYER_HP = 50
PLAYER_DASH_SPEED = 1500
PLAYER_DASH_TIME = 0.2
PLAYER_DASH_INV_TIME = 0.4
PLAYER_INV_TIME = 1

# Enemies
SQUID_SIZE = 64
SQUID_HP = 50
SQUID_SHOOT_DIST = 500
PROJECTILE_SPEED = 350
TOMATO_SIZE = 54
TOMATO_HP = 30
TOMATO_ATTACK_DIST = 220
PROJECTILE_SIZE = 48
PROJECTILE_LIFETIME = 2.5

# Game Logic
WAVE_DURATION = 105
SHOP_DURATION = 15
INITIAL_PIZZA_GOAL = 3
PIZZA_GOAL_INCREMENT = 2
UPGRADE_COST = 2
DEATH_PENALTY_TIME = 30
DEATH_PIZZA_PENALTY_DIVISOR = 1
DEATH_ANIMATION_DURATION = 7.0
DEATH_MSG_FLY_SPEED = 1.5
DEATH_DRAIN_SPEED = 1.5
OVEN_SAFE_ZONE_RADIUS = 270
ORDER_SPAWN_TIME = 3.5
MUSIC_SPEEDUP_TIME = 30
MUSIC_SPEED_FACTOR = 1.4
BOMBS_COUNT_MIN = 6
BOMBS_COUNT_MAX = 8
PILL_COUNT_MIN = 5
PILL_COUNT_MAX = 8
PILL_DURATION_TIME = 15
PILL_SPEED_MULTI = 1.5
PILL_ATTACK_SPEED_MULTI = 2.0

# Texts
TEXT_WAVE = "VAGUE"
TEXT_SCORE = "SCORE"
TEXT_WAITING = "EN ATTENTE..."
TEXT_EMPTY = "VIDE"
TEXT_VALIDATE = "VALIDER !"
TEXT_OVEN_TITLE = "FOUR À PIZZA"
TEXT_SHOP_TITLE = "PAUSE CUISINE - AMÉLIORATIONS"
TEXT_SKIP_BTN = "PASSER >"
TEXT_SHOP_RESUME = "Reprise dans: {}s"
TEXT_SHOP_BUY = "Appuyer sur E ou ESPACE"
TEXT_GAME_OVER = "GAME OVER"
TEXT_RETURN_MENU = "PRESS ESPACE TO RETURN TO MENU"

# Tutorial
TUTORIAL_TEXTS = {
    1: [
        "Bienvenue ! Ici, les roches et les arbres sont incassables ! Allez dans l'autre dimension en traversant un portail.",
        "Cassez un Arbre à Pâte et un crystal de fromage en jouant de votre instrument (E ou Espace)."
    ],
    2: [
        "Bravo ! Revenez maintenant dans le monde normal. Le but du jeu est de cuisiner le plus de pizzas possible.",
        "Interagissez avec le four (E ou Espace) et cuisinez une Pizza Vide avant que le temps ne s'écoule."
    ],
    3: [
        "Un monstre ! Utilisez le Saxophone (E/Espace) pour attaquer. Si vous tombez à court de PV, vous perdrez tout vos items, et vous serez envoyé 20 secondes dans le futur.",
        "Tuez des tomates sauvages pour en récupérer et cuisinez une Pizza Tomate avant que le temps ne s'écoule."
    ],
    4: [
        "Utilisez la Flûte de Pan pour aller plus vite. Mais celle-ci est plus difficile à jouer.",
        "Fabriquez une Pizza Margherita, en partie normale, vous avez un quota de pizza à atteindre par vague, si il n'est pas atteint, la partie s'arrête."
    ],
    5: [
        "Fabriquez 3 pizzas double fromage. Votre sac à dos est limité à 3x chaque ingrédient, jouez stratégiquement.",
        "Votre capacité pourra être augmentée au fur et à mesure de la partie."
    ]
}

# Colors
CLR_UI_PANEL = (30, 35, 50)
CLR_UI_BORDER = (100, 110, 140)
CLR_TEXT_MAIN = (255, 255, 255)
CLR_TEXT_GOLD = (255, 215, 100)
CLR_TEXT_CREAM = (255, 230, 200)
CLR_BTN_RED = (150, 50, 50)
CLR_BTN_RED_HOVER = (200, 70, 70)
CLR_CARD_BG = (50, 55, 75)
CLR_CARD_ACTIVE = (70, 75, 100)
CLR_VALID_GREEN = (0, 180, 0)
CLR_INVALID_RED = (220, 0, 0)
CLR_PRICE_GREEN = (100, 255, 100)
CLR_PRICE_RED = (255, 100, 100)

# Upgrade Config
UPGRADE_DEFS = {
    "speed": {"name": "Vitesse", "desc": "+25 Vitesse", "cost": 2, "val": 25},
    "cap": {"name": "Sac à dos", "desc": "+1 Capacité", "cost": 2, "val": 1},
    "atk_speed": {"name": "Vitesse attaque", "desc": "-0.05s Recharge", "cost": 2, "val": 0.05},
    "health": {"name": "Vie", "desc": "+5 PV Max", "cost": 2, "val": 5},
    "time": {"name": "Patience", "desc": "+10% Temps", "cost": 2, "val": 0.1},
}

# Controls
KEYS_UP = [pygame.K_UP, pygame.K_z]
KEYS_DOWN = [pygame.K_DOWN, pygame.K_s]
KEYS_LEFT = [pygame.K_LEFT, pygame.K_q]
KEYS_RIGHT = [pygame.K_RIGHT, pygame.K_d]
KEYS_VALIDATE = [pygame.K_RETURN, pygame.K_SPACE, pygame.K_e]
KEYS_CANCEL = [pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_e]
KEYS_INTERACT = [pygame.K_e, pygame.K_SPACE]
