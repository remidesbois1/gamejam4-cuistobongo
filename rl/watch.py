"""Watch a player in the real game (window, graphics, sounds), no GPU needed.

The real ``Game`` runs normally; every ``frame_skip`` frames its state is
copied into a headless ``Engine`` (``rl.bridge.engine_from_game``), the player
picks an action, and ``GameDriver`` presses the keys a human would press
(movement held, E to play the instrument, E / arrows / E in the recipe menu,
arrows / E in the shop). Death animations and the roulette play as usual.

    python -m rl.watch --player runs/bongo-v1/best.pt
    python -m rl.watch --player scripted --speed 4

Keys: Space pause, Up/Down (or +/-) speed x1..x8, Tab deterministic/sampled
actions, N new game, Esc quit.
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(argv=None):
    p = argparse.ArgumentParser(description="Watch a Cuisto Bongo player in the real game")
    p.add_argument("--player", required=True, help="checkpoint path, 'scripted' or 'random'")
    p.add_argument("--seed", type=int, default=0, help="random seed of the game (gameplay draws)")
    p.add_argument("--speed", type=int, default=1, help="game frames per displayed frame (1..8)")
    p.add_argument("--frame-skip", type=int, default=6, help="frames per decision (as in training)")
    p.add_argument("--stochastic", action="store_true", help="sample actions instead of the most likely one")
    args = p.parse_args(argv)

    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import random

    import pygame
    import settings
    from game import Game

    from .bridge import GameDriver, engine_from_game
    from .policies import make_player

    deterministic = not args.stochastic
    player = make_player(args.player, seed=args.seed, deterministic=deterministic)
    game = Game()
    pygame.display.set_caption(f"Cuisto Bongo — IA ({args.player})")
    driver = GameDriver(game)
    speed, paused, seed = max(1, min(8, args.speed)), False, args.seed

    def new_game():
        nonlocal frame
        random.seed(seed)
        game.start()
        frame = 0

    frame = 0
    new_game()
    try:
        while game.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game.running = False
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                    elif event.key in (pygame.K_UP, pygame.K_PLUS, pygame.K_KP_PLUS):
                        speed = min(8, speed * 2)
                    elif event.key in (pygame.K_DOWN, pygame.K_MINUS, pygame.K_KP_MINUS):
                        speed = max(1, speed // 2)
                    elif event.key == pygame.K_TAB and hasattr(player, "deterministic"):
                        player.deterministic = not player.deterministic
                    elif event.key == pygame.K_n:
                        seed += 1
                        new_game()
            if paused:
                game.draw()
                game.clock.tick(settings.FPS)
                continue
            for _ in range(speed):
                if game.state == "GAME_OVER":
                    game.game_over_timer += 1 / settings.FPS
                    if game.game_over_timer > 4:
                        seed += 1
                        new_game()
                    break
                if game.state == "SHOP":
                    engine = engine_from_game(game)
                    if engine.can_buy():
                        driver.begin_decision(player(engine))
                    else:
                        driver.skip_shop()
                elif game.state == "PLAYING" and frame % args.frame_skip == 0:
                    driver.begin_decision(player(engine_from_game(game)))
                driver.frame()
                game.handle()
                game.update(1 / settings.FPS)
                if game.state == "PLAYING":
                    frame += 1
            game.draw()
            game.clock.tick(settings.FPS)
    finally:
        driver.close()
        pygame.quit()


if __name__ == "__main__":
    main()
