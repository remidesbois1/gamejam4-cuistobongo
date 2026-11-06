"""The headless engine replays the real pygame game exactly (same seed, same inputs).

Longer runs: ``python -m rl.parity --seeds 1 2 3 ... --decisions 20000``.
"""

import random

import pytest

from rl.baselines import ScriptedBot, random_policy
from rl.headless import rules as R
from rl.headless.engine import roulette_index
from rl.parity import make_game, replay


@pytest.fixture(scope="module")
def game():
    return make_game()


@pytest.mark.parametrize("seed", [3, 15, 27])
def test_scripted_games_match_tick_by_tick(game, seed):
    coverage = {}
    engine, ticks = replay(seed, 4000, ScriptedBot(seed, jitter=0.15), game=game, coverage=coverage)
    assert ticks > 5000
    # The scripted cook must reach the oven, the Upside Down and the shop for the test to mean anything.
    assert coverage.get("pizzas", 0) >= 3 and coverage.get("upside down ticks", 0) > 0


def test_random_inputs_match_tick_by_tick(game):
    replay(7, 1500, random_policy(random.Random(7)), game=game)


def test_settings_constants_are_the_game_ones():
    import settings

    pairs = {
        "MAP_WIDTH": R.MAP_W, "MAP_HEIGHT": R.MAP_H, "PLAYER_SIZE": R.PLAYER_SIZE, "PLAYER_SPEED": R.PLAYER_SPEED,
        "PLAYER_HP": R.PLAYER_HP, "PLAYER_DASH_SPEED": R.DASH_SPEED, "PLAYER_DASH_TIME": R.DASH_TIME,
        "PLAYER_DASH_INV_TIME": R.DASH_INV_TIME, "PLAYER_INV_TIME": R.PLAYER_INV_TIME,
        "SQUID_SIZE": R.SQUID_SIZE, "SQUID_HP": R.SQUID_HP, "SQUID_SHOOT_DIST": R.SQUID_SHOOT_DIST,
        "PROJECTILE_SPEED": R.PROJECTILE_SPEED, "TOMATO_SIZE": R.TOMATO_SIZE, "TOMATO_HP": R.TOMATO_HP,
        "TOMATO_ATTACK_DIST": R.TOMATO_ATTACK_DIST, "PROJECTILE_SIZE": R.PROJECTILE_SIZE,
        "PROJECTILE_LIFETIME": R.PROJECTILE_LIFETIME, "WAVE_DURATION": R.WAVE_DURATION,
        "SHOP_DURATION": R.SHOP_DURATION, "INITIAL_PIZZA_GOAL": R.INITIAL_PIZZA_GOAL,
        "PIZZA_GOAL_INCREMENT": R.PIZZA_GOAL_INCREMENT, "DEATH_PENALTY_TIME": R.DEATH_PENALTY_TIME,
        "OVEN_SAFE_ZONE_RADIUS": R.OVEN_SAFE_ZONE_RADIUS, "ORDER_SPAWN_TIME": R.ORDER_SPAWN_TIME,
        "BOMBS_COUNT_MIN": R.BOMBS_COUNT_MIN, "BOMBS_COUNT_MAX": R.BOMBS_COUNT_MAX,
        "PILL_COUNT_MIN": R.PILL_COUNT_MIN, "PILL_COUNT_MAX": R.PILL_COUNT_MAX,
        "PILL_DURATION_TIME": R.PILL_DURATION_TIME, "PILL_SPEED_MULTI": R.PILL_SPEED_MULTI,
        "PILL_ATTACK_SPEED_MULTI": R.PILL_ATTACK_SPEED_MULTI,
    }
    assert {k: getattr(settings, k) for k in pairs} == pairs
    assert [(d["cost"], d["val"]) for d in settings.UPGRADE_DEFS.values()] == \
        [(R.UPGRADE_COST, value) for _, value in R.UPGRADES]


def test_roulette_matches_the_animated_slot():
    """roulette_index replays ui.RouletteSlot frame by frame at 60 FPS."""
    import ui

    class Item:
        name, icon = "", None

    rng = random.Random(0)
    for _ in range(200):
        n = rng.choice([2, 3, 5, 6])
        slot = ui.RouletteSlot([Item() for _ in range(n)], None, "")
        while not slot.update(1 / 60):
            pass
        assert slot.current_idx == roulette_index(slot.spin_duration, n)
