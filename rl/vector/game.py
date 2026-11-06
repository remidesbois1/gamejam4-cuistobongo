"""Batched training environment: engine + observations + rewards + automatic reset.

The reward is ``rl.rewards.reward`` (same weights as the headless evaluation).
Training adds two documented aids that never change the game rules:

* potential-based shaping ``coef * (gamma * phi(s') - phi(s))`` (Ng et al.,
  1999: the optimal policy is unchanged), with ``phi`` = 0.25 per bag
  ingredient that an open order still needs + 0.5 x (1 - distance to the oven
  / 4000 px) when an order is ready to cook (distance through the best portal
  if the oven is in the other dimension); ``phi`` is 0 outside play and after
  a terminal state;
* varied starts: a fraction of games start directly at a random wave 2..8,
  with the goal/extra enemies of that wave, random upgrades bought with the
  pizzas of the previous goals, a random weapon, malus and bonus, so every
  combination is practised early. Statistics only count normal starts.
"""

import torch

from ..actions import ACTION_COUNT
from ..headless import rules as R
from ..rewards import RewardWeights, reward as game_reward
from .engine import VectorEngine
from .features import _tables, encode, orders_missing, player_centre

STAT_KEYS = ("episodes", "score", "waves", "pizzas", "deaths", "expired", "game_over", "length",
             "game_return", "wave_reached")
EVENT_TOTALS = ("score", "waves", "pizzas", "deaths", "expired")


def potential(e):
    """Shaping potential ``phi`` [N] (engine dtype)."""
    t = _tables(e.p_x.device, e.p_x.dtype)
    demand = (t["need"][e.order_recipe] * e.order_alive.unsqueeze(-1)).sum(1)
    useful = torch.minimum(e.p_inventory, demand).sum(1).to(e.p_x.dtype)
    _, ready = orders_missing(e)
    pcx, pcy = player_centre(e)
    direct = torch.sqrt((pcx - R.OVEN_CX) ** 2 + (pcy - R.OVEN_CY) ** 2)
    half = R.PORTAL_SIZE // 2
    qx, qy = (e.portal_rx + half).to(pcx.dtype), (e.portal_ry + half).to(pcx.dtype)
    via = (torch.sqrt((qx - pcx.unsqueeze(1)) ** 2 + (qy - pcy.unsqueeze(1)) ** 2)
           + torch.sqrt((qx - R.OVEN_CX) ** 2 + (qy - R.OVEN_CY) ** 2)).min(1).values
    dist = torch.where(e.dim == e.oven_dim, direct, via)
    phi = 0.25 * useful + 0.5 * ready.any(1).to(pcx.dtype) * (1 - (dist / 4000).clamp(max=1))
    return torch.where(e.phase == 0, phi, torch.zeros_like(phi))


def wave_goal(wave):
    """Pizza goal of a wave (tensor), as game.py raises it."""
    return (R.INITIAL_PIZZA_GOAL + R.PIZZA_GOAL_INCREMENT * (wave - 1)).clamp(max=R.PIZZA_GOAL_MAX)


class VectorGame:
    def __init__(self, num_envs, *, device="cpu", dtype=torch.float32, frame_skip=6, episode_limit=12000,
                 weights=None, shaping=1.0, gamma=0.998, random_start=0.0, max_start_wave=8, seed=0,
                 layouts=None):
        if not 0.0 <= random_start <= 1.0:
            raise ValueError("random_start must be within [0, 1]")
        self.engine = VectorEngine(num_envs, device=device, dtype=dtype, frame_skip=frame_skip, seed=seed,
                                   layouts=layouts)
        self.n = num_envs
        self.device = self.engine.device
        self.weights = weights if weights is not None else RewardWeights()
        self.shaping = shaping
        self.gamma = gamma
        self.random_start = random_start
        self.max_start_wave = max_start_wave
        self.episode_limit = episode_limit
        f64 = lambda: torch.zeros(num_envs, dtype=torch.float64, device=self.device)
        self.decisions = torch.zeros(num_envs, dtype=torch.long, device=self.device)
        self.normal_start = torch.ones(num_envs, dtype=torch.bool, device=self.device)
        self.phi = f64()
        self.episode_return = f64()
        self.totals = {key: f64() for key in EVENT_TOTALS}
        self._stats = {key: torch.zeros((), dtype=torch.float64, device=self.device) for key in STAT_KEYS}
        # Optional bool[N]: only games still marked are recorded (evaluation keeps
        # the first episode of every game, without a bias toward short ones).
        self.count_mask = None

    def _randint(self, low, high):
        return (self.engine.rand(self.n) * (high - low)).long() + low

    def _vary(self, mask):
        """Jump the masked fresh games to a random later wave (see module docstring)."""
        e = self.engine
        varied = mask & (e.rand(self.n) < self.random_start)
        target = self._randint(2, self.max_start_wave + 1)
        prev = target - 1
        e.wave_num = torch.where(varied, prev, e.wave_num)
        e.pizza_goal = torch.where(varied, wave_goal(prev), e.pizza_goal)
        e.extra = torch.where(varied, (prev - 5).clamp(min=0), e.extra)
        pizzas = torch.zeros_like(e.pizzas_made)
        for wave in range(1, self.max_start_wave):
            earned = varied & (prev >= wave)
            pizzas = pizzas + torch.where(earned, wave_goal(torch.full_like(prev, wave)), 0)
            for _ in range(4):
                u = self._randint(0, len(R.UPGRADES))
                cost = e.upgrade_costs.gather(1, u.unsqueeze(1)).squeeze(1)
                buy = earned & (pizzas >= cost)
                pizzas = pizzas - torch.where(buy, cost, 0)
                self._apply_upgrade(buy, u)
        e.pizzas_made = torch.where(varied, pizzas.clamp(max=1), e.pizzas_made)
        malus = self._randint(0, len(R.MALUSES))
        weapon = self._randint(0, len(R.WEAPONS))
        bonus = self._randint(0, len(R.BONUSES))
        e.begin_wave(varied, malus, weapon, bonus)
        return varied

    def _apply_upgrade(self, buy, u):
        e = self.engine
        step = lambda kind: buy & (u == kind)
        e.p_vel = torch.where(step(R.SPEED), e.p_vel + R.UPGRADES[R.SPEED][1], e.p_vel)
        e.p_cap = torch.where(step(R.CAP), e.p_cap + R.UPGRADES[R.CAP][1], e.p_cap)
        e.cd_limit = torch.where(step(R.ATK_SPEED), (e.cd_limit - R.UPGRADES[R.ATK_SPEED][1]).clamp(min=R.MIN_CD_LIMIT),
                                 e.cd_limit)
        e.p_max_hp = torch.where(step(R.HEALTH), e.p_max_hp + R.UPGRADES[R.HEALTH][1], e.p_max_hp)
        e.p_hp = torch.minimum(e.p_hp, e.p_max_hp)
        e.time_mult = torch.where(step(R.TIME), e.time_mult + R.UPGRADES[R.TIME][1], e.time_mult)
        bought = buy.unsqueeze(1) & (torch.arange(len(R.UPGRADES), device=self.device) == u.unsqueeze(1))
        e.upgrade_costs = torch.where(bought, (e.upgrade_costs + R.UPGRADE_COST_STEP).clamp(max=R.UPGRADE_COST_MAX),
                                      e.upgrade_costs)

    def _restart(self, mask):
        if not self.engine._any(mask):
            return
        self.engine.reset(mask)
        if self.random_start > 0:
            varied = self._vary(mask)
            self.normal_start = torch.where(mask, ~varied, self.normal_start)
        else:
            self.normal_start = torch.where(mask, True, self.normal_start)
        self.decisions = torch.where(mask, 0, self.decisions)
        self.episode_return = torch.where(mask, 0.0, self.episode_return)
        for key, value in self.totals.items():
            self.totals[key] = torch.where(mask, 0.0, value)

    def observe(self):
        return encode(self.engine), self.engine.action_mask()

    def reset(self):
        self._restart(torch.ones(self.n, dtype=torch.bool, device=self.device))
        self.phi = potential(self.engine).double()
        return self.observe()

    def step(self, actions):
        """Apply actions; return ``(obs, mask, reward, terminated, truncated, final_obs)``.

        ``obs``/``mask`` already belong to the next episode where a game ended;
        ``final_obs`` is the last observation of the finished episode (value
        bootstrap of games cut by the decision limit).
        """
        e = self.engine
        events = e.step(actions)
        self.decisions = self.decisions + 1
        final_obs = encode(e)
        terminated = e.phase == 2
        truncated = ~terminated & (self.decisions >= self.episode_limit)
        done = terminated | truncated
        game = game_reward(events, self.weights).double()
        phi = torch.where(terminated, 0.0, potential(e).double())
        shaped = game + self.shaping * (self.gamma * phi - self.phi)
        self.episode_return = self.episode_return + game
        for key in self.totals:
            self.totals[key] = self.totals[key] + events[key].double()
        self._record(done, terminated)
        self._restart(done)
        self.phi = torch.where(done, potential(e).double(), phi)
        obs, mask = self.observe()
        return obs, mask, shaped.float(), terminated, truncated, final_obs

    def _record(self, done, terminated):
        counted = done & self.normal_start
        if self.count_mask is not None:
            counted = counted & self.count_mask
        c = counted.double()
        s, t = self._stats, self.totals
        s["episodes"] += c.sum()
        for key in EVENT_TOTALS:
            s[key] += (t[key] * c).sum()
        s["game_over"] += (terminated.double() * c).sum()
        s["length"] += (self.decisions.double() * c).sum()
        s["game_return"] += (self.episode_return * c).sum()
        s["wave_reached"] += (self.engine.wave_num.double() * c).sum()

    def pop_stats(self):
        """Means over normally started episodes finished since the last call."""
        values = {k: float(v) for k, v in self._stats.items()}
        for v in self._stats.values():
            v.zero_()
        count = values.pop("episodes")
        if count == 0:
            return {"episodes": 0}
        result = {k: v / count for k, v in values.items()}
        result["episodes"] = int(count)
        return result


class GraphedStep:
    """Replay ``VectorGame.step`` as one CUDA graph instead of thousands of kernel launches.

    Every tensor of the game and its engine is kept in a static buffer: after
    each captured step, rebound attributes are copied back into those buffers.
    Outputs are overwritten by the next replay; consume or copy them first.
    Use ``reset()`` instead of ``game.reset()`` once the graph exists.
    """

    def __init__(self, game, warmup=3):
        if game.device.type != "cuda":
            raise ValueError("CUDA graphs need a CUDA game")
        self.game = game
        self.actions = torch.zeros(game.n, dtype=torch.long, device=game.device)
        game.reset()
        self._slots = list(self._state_slots())
        stream = torch.cuda.Stream()
        stream.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(stream):
            for _ in range(warmup):
                self._body()
        torch.cuda.current_stream().wait_stream(stream)
        self.graph = torch.cuda.CUDAGraph()
        self.graph.register_generator_state(game.engine.gen)
        with torch.cuda.graph(self.graph):
            self.outputs = self._body()

    def _state_slots(self):
        for owner in (self.game.engine, self.game):
            for name, value in list(vars(owner).items()):
                if isinstance(value, torch.Tensor):
                    yield owner, name, value
                elif isinstance(value, dict):
                    for key, item in value.items():
                        if isinstance(item, torch.Tensor):
                            yield value, key, item

    def _restore(self):
        for owner, name, static in self._slots:
            current = owner[name] if isinstance(owner, dict) else getattr(owner, name)
            if current is not static:
                static.copy_(current)
                if isinstance(owner, dict):
                    owner[name] = static
                else:
                    setattr(owner, name, static)

    def _body(self):
        outputs = self.game.step(self.actions)
        self._restore()
        return outputs

    def reset(self):
        outputs = self.game.reset()
        self._restore()
        return outputs

    def __call__(self, actions):
        self.actions.copy_(actions)
        self.graph.replay()
        return self.outputs


__all__ = ["ACTION_COUNT", "STAT_KEYS", "GraphedStep", "VectorGame", "potential"]
