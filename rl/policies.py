"""Players that read a headless ``Engine`` and return an action index.

* ``ModelPlayer``: a trained checkpoint. The observation is computed by the
  same torch encoder as in training, after copying the headless state into a
  one-game ``VectorEngine`` (``load``); the action mask is the headless one.
* ``make_player("random" | "scripted" | path)``: baselines or a checkpoint.
"""

import random

from .baselines import ScriptedBot, random_policy
from .headless.env import action_mask


class ModelPlayer:
    def __init__(self, path, deterministic=True, seed=0):
        import torch
        from .vector.engine import VectorEngine
        from .vector.features import encode
        from .vector.layouts import LayoutPool
        from .vector.policy import load_checkpoint

        torch.set_num_threads(1)
        self.torch, self.encode = torch, encode
        self.model, self.payload = load_checkpoint(path, "cpu")
        self.deterministic = deterministic
        self.generator = torch.Generator().manual_seed(seed)
        # A one-game engine only used as a tensor buffer for ``encode``: one layout is enough.
        self.vec = VectorEngine(1, device="cpu", dtype=torch.float64, layouts=LayoutPool.generate(1))

    def __call__(self, engine):
        torch = self.torch
        self.vec.load(0, engine)
        obs = self.encode(self.vec)
        mask = torch.tensor([action_mask(engine)])
        with torch.no_grad():
            logits, _ = self.model(obs, mask)
        if self.deterministic:
            return int(logits.argmax(-1))
        return int(torch.multinomial(torch.softmax(logits, -1), 1, generator=self.generator))


def make_player(spec, seed=0, deterministic=True):
    if spec == "random":
        return random_policy(random.Random(seed))
    if spec == "scripted":
        return ScriptedBot(seed, jitter=0.0)
    return ModelPlayer(spec, deterministic=deterministic, seed=seed)
