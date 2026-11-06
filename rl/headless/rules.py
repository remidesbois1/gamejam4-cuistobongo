"""Gameplay constants of Cuisto Bongo, without pygame.

Values copied from ``settings.py`` and from the literals of the game classes
(``player.py``, ``enemy.py``, ``world.py``...). ``tests/test_headless_parity.py``
replays the real game against the headless engine, so any drift fails there;
``tests/test_rules.py`` compares the values that ``settings.py`` defines.
"""

import math

DT = 1.0 / 60  # one tick of the 60 FPS game loop

MAP_W, MAP_H = 5120, 3200

# Player
PLAYER_SIZE = 80
PLAYER_SPEED = 400
PLAYER_HP = 50
PLAYER_INV_TIME = 1
DASH_SPEED = 1500
DASH_TIME = 0.2
DASH_INV_TIME = 0.4
SPAWN_X = MAP_W // 2 + PLAYER_SIZE
SPAWN_Y = MAP_H // 2 - PLAYER_SIZE // 2
INVENTORY_CAP = 3

# Ingredients (index order used everywhere in rl/)
DOUGH, TOMATO, CHEESE = 0, 1, 2
INGREDIENTS = ("dough", "tomato", "cheese")
DROP_SIZE = 40

# Weapons (roulette order)
DRUM, PAN, SAX = 0, 1, 2
WEAPONS = ("drum_weapon", "pan_weapon", "sax_weapon")
CD_LIMIT = 0.4
DRUM_RADIUS, DRUM_ENEMY_DAMAGE, DRUM_RES_DAMAGE = 200, 10, 1
DASH_RADIUS, DASH_ENEMY_DAMAGE, DASH_RES_DAMAGE = 100, 20, 2
SLOW_WEAPON_CD_FACTOR, SLOW_WEAPON_CD_MIN = 2.5, 0.2
NOTE_SPEED, NOTE_TIME = 450, 0.6
NOTE_RADIUS, NOTE_ENEMY_DAMAGE, NOTE_RES_DAMAGE = 180, 35, 3

# Resources: (kind, clusters, per cluster, min distance, w, h, hp, ingredient)
TREE, CHEESE_ORE = 0, 1
RESOURCE_TYPES = (
    (TREE, 25, 4, 6, 80, 120, 4, DOUGH),
    (CHEESE_ORE, 35, 3, 5, 72, 72, 3, CHEESE),
)
MAX_RESOURCES = sum(t[1] * t[2] for t in RESOURCE_TYPES)  # 205
HIT_COOLDOWN = 0.2

# Enemies
SQUID, TOMATO_ENEMY = 0, 1
SQUID_SIZE, SQUID_HP, GIANT_FACTOR, GIANT_HP_FACTOR = 64, 50, 3, 4.5
SQUID_SHOOT_DIST, SQUID_SHOOT_CD = 500, 2.0
SQUID_SEP_DIST, SQUID_SEP_FORCE, SQUID_SEP_GAIN = 80, 200, 50
SQUID_PORTAL_FLEE_DIST, SQUID_FLEE_SPEED = 150, 150
SQUID_NEAR, SQUID_FAR, SQUID_AWAY_SPEED, SQUID_CLOSER_SPEED, SQUID_WANDER_SPEED = 250, 450, 150, 120, 100
TOMATO_SIZE, TOMATO_HP, TOMATO_ATTACK_DIST = 54, 30, 220
TOMATO_SEP_DIST, TOMATO_SEP_FORCE = 50, 100
TOMATO_JUMP_SPEED, TOMATO_ROLL_SPEED = 120, 320
CONTACT_DAMAGE = 5
BASE_SQUIDS, BASE_TOMATOES = 15, 28

# Enemy states
WANDER, ADJUST = 0, 1
IDLE, JUMP_PREP, JUMP, LAND, CHARGE_PREP, ROLLING = 0, 1, 2, 3, 4, 5

# Projectiles
PROJECTILE_SIZE, PROJECTILE_SPEED, PROJECTILE_LIFETIME, PROJECTILE_DAMAGE = 48, 350, 2.5, 10

# Oven and portals
OVEN_X, OVEN_Y, OVEN_W, OVEN_H = MAP_W // 2 - 60, MAP_H // 2 - 60, 130, 160
OVEN_CX, OVEN_CY = OVEN_X + OVEN_W // 2, OVEN_Y + OVEN_H // 2
OVEN_ACTIVE_DIST = 180
OVEN_SAFE_ZONE_RADIUS = 270
OVEN_ENEMY_PUSH_RADIUS, OVEN_ENEMY_PUSH_SPEED = OVEN_SAFE_ZONE_RADIUS + 15, 500
OVEN_PROJECTILE_RADIUS = OVEN_SAFE_ZONE_RADIUS + 20
PORTAL_SIZE = 128
PORTAL_HITBOX_SHRINK = 64
PORTAL_POSITIONS = ((MAP_W // 2 - 800, MAP_H // 2 - 600), (MAP_W // 2 + 800, MAP_H // 2 - 600),
                    (MAP_W // 2 - 800, MAP_H // 2 + 600), (MAP_W // 2 + 800, MAP_H // 2 + 600))
PORTAL_SAFE_DIST, OVEN_SAFE_DIST = 220, 250
PORTAL_MIN, PORTAL_MAX_X, PORTAL_MAX_Y = 100, MAP_W - 228, MAP_H - 228
PORTAL_LERP = 3

# Orders: (name, (dough, tomato, cheese), points, time limit)
RECIPES = (
    ("Pizza Margherita", (1, 1, 1), 100, 50),
    ("Pizza Vide", (1, 0, 0), 50, 30),
    ("Pizza Tomate", (1, 2, 0), 100, 50),
    ("Pizza Double Fromage", (1, 0, 2), 80, 40),
)
ORDER_SLOTS = 3
ORDER_SPAWN_TIME = 3.5

# Waves and shop
WAVE_DURATION = 105
SHOP_DURATION = 15
INITIAL_PIZZA_GOAL, PIZZA_GOAL_INCREMENT, PIZZA_GOAL_MAX = 3, 2, 10
DEATH_PENALTY_TIME = 30
SPEED, CAP, ATK_SPEED, HEALTH, TIME = 0, 1, 2, 3, 4
UPGRADES = (("speed", 25), ("cap", 1), ("atk_speed", 0.05), ("health", 5), ("time", 0.1))
UPGRADE_COST, UPGRADE_COST_STEP, UPGRADE_COST_MAX = 2, 1, 10
MIN_CD_LIMIT = 0.1
SHOP_CARDS = 3

# Malus / bonus (roulette order)
SQUID_INVASION, OVEN_DIMENSION, GIANT_SQUIDS, ALIEN_TOMATOES, FLEEING_ITEMS, MOVING_PORTALS = range(6)
MALUSES = ("Invasion Gluante", "Cuisine dans l'Inconnu", "Calamars Gourmands", "Tomates Perdues",
           "Objets Trouillards", "Portails Pompettes")
INVASION_SQUIDS, GIANT_SQUID_COUNT = 5, 8
DROP_FLEE_DIST, DROP_FLEE_SPEED = 500, 90
BOMBS, COMPASS, PILLS = 0, 1, 2
BONUSES = ("Bombes de l'Abbaye", "Cinquième Sens", "Here we go !")
BOMBS_COUNT_MIN, BOMBS_COUNT_MAX, BOMB_SIZE, BOMB_FUSE, BOMB_RADIUS = 6, 8, 48, 4.0, 300
PILL_COUNT_MIN, PILL_COUNT_MAX, PILL_SIZE = 5, 8, 32
PILL_DURATION_TIME, PILL_SPEED_MULTI, PILL_ATTACK_SPEED_MULTI = 15, 1.5, 2.0
SPAWN_MARGIN = 300
SPAWN_TRIES = 50

# Roulette slot animation (ui.RouletteSlot)
ROULETTE_SPIN_MIN, ROULETTE_SPIN_MAX = 1.5, 2.5
ROULETTE_SPEED, ROULETTE_SLOWDOWN, ROULETTE_STOP_SPEED = 0.05, 1.2, 0.4

TAU = math.pi * 2
