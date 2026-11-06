"""Learning reward of Cuisto Bongo, from the per-decision events of either engine.

The game score alone is a poor signal: it ignores the pizza goal that ends the
game, and gives nothing for surviving a wave. These weights are hypotheses to
test, not tuned values; ``doc/rl.md`` explains each choice.
"""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RewardWeights:
    score: float = 0.01      # order points (an expired order removes its points)
    pizza: float = 1.0       # every pizza counts toward the wave goal
    wave: float = 3.0        # wave goal reached
    game_over: float = -5.0  # goal missed: the game ends
    death: float = -1.0      # bag emptied, 30 s lost
    damage: float = -0.01    # per health point lost

    def as_dict(self):
        return asdict(self)


def reward(events, w):
    """Weighted sum of an events mapping (dict of floats or of tensors)."""
    return (events["score"] * w.score + events["pizzas"] * w.pizza + events["waves"] * w.wave
            + events["game_over"] * w.game_over + events["deaths"] * w.death + events["damage"] * w.damage)
