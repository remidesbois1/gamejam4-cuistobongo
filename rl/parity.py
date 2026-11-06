"""Replay the real pygame game and the headless engine side by side.

Both start from the same seed: gameplay modules draw from the global ``random``
(seeded like ``Engine(seed)``), purely cosmetic modules (camera shake, map
tiles, particles, sounds, death debris) get their own generator. Inputs come
from a policy reading the headless state, sent to the real game as key presses
by ``GameDriver``. After every tick the two states must be identical.

    python -m rl.parity --seeds 1 2 3 --decisions 6000
"""

import argparse
import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COSMETIC_MODULES = ("camera", "map", "effects", "player", "world")


def make_game():
    """A real ``Game`` with dummy video/audio, its cosmetic modules on a private RNG."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import importlib
    import game as game_module
    for name in COSMETIC_MODULES:
        importlib.import_module(name).random = random.Random(0)
    game = game_module.Game()
    # Music is irrelevant here and its channel juggling fails with the dummy audio driver.
    game.music_normal = game.music_upside = game.music_normal_fast = game.music_upside_fast = None
    game.music_drug = None
    return game


class Mismatch(AssertionError):
    pass


def replay(seed, decisions, policy, frame_skip=6, game=None, log=None, coverage=None):
    """Play ``decisions`` decisions in both engines; raise ``Mismatch`` on the first difference.

    Returns ``(engine, ticks)``. ``coverage`` (a dict) counts the mechanics exercised.
    """
    from .actions import COOK, decode
    from .bridge import GameDriver, engine_from_game, first_difference, state_dict
    from .headless.engine import OVER, PLAY, SHOP, Engine

    game = game or make_game()
    random.seed(seed)
    game.start()
    engine = Engine(seed)
    driver = GameDriver(game)
    ticks = 0
    coverage = {} if coverage is None else coverage

    def count(key, n=1):
        if n:
            coverage[key] = coverage.get(key, 0) + n

    def check(where):
        diff = first_difference(state_dict(engine), state_dict(engine_from_game(game)))
        if diff:
            raise Mismatch(f"seed {seed}, tick {ticks}, {where}: {diff}")

    def settle():
        """Run the real game through DYING, the shop exit and the roulette."""
        while game.state == "DYING":
            game.update(1 / 60)
        if game.state == "SHOP" and engine.phase == PLAY:
            driver.skip_shop()
            driver.frame()
            game.handle()
        while game.state in ("SHOP", "ROULETTE") and engine.phase == PLAY:
            game.update(1 / 60)

    def tick(kind, slot, dx, dy, interact):
        before = (len(engine.bombs), len(engine.pills), len(engine.notes), engine.player.hp, engine.wave_num)
        if kind == COOK:
            engine.tick(cook=slot)
        else:
            engine.tick(dx > 0, dx < 0, dy > 0, dy < 0, interact)
        events = engine.pop_events().as_dict()
        for key in ("deaths", "pizzas", "expired", "kills", "harvested", "picked", "waves", "game_over"):
            count(key, events[key])
        p = engine.player
        same_wave = engine.wave_num == before[4] and engine.phase == PLAY
        count(f"malus {engine.malus}")
        count(f"bonus {engine.bonus}")
        count(f"weapon {p.weapon}")
        count("dash ticks", p.dash_timer > 0)
        count("upside down ticks", engine.dim == 0)
        count("bombs exploded", max(0, before[0] - len(engine.bombs)) if same_wave else 0)
        count("pills taken", max(0, before[1] - len(engine.pills)) if same_wave else 0)
        count("notes exploded", max(0, before[2] - len(engine.notes)))
        count("hits taken", before[3] > p.hp)
        count("menu open ticks", engine.menu_open)

    try:
        check("start")
        for decision in range(decisions):
            if engine.phase == OVER:
                break
            action = policy(engine)
            if not driver.begin_decision(action):
                raise Mismatch(f"seed {seed}: the real recipe menu cannot be closed (decision {decision})")
            kind, (dx, dy), interact, slot = decode(action)
            if engine.phase == SHOP:
                engine.buy(slot)
                count("purchases")
                driver.frame()
                game.handle()
                settle()
                check(f"after buying card {slot}")
                continue
            engine.close_menu()
            for i in range(frame_skip):
                tick(kind, slot if i == 0 else None, dx, dy, interact and i == 0)
                driver.frame()
                game.handle()
                game.update(1 / 60)
                ticks += 1
                settle()
                check(f"decision {decision} ({action}), tick {i}")
                if engine.phase != PLAY:
                    break
            if log and decision % 2000 == 0:
                log(f"seed {seed}: decision {decision}, wave {engine.wave_num}, score {engine.score}")
    finally:
        driver.close()
    return engine, ticks


def main(argv=None):
    from .baselines import ScriptedBot

    parser = argparse.ArgumentParser(description="Tick-by-tick parity: real pygame game vs headless engine")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1])
    parser.add_argument("--decisions", type=int, default=3000)
    parser.add_argument("--frame-skip", type=int, default=6)
    parser.add_argument("--jitter", type=float, default=0.1, help="random action probability of the bot")
    args = parser.parse_args(argv)
    game = make_game()
    coverage, total = {}, 0
    for seed in args.seeds:
        started = time.perf_counter()
        engine, ticks = replay(seed, args.decisions, ScriptedBot(seed, args.jitter), args.frame_skip, game,
                               log=print, coverage=coverage)
        total += ticks
        print(f"seed {seed}: {ticks} identical ticks, wave {engine.wave_num}, score {engine.score}, "
              f"{time.perf_counter() - started:.1f}s")
    print(f"{total} identical ticks in total; coverage:")
    for key in sorted(coverage):
        print(f"  {key}: {coverage[key]}")


if __name__ == "__main__":
    main()
