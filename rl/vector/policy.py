"""Masked actor-critic with built-in observation normalisation, and checkpoints."""

from pathlib import Path

import torch
from torch import nn

from ..actions import ACTION_COUNT
from .features import FEATURE_SIZE, SCHEMA

MASKED_LOGIT = -1e8


class RunningNorm(nn.Module):
    """Running mean/variance of observations (parallel Welford), saved with the model."""

    def __init__(self, size, clip=10.0):
        super().__init__()
        self.clip = clip
        self.register_buffer("mean", torch.zeros(size, dtype=torch.float64))
        self.register_buffer("var", torch.ones(size, dtype=torch.float64))
        self.register_buffer("count", torch.tensor(1e-4, dtype=torch.float64))

    @torch.no_grad()
    def update(self, batch):
        batch = batch.double()
        n = batch.shape[0]
        mean, var = batch.mean(0), batch.var(0, unbiased=False)
        delta = mean - self.mean
        total = self.count + n
        self.mean += delta * n / total
        self.var = (self.var * self.count + var * n + delta.square() * self.count * n / total) / total
        self.count = total

    def forward(self, obs):
        return ((obs - self.mean.float()) / (self.var.float() + 1e-8).sqrt()).clamp(-self.clip, self.clip)


def _mlp(sizes, out, gain):
    layers = []
    for a, b in zip(sizes[:-1], sizes[1:]):
        linear = nn.Linear(a, b)
        nn.init.orthogonal_(linear.weight, 2 ** 0.5)
        nn.init.zeros_(linear.bias)
        layers += [linear, nn.SiLU()]
    head = nn.Linear(sizes[-1], out)
    nn.init.orthogonal_(head.weight, gain)
    nn.init.zeros_(head.bias)
    return nn.Sequential(*layers, head)


class ActorCritic(nn.Module):
    """Separate actor and critic MLPs on the normalised observation.

    Invalid actions (``mask`` False) get a logit of -1e8: probability zero,
    finite log-probabilities and entropy.
    """

    def __init__(self, obs_size=FEATURE_SIZE, actions=ACTION_COUNT, hidden=(512, 512, 256)):
        super().__init__()
        self.hidden = tuple(hidden)
        self.norm = RunningNorm(obs_size)
        self.actor = _mlp((obs_size, *hidden), actions, 0.01)
        self.critic = _mlp((obs_size, *hidden), 1, 1.0)

    def heads(self, normalized, mask=None):
        """Masked logits and value from an already normalised observation."""
        logits = self.actor(normalized)
        if mask is not None:
            logits = logits.masked_fill(~mask, MASKED_LOGIT)
        return logits, self.critic(normalized).squeeze(-1)

    def forward(self, obs, mask=None):
        return self.heads(self.norm(obs), mask)


def save_checkpoint(path, model, *, optimizer=None, extra=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema": SCHEMA, "obs_size": FEATURE_SIZE, "actions": ACTION_COUNT,
               "hidden": list(model.hidden), "model": model.state_dict(), **(extra or {})}
    if optimizer is not None:
        payload["optimizer"] = optimizer.state_dict()
    tmp = path.with_suffix(path.suffix + ".tmp")
    torch.save(payload, tmp)
    tmp.replace(path)


def load_checkpoint(path, device="cpu"):
    payload = torch.load(path, map_location=device, weights_only=False)
    if payload.get("schema") != SCHEMA or payload.get("obs_size") != FEATURE_SIZE \
            or payload.get("actions") != ACTION_COUNT:
        raise ValueError(f"{path} is not a {SCHEMA} checkpoint for these features")
    model = ActorCritic(hidden=payload["hidden"]).to(device)
    model.load_state_dict(payload["model"])
    return model.eval(), payload
