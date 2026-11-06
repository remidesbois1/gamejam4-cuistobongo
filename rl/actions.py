"""The 24 discrete actions of the agent.

=========  =====================================================
0 - 8      move (none, N, NE, E, SE, S, SW, W, NW)
9 - 17     same moves + interact (instrument; ignored at the oven)
18 - 20    cook order slot 0, 1, 2 (oven active, ingredients in bag)
21 - 23    buy shop card 0, 1, 2 (shop only, card affordable)
=========  =====================================================

Moves follow the keyboard: up and left both pressed is the NW diagonal,
normalised by the game like a human input.
"""

MOVES = ((0, 0), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1))
MOVE, COOK, BUY = 0, 1, 2
INTERACT_BASE = len(MOVES)
COOK_BASE = 2 * len(MOVES)
BUY_BASE = COOK_BASE + 3
ACTION_COUNT = BUY_BASE + 3


def decode(action):
    """``(kind, (dx, dy), interact, slot)`` of an action index."""
    action = int(action)
    if not 0 <= action < ACTION_COUNT:
        raise ValueError(f"action {action} outside [0, {ACTION_COUNT})")
    if action < COOK_BASE:
        return MOVE, MOVES[action % len(MOVES)], action >= INTERACT_BASE, None
    if action < BUY_BASE:
        return COOK, (0, 0), False, action - COOK_BASE
    return BUY, (0, 0), False, action - BUY_BASE
