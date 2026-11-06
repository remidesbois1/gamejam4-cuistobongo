"""Bridge between the real pygame ``Game`` and the headless engine.

* ``engine_from_game(game)``: copy of the real game state into an ``Engine``
  (no RNG): lets the RL encoder read the real game (watch mode) and lets the
  parity test compare both engines.
* ``state_dict(engine)``: every gameplay field, in a comparable form.
* ``GameDriver``: plays an RL action in the real game, with the same keys and
  menu presses a human would use.

Importing this module imports the game modules (pygame); the headless engine
itself never does.
"""

import pygame

import settings
from bonus_manager import Bomb
from effects import ExplodingNote
from enemy import Squid, TomatoEnemy
from item import CheeseOre, Tree
from recipe import RECIPES

from .headless import rules as R
from .headless.engine import (OVER, PLAY, SHOP, Bomb as HBomb, Drop, Engine, Enemy, Note, Order, Pill,
                              Player, Portal, Projectile, Resource)
from .actions import COOK, BUY, decode

INGREDIENT_INDEX = {name: i for i, name in enumerate(R.INGREDIENTS)}
TOMATO_STATES = {"IDLE": R.IDLE, "JUMP_PREP": R.JUMP_PREP, "JUMP": R.JUMP, "LAND": R.LAND,
                 "CHARGE_PREP": R.CHARGE_PREP, "ROLLING": R.ROLLING}
PHASES = {"PLAYING": PLAY, "DYING": PLAY, "SHOP": SHOP, "ROULETTE": SHOP, "GAME_OVER": OVER}


def _player(game):
    gp, h = game.player, Player()
    h.x, h.y = gp.pos.x, gp.pos.y
    h.rx, h.ry = gp.rect.x, gp.rect.y
    h.vel, h.hp, h.max_hp, h.inv_timer = gp.vel, gp.health, gp.max_health, gp.inv_timer
    h.last_dx, h.last_dy = gp.last_dir.x, gp.last_dir.y
    h.dash_timer, h.dash_vx, h.dash_vy = gp.dash_timer, gp.dash_vec.x, gp.dash_vec.y
    h.speed_mult = gp.speed_multiplier
    h.inventory = [gp.inventory.counts[name] for name in R.INGREDIENTS]
    h.cap = gp.inventory.cap
    h.weapon = R.WEAPONS.index(gp.weapon)
    return h


def _enemy(en):
    e = Enemy()
    e.x, e.y = en.pos.x, en.pos.y
    e.rx, e.ry, e.size = en.rect.x, en.rect.y, en.rect.width
    e.hp, e.max_hp, e.hit_timer = en.hp, en.max_hp, en.hit_timer
    e.shoot_cd = e.move_state = e.move_timer = e.state = e.timer = 0
    e.wx = e.wy = e.vx = e.vy = 0.0
    if isinstance(en, Squid):
        e.kind, e.giant, e.dim = R.SQUID, en.giant, en.dim
        e.shoot_cd, e.move_timer = en.shoot_cd, en.move_timer
        e.move_state = R.ADJUST if en.move_state == "ADJUST" else R.WANDER
        e.wx, e.wy = en.wander_vec.x, en.wander_vec.y
    else:
        e.kind, e.giant, e.dim = R.TOMATO_ENEMY, False, getattr(en, "dim", 1)
        e.state, e.timer = TOMATO_STATES[en.state], en.timer
        e.vx, e.vy = en.vel.x, en.vel.y
    return e


def engine_from_game(game):
    """An ``Engine`` holding the state of a started pygame ``Game`` (no RNG)."""
    w = game.world
    e = Engine.__new__(Engine)
    e.rng = None
    e.ticks = 0
    e.events = None
    e.player = _player(game)
    e.phase = PHASES[game.state]
    e.score, e.wave_timer, e.wave_num = game.score, game.wave_timer, game.wave_num
    e.pizza_goal, e.round_p, e.extra, e.pizzas_made = game.pizza_goal, game.round_p, game.extra_enemies, game.pizzas_made
    e.menu_open = game.recipe_menu.is_open
    e.last_weapon = R.WEAPONS.index(game.last_weapon)
    bm, mm = game.bonus_manager, game.malus_manager
    e.last_bonus = bm.bonuses.index(game.last_bonus) if game.last_bonus else None
    e.malus = mm.maluses.index(mm.current_malus) if mm.current_malus else None
    e.bonus = bm.bonuses.index(bm.active_bonus) if bm.active_bonus else None
    e.pill_timer = bm.pill_effect_timer

    e.orders = [Order.__new__(Order) if o else None for o in game.om.active_orders]
    for h, o in zip(e.orders, game.om.active_orders):
        if o:
            h.recipe, h.max_time, h.timer = RECIPES.index(o.recipe), o.max_time, o.timer
    e.time_mult, e.spawn_timer = game.om.time_mult, game.om.spawn_timer
    pool = game.shop_menu.pool
    e.upgrade_costs = [u.cost for u in pool]
    e.shop_cards = [pool.index(u) for u in game.shop_menu.active]

    e.dim, e.in_portal, e.items_flee = w.dim, w.in_p, w.items_flee
    e.oven_dim, e.oven_active = w.oven.dim, w.oven.active
    e.cd, e.cd_limit, e.cd_limit_mult = w.cd, w.cd_limit, w.cd_limit_multiplier
    e.portals = []
    for po in w.portals:
        p = Portal(0, 0)
        p.x, p.y, p.rx, p.ry = po.pos.x, po.pos.y, po.rect.x, po.rect.y
        p.moving, p.vx, p.vy, p.tvx, p.tvy = po.moving, po.vel.x, po.vel.y, po.target_vel.x, po.target_vel.y
        p.move_timer = po.move_timer
        e.portals.append(p)
    e.notes = []
    for fx in w.effs:
        if isinstance(fx, ExplodingNote) and not fx.done:
            n = Note.__new__(Note)
            n.x, n.y, n.dx, n.dy, n.timer = fx.pos.x, fx.pos.y, fx.dir.x, fx.dir.y, fx.timer
            e.notes.append(n)

    specs = {Tree: R.RESOURCE_TYPES[0], CheeseOre: R.RESOURCE_TYPES[1]}
    e.res = []
    for r in w.res_manager.res:
        h = Resource(specs[type(r)], r.rect.x, r.rect.y, 0)
        h.hp, h.max_hp, h.hit_timer = r.health, r.max_health, r.hit_timer
        e.res.append(h)
    e.res_drops = [Drop(INGREDIENT_INDEX[d.type], d.rect.x, d.rect.y, d.dim) for d in w.res_manager.drops]
    em = w.enemy_manager
    e.enemies = [_enemy(en) for en in em.enemies]
    e.enemy_drops = [Drop(INGREDIENT_INDEX[d.type], d.rect.x, d.rect.y, d.dim) for d in em.drops]
    e.projectiles = []
    for pr in em.projectiles:
        h = Projectile.__new__(Projectile)
        h.x, h.y, h.rx, h.ry, h.size = pr.pos.x, pr.pos.y, pr.rect.x, pr.rect.y, pr.rect.width
        h.vx, h.vy, h.timer, h.dim = pr.vel.x, pr.vel.y, pr.timer, pr.dim
        e.projectiles.append(h)
    e.bombs = []
    for b in bm.bombs:
        h = HBomb(0, 0)
        h.rx, h.ry, h.dim, h.attached, h.timer = b.rect.x, b.rect.y, b.dim, b.state == "ATTACHED", b.timer
        e.bombs.append(h)
    e.pills = [Pill(p.rect.centerx, p.rect.centery, 0.0) for p in bm.pills]
    return e


def state_dict(e):
    """All gameplay state of an engine, as plain comparable values (cosmetics excluded)."""
    p = e.player
    return {
        "phase": e.phase, "wave_num": e.wave_num, "wave_timer": e.wave_timer, "score": e.score,
        "pizza_goal": e.pizza_goal, "round_p": e.round_p, "extra": e.extra, "pizzas_made": e.pizzas_made,
        "menu_open": e.menu_open, "last_weapon": e.last_weapon, "last_bonus": e.last_bonus,
        "malus": e.malus, "bonus": e.bonus, "pill_timer": e.pill_timer,
        "orders": [(o.recipe, o.max_time, o.timer) if o else None for o in e.orders],
        "time_mult": e.time_mult, "spawn_timer": e.spawn_timer,
        "upgrade_costs": list(e.upgrade_costs), "shop_cards": list(e.shop_cards),
        "dim": e.dim, "in_portal": e.in_portal, "items_flee": e.items_flee,
        "oven": (e.oven_dim, e.oven_active), "cd": (e.cd, e.cd_limit, e.cd_limit_mult),
        "player": (p.x, p.y, p.rx, p.ry, p.vel, p.hp, p.max_hp, p.inv_timer, p.last_dx, p.last_dy,
                   p.dash_timer, p.dash_vx, p.dash_vy, p.speed_mult, tuple(p.inventory), p.cap, p.weapon),
        "portals": [(q.x, q.y, q.rx, q.ry, q.moving, q.vx, q.vy, q.tvx, q.tvy, q.move_timer) for q in e.portals],
        "notes": [(n.x, n.y, n.dx, n.dy, n.timer) for n in e.notes],
        "res": [(r.kind, r.rx, r.ry, r.hp, r.hit_timer) for r in e.res],
        "res_drops": [(d.kind, d.rx, d.ry, d.dim) for d in e.res_drops],
        "enemy_drops": [(d.kind, d.rx, d.ry, d.dim) for d in e.enemy_drops],
        "enemies": [(n.kind, n.giant, n.x, n.y, n.rx, n.ry, n.size, n.hp, n.max_hp, n.hit_timer, n.dim,
                     n.shoot_cd, n.move_state, n.move_timer, n.wx, n.wy, n.state, n.timer, n.vx, n.vy)
                    for n in e.enemies],
        "projectiles": [(q.x, q.y, q.rx, q.ry, q.size, q.vx, q.vy, q.timer, q.dim) for q in e.projectiles],
        "bombs": [(b.rx, b.ry, b.dim, b.attached, b.timer) for b in e.bombs],
        "pills": [(q.rx, q.ry) for q in e.pills],
    }


def first_difference(a, b, path="state"):
    """Path and values of the first mismatch between two ``state_dict`` values, or None."""
    if isinstance(a, dict):
        for key in a:
            found = first_difference(a[key], b[key], f"{path}.{key}")
            if found:
                return found
        return None
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return f"{path}: length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            found = first_difference(x, y, f"{path}[{i}]")
            if found:
                return found
        return None
    return None if a == b else f"{path}: {a!r} != {b!r}"


class _Keys:
    """Stand-in for ``pygame.key.get_pressed()``."""

    def __init__(self):
        self.down = set()

    def __getitem__(self, key):
        return key in self.down


def _key_event(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode="", mod=0, scancode=0)


class GameDriver:
    """Play RL actions in the real game with the keys of a human player.

    ``pygame.key.get_pressed`` is replaced while the driver lives: movement
    comes from the agent, not from the keyboard. Call ``begin_decision`` with
    each new action, then ``frame()`` before every ``game.handle()``.
    """

    def __init__(self, game):
        self.game = game
        self.keys = _Keys()
        self._get_pressed = pygame.key.get_pressed
        pygame.key.get_pressed = lambda: self.keys
        self.pending = []

    def close(self):
        pygame.key.get_pressed = self._get_pressed

    def _walk(self, current, target, limit=3):
        """RIGHT presses moving a menu cursor from ``current`` to ``target``."""
        while current != target:
            self.pending.append(_key_event(pygame.K_RIGHT))
            current = (current + 1) % limit

    def _close_menu(self):
        """Close the recipe menu like a player: validate a slot that cannot be cooked."""
        game = self.game
        inv = game.player.inventory
        for idx, order in enumerate(game.om.active_orders):
            if order is None or not inv.has_ingredients(order.recipe.ingredients):
                self._walk(game.recipe_menu.idx, idx)
                self.pending.append(_key_event(pygame.K_e))
                return True
        return False

    def begin_decision(self, action):
        """Translate one RL action into held keys and queued key presses.

        Returns False when the real menu cannot follow (all three orders cookable
        while closing the recipe menu): the player then stays in the menu.
        """
        game = self.game
        self.pending = []
        self.keys.down = set()
        kind, (dx, dy), interact, slot = decode(action)
        if game.state == "SHOP":
            if kind == BUY:
                shop = game.shop_menu
                can_buy = any(game.pizzas_made >= u.cost for u in shop.active)
                self._walk(shop.idx, slot, 3 if can_buy else 4)
                self.pending.append(_key_event(pygame.K_e))
            return True
        if kind == COOK:
            if not game.recipe_menu.is_open:
                self.pending.append(_key_event(pygame.K_e))
            self._walk(game.recipe_menu.idx, slot)
            self.pending.append(_key_event(pygame.K_e))
            return True
        if game.recipe_menu.is_open and not self._close_menu():
            return False
        if dx > 0:
            self.keys.down.add(pygame.K_RIGHT)
        if dx < 0:
            self.keys.down.add(pygame.K_LEFT)
        if dy > 0:
            self.keys.down.add(pygame.K_DOWN)
        if dy < 0:
            self.keys.down.add(pygame.K_UP)
        if interact and not game.world.oven.active:
            self.pending.append(_key_event(pygame.K_e))
        return True

    def skip_shop(self):
        """Press "PASSER" (only reachable when nothing is affordable)."""
        self.pending = [_key_event(pygame.K_DOWN), _key_event(pygame.K_e)]

    def frame(self):
        """Post the queued presses for the coming ``game.handle()``."""
        for event in self.pending:
            pygame.event.post(event)
        self.pending = []
