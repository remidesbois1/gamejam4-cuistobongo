"""Decision-level wrapper of the headless engine (same contract as the vector engine).

One decision holds an action for ``frame_skip`` ticks (6 ticks = 0.1 s by
default). Shop purchases are decisions that take no tick. A decision ends early
when the wave ends. ``terminated`` is GAME OVER (pizza goal missed);
``truncated`` is the optional decision limit.
"""

from ..actions import ACTION_COUNT, BUY, COOK, COOK_BASE, BUY_BASE, decode
from .engine import OVER, PLAY, SHOP, Engine


def action_mask(engine):
    """Valid actions in the current state (list of 24 booleans)."""
    if engine.phase == SHOP:
        mask = [False] * ACTION_COUNT
        for card in range(3):
            mask[BUY_BASE + card] = engine.can_buy(card)
        return mask
    mask = [True] * COOK_BASE + [False] * (ACTION_COUNT - COOK_BASE)
    if engine.phase == PLAY:
        for slot in range(3):
            mask[COOK_BASE + slot] = engine.can_cook(slot)
    return mask


def play_decision(engine, action, frame_skip):
    """Apply one action: shop purchase, cooking, or moves held for ``frame_skip`` ticks."""
    kind, (dx, dy), interact, slot = decode(action)
    if engine.phase == SHOP:
        if kind == BUY:
            engine.buy(slot)
        return
    if engine.phase != PLAY:
        return
    engine.close_menu()
    if kind == BUY:
        kind, interact = None, False
    for i in range(frame_skip):
        if kind == COOK:
            engine.tick(cook=slot if i == 0 else None)
        else:
            engine.tick(dx > 0, dx < 0, dy > 0, dy < 0, interact and i == 0)
        if engine.phase != PLAY:
            return


class HeadlessEnv:
    def __init__(self, frame_skip=6, episode_limit=None, seed=None):
        self.frame_skip = frame_skip
        self.episode_limit = episode_limit
        self.engine = Engine(seed)
        self.decisions = 0

    def reset(self, seed=None):
        self.engine.reset(seed)
        self.decisions = 0
        return self.engine

    def action_mask(self):
        return action_mask(self.engine)

    def step(self, action):
        """Returns ``(events dict, terminated, truncated)``."""
        play_decision(self.engine, action, self.frame_skip)
        self.decisions += 1
        terminated = self.engine.phase == OVER
        truncated = not terminated and self.episode_limit is not None and self.decisions >= self.episode_limit
        return self.engine.pop_events().as_dict(), terminated, truncated
