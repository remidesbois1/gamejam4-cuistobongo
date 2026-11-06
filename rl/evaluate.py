"""Evaluate a player on the headless reference engine (same rules as the pygame game).

Every player gets the same seeds (never used in training: training draws its
layouts from the cached pool and its own torch generator). Games are played
until GAME OVER or the decision limit, in parallel worker processes.

    python -m rl.evaluate --player runs/bongo-v1/best.pt --games 40 --seed 700000
    python -m rl.evaluate --player scripted --games 40 --seed 700000
    python -m rl.evaluate --player random --games 40 --seed 700000 --output eval-random.json
"""

import argparse
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .headless.engine import OVER
from .headless.env import HeadlessEnv

GAME_KEYS = ("score", "waves", "wave_reached", "pizzas", "expired", "deaths", "kills", "harvested",
             "game_over", "decisions", "minutes")


def play_game(player_spec, seed, frame_skip, limit, deterministic):
    from .policies import make_player

    player = make_player(player_spec, seed=seed, deterministic=deterministic)
    env = HeadlessEnv(frame_skip=frame_skip, episode_limit=limit, seed=seed)
    totals = {"pizzas": 0, "expired": 0, "deaths": 0, "kills": 0, "harvested": 0, "waves": 0, "ticks": 0}
    while True:
        events, terminated, truncated = env.step(player(env.engine))
        for key in totals:
            totals[key] += events[key]
        if terminated or truncated:
            break
    e = env.engine
    return {"seed": seed, "score": e.score, "waves": totals["waves"], "wave_reached": e.wave_num,
            "pizzas": totals["pizzas"], "expired": totals["expired"], "deaths": totals["deaths"],
            "kills": totals["kills"], "harvested": totals["harvested"], "game_over": int(e.phase == OVER),
            "decisions": env.decisions, "minutes": totals["ticks"] / 3600}


def summarise(games):
    summary = {"games": len(games)}
    for key in GAME_KEYS:
        values = [g[key] for g in games]
        mean = sum(values) / len(values)
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1))
        summary[key] = {"mean": mean, "std": std, "min": min(values), "max": max(values)}
    return summary


def main(argv=None):
    p = argparse.ArgumentParser(description="Evaluate a player on the headless reference engine")
    p.add_argument("--player", required=True, help="checkpoint path, 'scripted' or 'random'")
    p.add_argument("--games", type=int, default=40)
    p.add_argument("--seed", type=int, default=700_000, help="first seed (seeds seed .. seed+games-1)")
    p.add_argument("--frame-skip", type=int, default=6)
    p.add_argument("--limit", type=int, default=12_600, help="decisions per game (12600 = 21 min = 12 waves)")
    p.add_argument("--stochastic", action="store_true", help="sample actions instead of the most likely one")
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    p.add_argument("--output", type=Path, help="write per-game results and the summary as JSON")
    args = p.parse_args(argv)
    seeds = range(args.seed, args.seed + args.games)
    with ProcessPoolExecutor(args.workers) as pool:
        games = list(pool.map(play_game, [args.player] * args.games, seeds, [args.frame_skip] * args.games,
                              [args.limit] * args.games, [not args.stochastic] * args.games))
    summary = summarise(games)
    print(json.dumps(summary, indent=2))
    if args.output:
        args.output.write_text(json.dumps({"player": args.player, "args": vars(args) | {"output": str(args.output)},
                                           "summary": summary, "games": games}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
