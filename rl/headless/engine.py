"""Cuisto Bongo without display: the rules of ``game.py`` and its managers, tick by tick.

Pure standard library (no pygame, no numpy). One ``Engine`` is one game, from
``Game.start()`` to GAME OVER, advanced by fixed 1/60 s ticks.

Fidelity contract (checked by ``tests/test_headless_parity.py`` against the
real pygame classes, same seed, every tick):

* same rules, same update order, same floating point formulas (pygame vectors
  use ``sqrt(x*x + y*y)``, ``lerp`` is ``a*(1-t) + b*t``, rects truncate floats);
* same gameplay random draws, in the same order, from ``self.rng``: a seed
  replays the same game as the real one with ``random.seed(seed)``. Draws of the
  game that only look cosmetic but sit in gameplay modules (cheese ore sprite,
  pill bobbing phase, bomb explosion hue) are consumed and kept as data.

Deliberate abstractions, documented in ``doc/rl.md``:

* the recipe menu is a direct action ``cook(slot)``: the oven must be active,
  the order present and its ingredients in the bag (otherwise the action is
  ignored); the menu then stays open until the next decision, which freezes
  the player like the real menu does;
* pressing interact next to the active oven does nothing (in the game it opens
  the recipe menu instead of attacking);
* the shop is a list of decisions ``buy(card)`` that take no game time; the
  game forces players to buy while a card is affordable, then leave;
* death (7 s animation) and the roulette (about 6 s) take no tick: the game is
  frozen during both, their outcome is computed exactly.
"""

import math
import random

from . import rules as R

DT = R.DT
PLAY, SHOP, OVER = 0, 1, 2


def colliderect(ax, ay, aw, ah, bx, by, bw, bh):
    """pygame.Rect.colliderect for non-empty rects."""
    return ax < bx + bw and ay < by + bh and ax + aw > bx and ay + ah > by


def roulette_index(spin_duration, n):
    """Final index of ui.RouletteSlot over ``n`` items, updated at 60 FPS."""
    idx, timer, speed, total, spinning = 0, 0.0, R.ROULETTE_SPEED, 0.0, True
    while True:
        if spinning:
            total += DT
            timer += DT
            if timer > speed:
                timer = 0
                idx = (idx + 1) % n
            if total > spin_duration:
                spinning, speed = False, R.ROULETTE_SPEED
        else:
            timer += DT
            if timer > speed:
                timer = 0
                idx = (idx + 1) % n
                speed *= R.ROULETTE_SLOWDOWN
                if speed > R.ROULETTE_STOP_SPEED:
                    return idx


class Player:
    __slots__ = ("x", "y", "rx", "ry", "vel", "hp", "max_hp", "inv_timer", "last_dx", "last_dy",
                 "dash_timer", "dash_vx", "dash_vy", "speed_mult", "inventory", "cap", "weapon")

    def __init__(self):
        self.x, self.y = float(R.SPAWN_X), float(R.SPAWN_Y)
        self.rx, self.ry = R.SPAWN_X, R.SPAWN_Y
        self.vel = R.PLAYER_SPEED
        self.hp = self.max_hp = R.PLAYER_HP
        self.inv_timer = 0
        self.last_dx, self.last_dy = 1.0, 0.0
        self.dash_timer = 0
        self.dash_vx = self.dash_vy = 0.0
        self.speed_mult = 1.0
        self.inventory = [0, 0, 0]
        self.cap = R.INVENTORY_CAP
        self.weapon = R.DRUM

    @property
    def cx(self):
        return self.rx + R.PLAYER_SIZE // 2

    @property
    def cy(self):
        return self.ry + R.PLAYER_SIZE // 2

    def collides(self, x, y, w, h):
        return colliderect(self.rx, self.ry, R.PLAYER_SIZE, R.PLAYER_SIZE, x, y, w, h)

    def take_damage(self, amount):
        if self.inv_timer > 0 or self.dash_timer > 0:
            return False
        if self.speed_mult > 1.1:
            amount /= 2
        self.hp -= amount
        self.inv_timer = R.PLAYER_INV_TIME
        return self.hp <= 0

    def respawn(self):
        self.hp = self.max_hp
        self.x, self.y = float(R.SPAWN_X), float(R.SPAWN_Y)
        self.rx, self.ry = R.SPAWN_X, R.SPAWN_Y
        self.inventory = [0, 0, 0]
        self.last_dx, self.last_dy = 1.0, 0.0
        self.dash_timer = 0
        self.speed_mult = 1.0

    def start_dash(self):
        dx, dy = self.last_dx, self.last_dy
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            dx, dy, length = 1.0, 0.0, 1.0
        self.dash_vx, self.dash_vy = dx / length, dy / length
        self.dash_timer = R.DASH_TIME
        self.inv_timer = R.DASH_INV_TIME

    def handle_input(self, right, left, down, up):
        if self.dash_timer > 0:
            self.dash_timer -= DT
            self.x += self.dash_vx * R.DASH_SPEED * DT
            self.y += self.dash_vy * R.DASH_SPEED * DT
            self.x = max(0, min(self.x, R.MAP_W - R.PLAYER_SIZE))
            self.y = max(0, min(self.y, R.MAP_H - R.PLAYER_SIZE))
            self.rx, self.ry = int(self.x), int(self.y)
            return
        self.inv_timer -= DT
        vx, vy = int(right) - int(left), int(down) - int(up)
        if vx or vy:
            length = math.sqrt(vx * vx + vy * vy)
            self.last_dx, self.last_dy = vx / length, vy / length
            self.x += self.last_dx * self.vel * self.speed_mult * DT
            self.y += self.last_dy * self.vel * self.speed_mult * DT
            self.x = max(0, min(self.x, R.MAP_W - 80))
            self.y = max(0, min(self.y, R.MAP_H - 80))
            self.rx, self.ry = int(self.x), int(self.y)

    def add_item(self, kind):
        if self.inventory[kind] < self.cap:
            self.inventory[kind] += 1
            return True
        return False


class Resource:
    __slots__ = ("kind", "rx", "ry", "w", "h", "hp", "max_hp", "drop", "hit_timer", "variant")

    def __init__(self, spec, x, y, variant):
        self.kind, _, _, _, self.w, self.h, self.max_hp, self.drop = spec
        self.rx, self.ry = int(x), int(y)
        self.hp = self.max_hp
        self.hit_timer = 0
        self.variant = variant

    @property
    def cx(self):
        return self.rx + self.w // 2

    @property
    def cy(self):
        return self.ry + self.h // 2

    def take_damage(self, amount, dim):
        # Every spawned resource has an Upside Down sprite: only breakable there.
        if dim == 1 or self.hit_timer > 0:
            return False
        self.hp -= amount
        self.hit_timer = R.HIT_COOLDOWN
        return self.hp <= 0


class Drop:
    """A dropped ingredient. ``dim`` only matters for drops of killed tomatoes."""

    __slots__ = ("kind", "rx", "ry", "dim")

    def __init__(self, kind, x, y, dim=1):
        self.kind, self.rx, self.ry, self.dim = kind, x, y, dim

    def flee(self, player):
        cx, cy = self.rx + R.DROP_SIZE // 2, self.ry + R.DROP_SIZE // 2
        dx, dy = cx - player.cx, cy - player.cy
        if math.sqrt(dx * dx + dy * dy) < R.DROP_FLEE_DIST:
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                fx, fy = cx + dx / length * R.DROP_FLEE_SPEED * DT, cy + dy / length * R.DROP_FLEE_SPEED * DT
                self.rx, self.ry = int(fx) - R.DROP_SIZE // 2, int(fy) - R.DROP_SIZE // 2


class Enemy:
    __slots__ = ("kind", "giant", "x", "y", "rx", "ry", "size", "hp", "max_hp", "hit_timer", "dim",
                 "shoot_cd", "move_state", "move_timer", "wx", "wy", "state", "timer", "vx", "vy")

    @property
    def cx(self):
        return self.rx + self.size // 2

    @property
    def cy(self):
        return self.ry + self.size // 2

    def take_damage(self, amount):
        if self.hit_timer > 0:
            return False
        self.hp -= amount
        self.hit_timer = R.HIT_COOLDOWN
        return self.hp <= 0


def make_squid(rng, x, y, dim=0, giant=False):
    e = Enemy()
    e.kind, e.giant = R.SQUID, giant
    e.size = R.SQUID_SIZE * (R.GIANT_FACTOR if giant else 1)
    e.rx, e.ry = int(x), int(y)
    e.x, e.y = x, y
    e.shoot_cd = rng.uniform(0, 2)
    e.move_state, e.move_timer = R.WANDER, 0
    e.wx = e.wy = 0.0
    e.hp = e.max_hp = R.SQUID_HP
    if giant:
        e.hp *= R.GIANT_HP_FACTOR
        e.max_hp *= R.GIANT_HP_FACTOR
    e.hit_timer = 0
    e.dim = dim
    e.state = e.timer = 0
    e.vx = e.vy = 0.0
    return e


def make_tomato(rng, x, y):
    e = Enemy()
    e.kind, e.giant, e.size = R.TOMATO_ENEMY, False, R.TOMATO_SIZE
    e.rx, e.ry = int(x), int(y)
    e.x, e.y = x, y
    e.hp = e.max_hp = R.TOMATO_HP
    e.hit_timer = 0
    e.state, e.timer = R.IDLE, rng.uniform(0.5, 1.5)
    e.vx = e.vy = 0.0
    e.dim = 1  # set by MalusManager.new_round before any use
    e.shoot_cd = e.move_state = e.move_timer = 0
    e.wx = e.wy = 0.0
    return e


class Projectile:
    __slots__ = ("x", "y", "rx", "ry", "size", "vx", "vy", "timer", "dim")

    def __init__(self, x, y, tx, ty, dim, big):
        self.size = R.PROJECTILE_SIZE * (3 if big else 1)
        self.rx, self.ry = x, y
        self.x, self.y = float(x), float(y)
        self.dim = dim
        dx, dy = tx - self.x, ty - self.y
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
            self.vx, self.vy = dx / length * R.PROJECTILE_SPEED, dy / length * R.PROJECTILE_SPEED
        else:
            self.vx, self.vy = 1.0, 0.0
        self.timer = 0


class Note:
    """effects.ExplodingNote of the saxophone."""

    __slots__ = ("x", "y", "dx", "dy", "timer")

    def __init__(self, x, y, dx, dy):
        self.x, self.y = float(x), float(y)
        length = math.sqrt(dx * dx + dy * dy)
        self.dx, self.dy = (dx / length, dy / length) if length > 0 else (1.0, 0.0)
        self.timer = 0


class Portal:
    __slots__ = ("x", "y", "rx", "ry", "moving", "vx", "vy", "tvx", "tvy", "move_timer")

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.rx, self.ry = x, y
        self.moving = False
        self.vx = self.vy = self.tvx = self.tvy = 0.0
        self.move_timer = 0

    @property
    def cx(self):
        return self.rx + R.PORTAL_SIZE // 2

    @property
    def cy(self):
        return self.ry + R.PORTAL_SIZE // 2

    def update(self, rng):
        if not self.moving:
            return
        self.move_timer -= DT
        if self.move_timer <= 0:
            self.move_timer = rng.uniform(0.5, 2.0)
            if rng.random() < 0.2:
                self.tvx, self.tvy = 0.0, 0.0
            else:
                angle = rng.uniform(0, R.TAU)
                speed = rng.uniform(150, 250)
                self.tvx, self.tvy = math.cos(angle) * speed, math.sin(angle) * speed
        t = DT * R.PORTAL_LERP
        self.vx = self.vx * (1 - t) + self.tvx * t
        self.vy = self.vy * (1 - t) + self.tvy * t
        self.x += self.vx * DT
        self.y += self.vy * DT
        self.x = max(R.PORTAL_MIN, min(self.x, R.PORTAL_MAX_X))
        self.y = max(R.PORTAL_MIN, min(self.y, R.PORTAL_MAX_Y))
        self.rx, self.ry = int(self.x), int(self.y)

    def reset(self, x, y):
        self.moving = False
        self.x, self.y = float(x), float(y)
        self.rx, self.ry = x, y


class Bomb:
    __slots__ = ("rx", "ry", "dim", "attached", "timer", "hue")

    def __init__(self, x, y):
        self.rx, self.ry = int(x) - R.BOMB_SIZE // 2, int(y) - R.BOMB_SIZE // 2
        self.dim = 1
        self.attached = False
        self.timer = 0
        self.hue = None


class Pill:
    __slots__ = ("rx", "ry", "phase")

    def __init__(self, x, y, phase):
        self.rx, self.ry = int(x) - R.PILL_SIZE // 2, int(y) - R.PILL_SIZE // 2
        self.phase = phase


class Order:
    __slots__ = ("recipe", "max_time", "timer")

    def __init__(self, recipe, time_mult):
        self.recipe = recipe
        self.max_time = R.RECIPES[recipe][3] * time_mult
        self.timer = self.max_time


class Events:
    """What happened since the last ``pop_events`` (rewards and statistics)."""

    FIELDS = ("ticks", "score", "pizzas", "expired", "damage", "deaths", "waves", "game_over",
              "picked", "kills", "harvested", "buys")
    __slots__ = FIELDS

    def __init__(self):
        for f in self.FIELDS:
            setattr(self, f, 0)

    def as_dict(self):
        return {f: getattr(self, f) for f in self.FIELDS}


class Engine:
    def __init__(self, seed=None):
        self.reset(seed)

    # ------------------------------------------------------------------ setup
    def reset(self, seed=None):
        """``Game.start()`` of a normal (non sandbox) game."""
        self.rng = rng = random.Random(seed)
        self.events = Events()
        self.ticks = 0
        self.orders = [None] * R.ORDER_SLOTS
        self.time_mult = 1.0
        self.spawn_timer = 0
        self._reset_orders()
        self.player = Player()
        self.last_weapon = R.DRUM
        self.last_bonus = None
        self.dim = 1
        self.portals = [Portal(x, y) for x, y in R.PORTAL_POSITIONS]
        self.oven_dim = 1
        self.oven_active = False
        self.items_flee = False
        self.res, self.res_drops = [], []
        self.enemies, self.projectiles, self.enemy_drops = [], [], []
        self.spawn()
        self.in_portal = False
        self.notes = []
        self.cd, self.cd_limit, self.cd_limit_mult = 0, R.CD_LIMIT, 1.0
        self.bombs, self.pills = [], []
        self.pill_timer = 0
        self.bonus = None
        self.upgrade_costs = [R.UPGRADE_COST] * len(R.UPGRADES)
        self.shop_cards = rng.sample(range(len(R.UPGRADES)), R.SHOP_CARDS)
        self.score, self.wave_timer, self.wave_num, self.phase = 0, R.WAVE_DURATION, 1, PLAY
        self.pizza_goal, self.round_p, self.extra = R.INITIAL_PIZZA_GOAL, 0, 0
        self.pizzas_made = 0
        self.menu_open = False
        self.malus = None
        self._new_round_malus(None)
        return self

    def _reset_orders(self):
        self.orders = [None] * R.ORDER_SLOTS
        self.orders[0] = Order(self._choice_recipe(), self.time_mult)
        self.spawn_timer = 0

    def _choice_recipe(self, rng=None):
        return (rng or self.rng).choice(range(len(R.RECIPES)))

    def _rng_for(self, owner):
        """Generator for the draws of ``owner`` during a tick (entity, ``"orders"``, ``"shop"``).

        Always ``self.rng`` (same order as the game); the vector parity test
        overrides it to feed both engines the same numbers per entity.
        """
        return self.rng

    def is_safe(self, x, y, size):
        for p in self.portals:
            if math.hypot(x - p.cx, y - p.cy) < R.PORTAL_SAFE_DIST:
                return False
        if math.hypot(x - R.OVEN_CX, y - R.OVEN_CY) < R.OVEN_SAFE_DIST:
            return False
        for r in self.res:
            if math.hypot(x - r.cx, y - r.cy) < size:
                return False
        return True

    def _random_spot(self):
        return (self.rng.uniform(R.SPAWN_MARGIN, R.MAP_W - R.SPAWN_MARGIN),
                self.rng.uniform(R.SPAWN_MARGIN, R.MAP_H - R.SPAWN_MARGIN))

    def spawn(self, extra=0):
        """WorldManager.spawn: resources, then enemies (lists and drops cleared)."""
        rng = self.rng
        self.res.clear()
        self.res_drops.clear()
        for spec in R.RESOURCE_TYPES:
            kind, clusters, per, min_dist = spec[:4]
            for _ in range(clusters):
                for _ in range(R.SPAWN_TRIES):
                    cx, cy = self._random_spot()
                    if self.is_safe(cx, cy, 150):
                        for _ in range(per):
                            for _ in range(20):
                                sang, sdist = rng.uniform(0, R.TAU), rng.uniform(0, 200)
                                tx, ty = cx + math.cos(sang) * sdist, cy + math.sin(sang) * sdist
                                if 100 < tx < R.MAP_W - 100 and 100 < ty < R.MAP_H - 100 \
                                        and self.is_safe(tx, ty, min_dist):
                                    variant = int(rng.random() >= 0.5) if kind == R.CHEESE_ORE else 0
                                    self.res.append(Resource(spec, tx, ty, variant))
                                    break
                        break
        self.enemies.clear()
        self.projectiles.clear()
        self.enemy_drops.clear()
        for _ in range(R.BASE_SQUIDS + extra):
            for _ in range(R.SPAWN_TRIES):
                ex, ey = self._random_spot()
                if self.is_safe(ex, ey, 100):
                    self.enemies.append(make_squid(rng, ex, ey))
                    break
        for _ in range(R.BASE_TOMATOES + extra):
            for _ in range(R.SPAWN_TRIES):
                ex, ey = self._random_spot()
                if self.is_safe(ex, ey, 80):
                    self.enemies.append(make_tomato(rng, ex, ey))
                    break

    def _new_round_malus(self, malus):
        """MalusManager.new_round; ``None`` is the first wave's NO_MALUS."""
        self.oven_dim = 1
        self.items_flee = False
        for portal, (x, y) in zip(self.portals, R.PORTAL_POSITIONS):
            portal.reset(x, y)
        for e in self.enemies:
            if e.kind == R.TOMATO_ENEMY:
                e.dim = 1
        self.malus = malus
        if malus == R.SQUID_INVASION:
            for _ in range(R.INVASION_SQUIDS):
                for _ in range(R.SPAWN_TRIES):
                    ex, ey = self._random_spot()
                    if self.is_safe(ex, ey, 100):
                        self.enemies.append(make_squid(self.rng, ex, ey, dim=1))
                        break
        elif malus == R.OVEN_DIMENSION:
            self.oven_dim = 0
        elif malus == R.GIANT_SQUIDS:
            self.enemies = [e for e in self.enemies if e.kind != R.SQUID]
            for _ in range(R.GIANT_SQUID_COUNT):
                for _ in range(R.SPAWN_TRIES):
                    ex, ey = self._random_spot()
                    if self.is_safe(ex, ey, 200):
                        self.enemies.append(make_squid(self.rng, ex, ey, giant=True))
                        break
        elif malus == R.ALIEN_TOMATOES:
            for e in self.enemies:
                if e.kind == R.TOMATO_ENEMY:
                    e.dim = 0
        elif malus == R.FLEEING_ITEMS:
            self.items_flee = True
        elif malus == R.MOVING_PORTALS:
            for portal in self.portals:
                portal.moving = True

    def _new_round_bonus(self, bonus):
        rng = self.rng
        self.bonus = bonus
        self.bombs.clear()
        self.pills.clear()
        self.pill_timer = 0
        if bonus == R.BOMBS:
            for _ in range(rng.randint(R.BOMBS_COUNT_MIN, R.BOMBS_COUNT_MAX)):
                for _ in range(R.SPAWN_TRIES):
                    ex, ey = self._random_spot()
                    if self.is_safe(ex, ey, 50):
                        bomb = Bomb(ex, ey)
                        bomb.dim = rng.choice([0, 1])
                        self.bombs.append(bomb)
                        break
        elif bonus == R.PILLS:
            for _ in range(rng.randint(R.PILL_COUNT_MIN, R.PILL_COUNT_MAX)):
                for _ in range(R.SPAWN_TRIES):
                    ex, ey = self._random_spot()
                    if self.is_safe(ex, ey, 50):
                        self.pills.append(Pill(ex, ey, rng.random()))
                        break

    # ----------------------------------------------------------------- combat
    def _hit_resources(self, px, py, damage, radius):
        for r in self.res[:]:
            if math.hypot(px - r.cx, py - r.cy) < radius and r.take_damage(damage, self.dim):
                self.res_drops.append(Drop(r.drop, r.rx, r.ry))
                self.res.remove(r)
                self.events.harvested += 1

    def _hit_enemies(self, px, py, damage, radius):
        dim = self.dim
        for e in self.enemies[:]:
            if e.dim != dim:
                continue
            if math.hypot(px - e.cx, py - e.cy) < radius and e.take_damage(damage):
                if e.kind == R.TOMATO_ENEMY:
                    self.enemy_drops.append(Drop(R.TOMATO, e.rx, e.ry, dim))
                self.enemies.remove(e)
                self.events.kills += 1

    def trigger_weapon(self):
        if self.cd > 0:
            return False
        p = self.player
        limit = self.cd_limit * self.cd_limit_mult
        if p.weapon == R.DRUM:
            self.cd = limit
            self._hit_resources(p.cx, p.cy, R.DRUM_RES_DAMAGE, R.DRUM_RADIUS)
            self._hit_enemies(p.cx, p.cy, R.DRUM_ENEMY_DAMAGE, R.DRUM_RADIUS)
        elif p.weapon == R.PAN:
            self.cd = max(R.SLOW_WEAPON_CD_MIN, limit * R.SLOW_WEAPON_CD_FACTOR)
            p.start_dash()
        else:
            self.cd = max(R.SLOW_WEAPON_CD_MIN, limit * R.SLOW_WEAPON_CD_FACTOR)
            self.notes.append(Note(p.cx, p.cy, p.last_dx, p.last_dy))
        return True

    # ------------------------------------------------------------- the world
    def _world_update(self):
        p = self.player
        self.cd = max(0, self.cd - DT)
        for portal in self.portals:
            portal.update(self._rng_for(portal))
        for note in self.notes[:]:
            note.timer += DT
            if note.timer < R.NOTE_TIME:
                note.x += note.dx * R.NOTE_SPEED * DT
                note.y += note.dy * R.NOTE_SPEED * DT
            else:
                self._hit_resources(note.x, note.y, R.NOTE_RES_DAMAGE, R.NOTE_RADIUS)
                self._hit_enemies(note.x, note.y, R.NOTE_ENEMY_DAMAGE, R.NOTE_RADIUS)
                self.notes.remove(note)
        if p.dash_timer > 0:
            self._hit_resources(p.cx, p.cy, R.DASH_RES_DAMAGE, R.DASH_RADIUS)
            self._hit_enemies(p.cx, p.cy, R.DASH_ENEMY_DAMAGE, R.DASH_RADIUS)

        touching = False
        for portal in self.portals:
            if p.collides(portal.rx, portal.ry, R.PORTAL_SIZE, R.PORTAL_SIZE):
                touching = True
                s = R.PORTAL_HITBOX_SHRINK // 2
                if not self.in_portal and p.collides(portal.rx + s, portal.ry + s,
                                                     R.PORTAL_SIZE - 2 * s, R.PORTAL_SIZE - 2 * s):
                    self.dim, self.in_portal = 1 - self.dim, True
                    p.inv_timer = 0.2
                    return
                break
        if not touching:
            self.in_portal = False

        if self.dim == self.oven_dim:
            dx, dy = R.OVEN_CX - p.cx, R.OVEN_CY - p.cy
            self.oven_active = math.sqrt(dx * dx + dy * dy) < R.OVEN_ACTIVE_DIST
        else:
            self.oven_active = False

        self._resources_update()
        self._enemies_update()

    def _pick(self, drops, drop):
        if self.player.add_item(drop.kind):
            drops.remove(drop)
            self.events.picked += 1

    def _resources_update(self):
        p, dim = self.player, self.dim
        for r in self.res:
            r.hit_timer = max(0, r.hit_timer - DT)
        for d in self.res_drops[:]:
            visible = (dim == 1) == (d.kind == R.TOMATO)
            if self.items_flee and visible:
                d.flee(p)
            if visible and p.collides(d.rx, d.ry, R.DROP_SIZE, R.DROP_SIZE):
                self._pick(self.res_drops, d)

    def _enemies_update(self):
        p, dim = self.player, self.dim
        pcx, pcy = p.cx, p.cy
        enemies = self.enemies
        for e in enemies:
            if e.dim == self.oven_dim:
                dx, dy = e.x - R.OVEN_CX, e.y - R.OVEN_CY
                d = math.sqrt(dx * dx + dy * dy)
                if d < R.OVEN_ENEMY_PUSH_RADIUS:
                    length = math.sqrt(dx * dx + dy * dy)
                    e.x += dx / length * R.OVEN_ENEMY_PUSH_SPEED * DT
                    e.y += dy / length * R.OVEN_ENEMY_PUSH_SPEED * DT
                    e.rx, e.ry = int(e.x), int(e.y)
            if e.kind == R.SQUID:
                self._squid_update(e, pcx, pcy, visible=dim == e.dim)
                if dim == e.dim and p.collides(e.rx, e.ry, e.size, e.size):
                    p.take_damage(R.CONTACT_DAMAGE)
            elif dim == e.dim:
                self._tomato_update(e, pcx, pcy)
                if p.collides(e.rx, e.ry, e.size, e.size):
                    p.take_damage(R.CONTACT_DAMAGE)

        for proj in self.projectiles[:]:
            proj.x += proj.vx * DT
            proj.y += proj.vy * DT
            proj.rx, proj.ry = int(proj.x), int(proj.y)
            proj.timer += DT
            if proj.timer > R.PROJECTILE_LIFETIME:
                self.projectiles.remove(proj)
                continue
            if proj.dim == self.oven_dim:
                dx, dy = proj.x - R.OVEN_CX, proj.y - R.OVEN_CY
                if math.sqrt(dx * dx + dy * dy) < R.OVEN_PROJECTILE_RADIUS:
                    self.projectiles.remove(proj)
                    continue
            if proj.dim == dim and p.collides(proj.rx, proj.ry, proj.size, proj.size):
                p.take_damage(R.PROJECTILE_DAMAGE)
                self.projectiles.remove(proj)

        for d in self.enemy_drops[:]:
            if self.items_flee and dim == d.dim:
                d.flee(p)
            if dim == d.dim and p.collides(d.rx, d.ry, R.DROP_SIZE, R.DROP_SIZE):
                self._pick(self.enemy_drops, d)

    def _separation(self, e, radius, force):
        sx = sy = 0.0
        for o in self.enemies:
            if o is not e:
                dx, dy = e.x - o.x, e.y - o.y
                d = math.sqrt(dx * dx + dy * dy)
                if d < radius:
                    length = math.sqrt(dx * dx + dy * dy)
                    if length > 0:
                        k = force / max(1, d)
                        sx += dx / length * k
                        sy += dy / length * k
        return sx, sy

    def _squid_update(self, e, pcx, pcy, visible):
        rng = self._rng_for(e)
        e.hit_timer = max(0, e.hit_timer - DT)
        sx, sy = self._separation(e, R.SQUID_SEP_DIST, R.SQUID_SEP_FORCE)

        flee = None
        mcx, mcy = e.cx, e.cy
        for portal in self.portals:
            dx, dy = mcx - portal.cx, mcy - portal.cy
            if math.sqrt(dx * dx + dy * dy) < R.SQUID_PORTAL_FLEE_DIST:
                length = math.sqrt(dx * dx + dy * dy)
                if length > 0:
                    flee = (dx / length, dy / length)
                break

        vx = vy = 0.0
        if flee:
            vx, vy = flee[0] * R.SQUID_FLEE_SPEED, flee[1] * R.SQUID_FLEE_SPEED
            e.move_state = R.WANDER
        else:
            force = not visible
            e.move_timer -= DT
            if e.move_timer <= 0:
                if e.move_state == R.ADJUST and not force:
                    e.move_state = R.WANDER
                    e.move_timer = rng.uniform(0.3, 0.8)
                    self._wander(e, rng)
                else:
                    e.move_state = R.ADJUST if not force else R.WANDER
                    e.move_timer = rng.uniform(0.5, 1.0)
                    if force:
                        self._wander(e, rng)
            if not force:
                dx, dy = pcx - e.x, pcy - e.y
                dist = math.sqrt(dx * dx + dy * dy)
                if e.move_state == R.ADJUST:
                    if dist > 0:
                        if dist < R.SQUID_NEAR:
                            vx, vy = -(dx / dist) * R.SQUID_AWAY_SPEED, -(dy / dist) * R.SQUID_AWAY_SPEED
                        elif dist > R.SQUID_FAR:
                            vx, vy = dx / dist * R.SQUID_CLOSER_SPEED, dy / dist * R.SQUID_CLOSER_SPEED
                else:
                    vx, vy = e.wx * R.SQUID_WANDER_SPEED, e.wy * R.SQUID_WANDER_SPEED
                e.shoot_cd -= DT
                if e.shoot_cd <= 0 and dist < R.SQUID_SHOOT_DIST:
                    e.shoot_cd = R.SQUID_SHOOT_CD
                    self.projectiles.append(Projectile(e.cx - 24, e.cy - 24, pcx, pcy, e.dim, e.giant))
            else:
                vx, vy = e.wx * R.SQUID_WANDER_SPEED, e.wy * R.SQUID_WANDER_SPEED
        e.x += (vx + sx * R.SQUID_SEP_GAIN) * DT
        e.y += (vy + sy * R.SQUID_SEP_GAIN) * DT
        e.rx, e.ry = int(e.x), int(e.y)

    def _wander(self, e, rng):
        wx, wy = rng.uniform(-1, 1), rng.uniform(-1, 1)
        length = math.sqrt(wx * wx + wy * wy)
        if length > 0:
            wx, wy = wx / length, wy / length
        e.wx, e.wy = wx, wy

    def _tomato_update(self, e, pcx, pcy):
        e.hit_timer = max(0, e.hit_timer - DT)
        dx, dy = pcx - e.x, pcy - e.y
        dist = math.sqrt(dx * dx + dy * dy)
        e.timer -= DT
        s = e.state
        if s == R.IDLE:
            e.vx = e.vy = 0.0
            if e.timer <= 0:
                if dist < R.TOMATO_ATTACK_DIST:
                    e.state, e.timer = R.CHARGE_PREP, 1.0
                else:
                    e.state, e.timer = R.JUMP_PREP, 0.5
        elif s == R.JUMP_PREP:
            if e.timer <= 0:
                e.state, e.timer = R.JUMP, 0.5
                angle = self._rng_for(e).uniform(0, 6.28)
                e.vx, e.vy = math.cos(angle) * R.TOMATO_JUMP_SPEED, math.sin(angle) * R.TOMATO_JUMP_SPEED
        elif s == R.JUMP:
            e.x += e.vx * DT
            e.y += e.vy * DT
            if e.timer <= 0:
                e.state, e.timer = R.LAND, 0.2
                e.vx = e.vy = 0.0
        elif s == R.LAND:
            if e.timer <= 0:
                e.state, e.timer = R.IDLE, self._rng_for(e).uniform(0.5, 1.0)
        elif s == R.CHARGE_PREP:
            if e.timer <= 0:
                e.state, e.timer = R.ROLLING, 1.5
                if dist > 0:
                    e.vx, e.vy = dx / dist * R.TOMATO_ROLL_SPEED, dy / dist * R.TOMATO_ROLL_SPEED
        elif s == R.ROLLING:
            e.x += e.vx * DT
            e.y += e.vy * DT
            if e.timer <= 0:
                e.state, e.timer = R.IDLE, 1.5
        sx, sy = self._separation(e, R.TOMATO_SEP_DIST, R.TOMATO_SEP_FORCE)
        e.x += sx * DT
        e.y += sy * DT
        e.rx, e.ry = int(e.x) - e.size // 2, int(e.y) - e.size // 2

    # ------------------------------------------------------------ the rounds
    def _orders_update(self):
        change = 0
        for i, o in enumerate(self.orders):
            if o:
                o.timer -= DT
                if o.timer <= 0:
                    change -= int(R.RECIPES[o.recipe][2])
                    self.orders[i] = None
                    self.events.expired += 1
        if None in self.orders:
            self.spawn_timer += DT
            if self.spawn_timer >= R.ORDER_SPAWN_TIME:
                self.spawn_timer = 0
                i = self.orders.index(None)
                self.orders[i] = Order(self._choice_recipe(self._rng_for("orders")), self.time_mult)
        return change

    def can_cook(self, slot):
        o = self.orders[slot]
        if not (self.phase == PLAY and self.oven_active and o):
            return False
        need = R.RECIPES[o.recipe][1]
        return all(have >= n for have, n in zip(self.player.inventory, need))

    def _cook(self, slot):
        o = self.orders[slot]
        need = R.RECIPES[o.recipe][1]
        inv = self.player.inventory
        for k in range(3):
            inv[k] -= need[k]
        points = int(R.RECIPES[o.recipe][2] * max(0.5, o.timer / o.max_time))
        self.orders[slot] = None
        self.score += points
        self.pizzas_made += 1
        self.round_p += 1
        self.events.score += points
        self.events.pizzas += 1

    def _bonus_update(self):
        p = self.player
        for bomb in self.bombs[:]:
            if not bomb.attached:
                if p.collides(bomb.rx, bomb.ry, R.BOMB_SIZE, R.BOMB_SIZE) and self.dim == bomb.dim:
                    bomb.attached = True
            else:
                bomb.timer += DT
                bomb.rx = p.cx - R.BOMB_SIZE // 2
                bomb.ry = p.ry - 10 - R.BOMB_SIZE
                if bomb.timer >= R.BOMB_FUSE:
                    self._explode(bomb)
                    self.bombs.remove(bomb)
        self.pill_timer = max(0, self.pill_timer - DT)
        for pill in self.pills[:]:
            if p.collides(pill.rx, pill.ry, R.PILL_SIZE, R.PILL_SIZE):
                self.pill_timer = R.PILL_DURATION_TIME
                self.pills.remove(pill)

    def _explode(self, bomb):
        ex, ey = bomb.rx + R.BOMB_SIZE // 2, bomb.ry + R.BOMB_SIZE // 2
        bomb.hue = self._rng_for(bomb).randint(0, 360)
        dim = self.dim
        doomed = [e for e in self.enemies
                  if math.hypot(e.cx - ex, e.cy - ey) < R.BOMB_RADIUS and e.dim == dim]
        for e in doomed:
            if e.kind == R.TOMATO_ENEMY:
                self.res_drops.append(Drop(R.TOMATO, e.rx, e.ry))
            self.enemies.remove(e)
            self.events.kills += 1
        broken = [r for r in self.res
                  if math.hypot(r.cx - ex, r.cy - ey) < R.BOMB_RADIUS and r.take_damage(100, dim)]
        for r in broken:
            self.res_drops.append(Drop(r.drop, r.rx, r.ry))
            self.res.remove(r)
            self.events.harvested += 1

    def _reset_bonus_effects(self):
        self.pill_timer = 0
        self.player.speed_mult = 1.0
        self.cd_limit_mult = 1.0

    def _die(self):
        """DYING then respawn (game.py); the 7 s animation freezes everything."""
        self.player.respawn()
        self.dim = 1
        self.wave_timer -= R.DEATH_PENALTY_TIME
        self.events.deaths += 1

    def _end_wave(self):
        self._reset_bonus_effects()
        self.menu_open = False
        if self.round_p >= self.pizza_goal:
            self.phase = SHOP
            self.wave_timer = R.SHOP_DURATION  # shown, never decremented by the game
            self._reset_orders()
            self.shop_cards = self.rng.sample(range(len(R.UPGRADES)), R.SHOP_CARDS)
            self.events.waves += 1
            if not self.can_buy():
                self._leave_shop()
        else:
            self.phase = OVER
            self.events.game_over += 1

    # ------------------------------------------------------------------- shop
    def can_buy(self, card=None):
        cards = self.shop_cards if card is None else [self.shop_cards[card]]
        return self.phase == SHOP and any(self.pizzas_made >= self.upgrade_costs[u] for u in cards)

    def buy(self, card):
        """Buy one of the three shop cards; leaves the shop when nothing is affordable."""
        if not self.can_buy(card):
            return False
        u = self.shop_cards[card]
        self.pizzas_made -= self.upgrade_costs[u]
        p = self.player
        if u == R.SPEED:
            p.vel += R.UPGRADES[u][1]
        elif u == R.CAP:
            p.cap += R.UPGRADES[u][1]
        elif u == R.ATK_SPEED:
            self.cd_limit = max(R.MIN_CD_LIMIT, self.cd_limit - R.UPGRADES[u][1])
        elif u == R.HEALTH:
            p.max_hp += R.UPGRADES[u][1]
            p.hp = min(p.hp + R.UPGRADES[u][1], p.max_hp)
        else:
            self.time_mult += R.UPGRADES[u][1]
        self.upgrade_costs[u] = min(self.upgrade_costs[u] + R.UPGRADE_COST_STEP, R.UPGRADE_COST_MAX)
        others = [k for k in range(len(R.UPGRADES)) if k not in self.shop_cards]
        if others:
            self.shop_cards[card] = self._rng_for("shop").choice(others)
        self.events.buys += 1
        if not self.can_buy():
            self._leave_shop()
        return True

    def _leave_shop(self):
        """SHOP -> ROULETTE -> next wave (game.py), with the roulette's exact outcome."""
        rng = self.rng
        maluses = [m for m in range(len(R.MALUSES)) if m != self.malus]
        weapons = [w for w in range(len(R.WEAPONS)) if w != self.last_weapon]
        bonuses = [b for b in range(len(R.BONUSES)) if b != self.last_bonus]
        spins = [rng.uniform(R.ROULETTE_SPIN_MIN, R.ROULETTE_SPIN_MAX) for _ in range(3)]
        malus = maluses[roulette_index(spins[0], len(maluses))]
        weapon = weapons[roulette_index(spins[1], len(weapons))]
        bonus = bonuses[roulette_index(spins[2], len(bonuses))]

        self.phase, self.wave_timer, self.wave_num = PLAY, R.WAVE_DURATION, self.wave_num + 1
        if self.pizza_goal < R.PIZZA_GOAL_MAX:
            self.pizza_goal = min(self.pizza_goal + R.PIZZA_GOAL_INCREMENT, R.PIZZA_GOAL_MAX)
        else:
            self.extra += 1
        self.round_p = 0
        self.dim = 1
        self.player.respawn()
        self.player.weapon = self.last_weapon = weapon
        self.spawn(self.extra)
        self._new_round_malus(malus)
        self._new_round_bonus(bonus)
        self.last_bonus = bonus

    # ------------------------------------------------------------------- tick
    def tick(self, right=False, left=False, down=False, up=False, interact=False, cook=None):
        """One frame of ``Game.handle()`` + ``Game.update(1/60)`` in PLAYING state."""
        if self.phase != PLAY:
            raise RuntimeError("tick() needs the PLAY phase")
        self.ticks += 1
        self.events.ticks += 1
        if cook is not None:
            if self.can_cook(cook):
                self._cook(cook)
                self.menu_open = True
        elif interact and not self.oven_active and not self.menu_open:
            self.trigger_weapon()

        p = self.player
        if self.pill_timer > 0:
            p.speed_mult = R.PILL_SPEED_MULTI
            self.cd_limit_mult = 1.0 / R.PILL_ATTACK_SPEED_MULTI
        else:
            p.speed_mult = 1.0
            self.cd_limit_mult = 1.0
        if not self.menu_open:
            p.handle_input(right, left, down, up)
        if p.hp <= 0:
            self._die()
            return
        hp = p.hp
        self._world_update()
        self.wave_timer -= DT
        change = self._orders_update()
        self.score += change
        self.events.score += change
        self._bonus_update()
        self.events.damage += hp - p.hp
        if self.menu_open and not self.oven_active:
            self.menu_open = False
        if self.wave_timer <= 0:
            self._end_wave()

    def close_menu(self):
        self.menu_open = False

    def pop_events(self):
        events, self.events = self.events, Events()
        return events
