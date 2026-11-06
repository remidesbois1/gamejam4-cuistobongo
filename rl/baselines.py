"""Reference players for comparisons: uniform random and a scripted cook.

``ScriptedBot`` is a hand-written strategy reading the headless state. It is a
baseline (and the input generator of the parity tests), never a teacher: the
RL agent receives no demonstration from it.
"""

import math
import random

from . import actions as A
from .headless import rules as R
from .headless.engine import SHOP
from .headless.env import action_mask


def random_policy(rng):
    def act(engine):
        mask = action_mask(engine)
        return rng.choice([a for a, ok in enumerate(mask) if ok])
    return act


def _direction(dx, dy):
    """Index of the move (1..8) closest to the vector (dx, dy)."""
    if dx == 0 and dy == 0:
        return 0
    angle = math.atan2(dy, dx)
    best, best_err = 0, 9.0
    for i, (mx, my) in enumerate(A.MOVES[1:], start=1):
        err = abs((math.atan2(my, mx) - angle + math.pi) % (2 * math.pi) - math.pi)
        if err < best_err:
            best, best_err = i, err
    return best


class ScriptedBot:
    """Greedy cook: pick the most urgent order, fetch what is missing, cook it.

    Dough and cheese are mined in the Upside Down (dimension 0), tomatoes are
    killed in the world of their dimension; the oven is in ``oven_dim``. Free
    bombs and pills close by are picked up on the way.
    """

    def __init__(self, seed=0, jitter=0.1):
        self.rng = random.Random(seed)
        self.jitter = jitter

    def __call__(self, e):
        mask = action_mask(e)
        if e.phase == SHOP:
            cards = [c for c in range(3) if mask[A.BUY_BASE + c]]
            preference = (R.CAP, R.SPEED, R.TIME, R.ATK_SPEED, R.HEALTH)
            return A.BUY_BASE + min(cards, key=lambda c: preference.index(e.shop_cards[c]))
        cookable = [s for s in range(3) if mask[A.COOK_BASE + s]]
        if cookable:
            return A.COOK_BASE + max(cookable, key=lambda s: R.RECIPES[e.orders[s].recipe][2])
        if self.rng.random() < self.jitter:
            return self.rng.randrange(A.COOK_BASE)
        p = e.player
        bonus = self._bonus_target(e)
        if bonus is not None:
            return _direction(bonus[0] - p.cx, bonus[1] - p.cy)
        need = self._missing(e)
        target = None if need is None else self._target(e, need)
        if target is None:
            return self._go(e, R.OVEN_CX, R.OVEN_CY, e.oven_dim)
        tx, ty, dim, attack = target
        move = self._go(e, tx, ty, dim)
        dist = math.hypot(tx - p.cx, ty - p.cy)
        reach = {R.DRUM: 170, R.PAN: 140, R.SAX: 380}[p.weapon]
        if attack and e.dim == dim and dist < reach and e.cd <= 0:
            if p.weapon != R.DRUM:
                move = _direction(tx - p.cx, ty - p.cy)
            return A.INTERACT_BASE + move
        return move

    def _bonus_target(self, e, radius=600):
        """A nearby free bomb (same dimension) or pill: both help, both are cheap to grab."""
        p = e.player
        spots = [(b.rx + R.BOMB_SIZE // 2, b.ry + R.BOMB_SIZE // 2) for b in e.bombs
                 if not b.attached and b.dim == e.dim]
        spots += [(q.rx + R.PILL_SIZE // 2, q.ry + R.PILL_SIZE // 2) for q in e.pills]
        spots = [s for s in spots if math.hypot(s[0] - p.cx, s[1] - p.cy) < radius]
        return min(spots, key=lambda s: math.hypot(s[0] - p.cx, s[1] - p.cy)) if spots else None

    def _missing(self, e):
        """First missing ingredient of the most urgent feasible order, or None if cookable / no order."""
        orders = sorted((o for o in e.orders if o), key=lambda o: o.timer)
        inv = e.player.inventory
        for o in orders:
            need = R.RECIPES[o.recipe][1]
            missing = [k for k in range(3) if inv[k] < need[k]]
            if not missing:
                return None
            if all(need[k] <= e.player.cap for k in range(3)):
                return missing[0]
        return None

    def _target(self, e, kind):
        p = e.player
        best, best_d = None, float("inf")

        def consider(x, y, dim, attack):
            nonlocal best, best_d
            d = math.hypot(x - p.cx, y - p.cy) + (0 if dim == e.dim else 1500)
            if d < best_d:
                best, best_d = (x, y, dim, attack), d

        half = R.DROP_SIZE // 2
        for d in e.res_drops:
            if d.kind == kind:
                consider(d.rx + half, d.ry + half, 1 if kind == R.TOMATO else 0, False)
        if kind == R.TOMATO:
            for d in e.enemy_drops:
                consider(d.rx + half, d.ry + half, d.dim, False)
            for n in e.enemies:
                if n.kind == R.TOMATO_ENEMY:
                    consider(n.cx, n.cy, n.dim, True)
        else:
            for r in e.res:
                if r.drop == kind:
                    consider(r.cx, r.cy, 0, True)
        return best

    def _go(self, e, tx, ty, dim):
        p = e.player
        if e.dim != dim:
            portal = min(e.portals, key=lambda q: math.hypot(q.cx - p.cx, q.cy - p.cy) +
                         math.hypot(q.cx - tx, q.cy - ty))
            if e.in_portal:
                # Leave the portal before entering again.
                return _direction(p.cx - portal.cx, p.cy - portal.cy)
            tx, ty = portal.cx, portal.cy
        return _direction(tx - p.cx, ty - p.cy)
