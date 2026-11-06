"""Parity of the torch vector engine with the headless reference engine.

Tick level: every tick, each headless game is loaded into the vector engine,
both engines advance one tick with the same random numbers (the vector draws
are fed to the headless engine through ``Engine._rng_for``), and the full
states must match (floats within 1e-9, everything else exactly). Decision
level: ``VectorEngine.step`` against ``rl.headless.env.play_decision``.
"""

import random

import pytest
import torch

from rl import actions as A
from rl.baselines import ScriptedBot
from rl.headless import rules as R
from rl.headless.engine import DT, OVER, PLAY, SHOP, Drop, Engine, roulette_index
from rl.headless.env import action_mask, play_decision
from rl.vector.compare import first_difference, state_dict
from rl.vector.engine import ENEMY_SLOTS, EVENT_KEYS, VectorEngine
from rl.vector.layouts import load_pool

TOL = 1e-9
TICK_DRAWS = 9  # rand() calls per tick: portals, enemies, order, wave end + 5 wave-start draws
STEP_DRAWS = 6  # rand() calls at the start of step: shop card + 5 wave-start draws


@pytest.fixture(scope="module")
def pool(tmp_path_factory):
    return load_pool(48, cache_dir=tmp_path_factory.mktemp("layouts"), workers=0)


class Feed:
    """A ``random.Random`` stand-in replaying given ``random()`` values (then ``fallback``)."""

    def __init__(self, values=(), fallback=None):
        self.values, self.i, self.fallback = [float(v) for v in values], 0, fallback

    def random(self):
        if self.i < len(self.values):
            self.i += 1
            return self.values[self.i - 1]
        if self.fallback is None:
            raise AssertionError("the headless engine drew more numbers than the vector engine")
        return self.fallback.random()

    def uniform(self, a, b):
        return a + (b - a) * self.random()

    def _randbelow(self, n):
        return int(self.random() * n)

    def choice(self, seq):
        return seq[self._randbelow(len(seq))]

    def randint(self, a, b):
        return a + self._randbelow(b - a + 1)

    def sample(self, population, k):
        pool, out = list(population), []
        for i in range(k):
            j = self._randbelow(len(pool) - i)
            out.append(pool[j])
            pool[j] = pool[len(pool) - i - 1]
        return out


class FedEngine(Engine):
    """Headless engine drawing, during a tick, the numbers the vector engine drew."""

    feeds = None
    queue = None  # per-tick draws of one vector decision: (slot, [draws of tick 0, ...], shop draw)
    slots = None  # id(enemy) -> vector slot during a vector decision

    def _rng_for(self, owner):
        if self.feeds is None:
            return self.rng
        found = self.feeds.get(owner if isinstance(owner, str) else id(owner))
        return found if found is not None else Feed(fallback=random.Random(0))  # bomb hue (cosmetic)

    def feed(self, k, portal, enemy, order, wave):
        # Vector slot of each enemy: list index when loaded (kills leave dead slots).
        slots = self.slots if self.slots is not None else {id(e): j for j, e in enumerate(self.enemies)}
        self.feeds = {id(q): Feed(portal[k, j].tolist()) for j, q in enumerate(self.portals)}
        self.feeds.update({id(e): Feed(enemy[k, slots[id(e)]].tolist()) for e in self.enemies})
        self.feeds["orders"] = Feed([order[k].item()])
        self._real_rng, self.rng = self.rng, Feed(wave[k].tolist(), fallback=self.rng)

    def unfeed(self):
        self.feeds = None
        self.rng = self._real_rng

    def tick(self, *args, **kwargs):
        if self.queue is None:
            return super().tick(*args, **kwargs)
        k, ticks, _ = self.queue
        self.feed(k, *ticks.pop(0))
        try:
            super().tick(*args, **kwargs)
        finally:
            self.unfeed()

    def buy(self, card):
        if self.queue is None:
            return super().buy(card)
        k, _, shop = self.queue
        self.feeds, self._real_rng = {"shop": Feed([shop[k].item()])}, self.rng
        try:
            return super().buy(card)
        finally:
            self.unfeed()


class Recorder:
    """Wraps ``VectorEngine.rand`` and keeps every draw."""

    def __init__(self, vec):
        self.draws, self.rand = [], vec.rand
        vec.rand = self

    def __call__(self, *shape):
        t = self.rand(*shape)
        self.draws.append(t)
        return t


SCENARIOS = (
    dict(weapon=R.DRUM, order_timer=0.2),
    dict(weapon=R.PAN, malus=R.SQUID_INVASION, bonus=R.BOMBS, bombs_near=True),
    dict(weapon=R.SAX, malus=R.OVEN_DIMENSION, bonus=R.PILLS, pills_near=True, inventory=(3, 3, 3)),
    dict(weapon=R.DRUM, malus=R.GIANT_SQUIDS, bonus=R.COMPASS, hp=5),
    dict(weapon=R.PAN, malus=R.ALIEN_TOMATOES, bonus=R.PILLS, extra=4),
    dict(weapon=R.SAX, malus=R.FLEEING_ITEMS, bonus=R.BOMBS, bombs_near=True, drops_near=True),
    dict(weapon=R.DRUM, malus=R.MOVING_PORTALS, bonus=R.BOMBS, inventory=(3, 3, 3), hp=5),
    dict(weapon=R.SAX, malus=R.MOVING_PORTALS, bonus=R.PILLS, hp=5, squid_near=True),
    dict(weapon=R.PAN, malus=R.OVEN_DIMENSION, bonus=R.BOMBS, wave_end=150, won=True, pizzas=12),
    dict(weapon=R.DRUM, malus=R.FLEEING_ITEMS, bonus=R.PILLS, wave_end=60, won=True, pizzas=0),
    dict(weapon=R.SAX, malus=R.ALIEN_TOMATOES, bonus=R.COMPASS, wave_end=90, won=False),
)


def make_game(seed, cfg):
    """A headless game set in the situation of ``cfg`` (weapon, malus, bonus, shortcuts)."""
    e = FedEngine(seed)
    p = e.player
    if "malus" in cfg:
        e.extra = cfg.get("extra", 0)
        if e.extra:
            e.spawn(e.extra)
        e._new_round_malus(cfg["malus"])
        e._new_round_bonus(cfg["bonus"])
        e.last_bonus = cfg["bonus"]
    p.weapon = e.last_weapon = cfg["weapon"]
    if cfg.get("bombs_near"):
        for b, (dx, dim) in zip(e.bombs, ((260, 1), (260, 1), (-300, 0), (-300, 1))):
            b.rx, b.ry, b.dim = p.cx + dx, p.cy - 20, dim  # two bombs on one spot explode together
    if cfg.get("pills_near"):
        for q, dx in zip(e.pills, (-250, 300)):
            q.rx, q.ry = p.cx + dx, p.cy + 150
    if cfg.get("drops_near"):
        # Two tomatoes under the player with room for one (inventory cap), others nearby.
        e.res_drops += [Drop(R.TOMATO, p.rx + 20, p.ry + 20), Drop(R.TOMATO, p.rx + 25, p.ry + 20),
                        Drop(R.TOMATO, p.cx + 300, p.cy), Drop(R.TOMATO, p.cx + 330, p.cy + 10),
                        Drop(R.DOUGH, p.cx - 300, p.cy)]
        e.enemy_drops += [Drop(R.TOMATO, p.rx + 10, p.ry + 30, 1), Drop(R.TOMATO, p.cx, p.cy + 400, 1)]
        p.inventory = [0, R.INVENTORY_CAP - 1, 0]
    if cfg.get("squid_near"):
        squid = next(n for n in e.enemies if n.kind == R.SQUID)
        squid.x, squid.y, squid.dim = float(p.cx + 200), float(p.cy - 300), 1
        squid.rx, squid.ry = int(squid.x), int(squid.y)
    if "inventory" in cfg:
        p.inventory = list(cfg["inventory"])
    if "order_timer" in cfg:
        e.orders[0].timer = cfg["order_timer"]
    if "hp" in cfg:
        p.hp = cfg["hp"]
    if "wave_end" in cfg:
        e.wave_timer = cfg["wave_end"] * DT
        e.round_p = e.pizza_goal if cfg["won"] else 0
        e.pizzas_made = cfg["pizzas"] if cfg["won"] else 0
    return e


def decision_ticks(action, frame_skip):
    """The per-tick inputs ``play_decision`` gives ``tick`` for a PLAY decision."""
    kind, (dx, dy), interact, slot = A.decode(action)
    if kind == A.BUY:
        kind, interact = None, False
    out = []
    for i in range(frame_skip):
        if kind == A.COOK:
            out.append(dict(cook=slot if i == 0 else None))
        else:
            out.append(dict(right=dx > 0, left=dx < 0, down=dy > 0, up=dy < 0, interact=interact and i == 0))
    return out


def tick_tensors(inputs):
    dx = torch.tensor([int(t.get("right", False)) - int(t.get("left", False)) for t in inputs])
    dy = torch.tensor([int(t.get("down", False)) - int(t.get("up", False)) for t in inputs])
    interact = torch.tensor([t.get("interact", False) for t in inputs])
    cook = torch.tensor([-1 if t.get("cook") is None else t["cook"] for t in inputs])
    return dx, dy, interact, cook


def assert_same(ref, vec, where, tol=TOL):
    diff = first_difference(state_dict(ref), state_dict(vec), tol)
    assert diff is None, f"{where}: {diff}"


def assert_events(ref, vec, k, where):
    for key in EVENT_KEYS:
        assert abs(ref[key] - vec[key][k].item()) <= TOL, f"{where}: event {key} {ref[key]} != {vec[key][k].item()}"


def coverage_of(cov, e, before, events):
    """Count the mechanics a tick exercised."""
    def count(key, n=1):
        cov[key] = cov.get(key, 0) + int(n)

    p = e.player
    same_wave = e.wave_num == before["wave"] and e.phase == PLAY
    for key in ("deaths", "pizzas", "expired", "kills", "harvested", "picked", "waves", "game_over"):
        count(key, events[key])
    count("hits taken", events["damage"] > 0)
    count("bombs exploded", same_wave and len(e.bombs) < before["bombs"] and before["attached"])
    count("pills taken", same_wave and len(e.pills) < before["pills"])
    count("notes exploded", len(e.notes) < before["notes"])
    count("dash ticks", p.dash_timer > 0)
    count("menu frozen ticks", e.menu_open)
    count("portal switches", e.dim != before["dim"] and not events["deaths"])
    count("upside down ticks", e.dim == 0)
    count("giant squid ticks", any(n.giant for n in e.enemies))
    count("fleeing drops", e.items_flee and before["drops"] != [(d.rx, d.ry) for d in e.res_drops + e.enemy_drops])
    count("moving portal ticks", e.portals[0].moving)
    count("oven dim 0 cooks", e.oven_dim == 0 and events["pizzas"])
    count("projectiles fired", len(e.projectiles) > before["projectiles"])
    count(f"weapon {p.weapon}")
    count(f"malus {e.malus}")
    count(f"bonus {e.bonus}")


def snapshot(e):
    return {"wave": e.wave_num, "bombs": len(e.bombs), "pills": len(e.pills), "notes": len(e.notes),
            "attached": any(b.attached for b in e.bombs), "dim": e.dim, "projectiles": len(e.projectiles),
            "drops": [(d.rx, d.ry) for d in e.res_drops + e.enemy_drops]}


def run_tick_parity(pool, seeds, ticks, frame_skip=6):
    """Tick-level parity over ``SCENARIOS`` (one game per scenario); returns the coverage."""
    n = len(SCENARIOS)
    vec = VectorEngine(n, layouts=pool, seed=seeds[0])
    rec = Recorder(vec)
    games = [make_game(seed, cfg) for seed, cfg in zip(seeds, SCENARIOS)]
    bots = [ScriptedBot(seed) for seed in seeds]
    queues = [[] for _ in range(n)]
    restarts = [0] * n
    cov = {}
    compared = 0
    for t in range(ticks):
        live, inputs = [False] * n, [{} for _ in range(n)]
        for k, e in enumerate(games):
            if e.phase == OVER:
                restarts[k] += 1
                games[k] = e = make_game(seeds[k] + 1000 * restarts[k], {"weapon": SCENARIOS[k]["weapon"]})
                queues[k] = []
            if e.phase == SHOP:
                e.buy(bots[k](e) - A.BUY_BASE)  # real RNG: the next load resynchronises the vector game
                e.pop_events()
                cov["purchases"] = cov.get("purchases", 0) + 1
                continue
            if not queues[k]:
                queues[k] = decision_ticks(bots[k](e), frame_skip)
                e.close_menu()
            live[k] = True
            inputs[k] = queues[k].pop(0)
        for k, e in enumerate(games):
            vec.load(k, e)
        masks = vec.action_mask()
        for k, e in enumerate(games):
            assert masks[k].tolist() == action_mask(e), f"tick {t}, game {k}: action mask"
        rec.draws.clear()
        ev = vec._zero_events()
        vec._tick(torch.tensor(live), *tick_tensors(inputs), ev)
        draws = rec.draws[:4]
        for k, e in enumerate(games):
            if not live[k]:
                continue
            before = snapshot(e)
            e.feed(k, *draws)
            try:
                e.tick(**inputs[k])
            finally:
                e.unfeed()
            events = e.pop_events().as_dict()
            coverage_of(cov, e, before, events)
            got = vec.to_engine(k)
            if e.wave_num != before["wave"]:
                # The roulette ran inside the tick: the new wave comes from the layout pool.
                for field in ("phase", "wave_num", "pizza_goal", "extra", "round_p", "score", "dim"):
                    assert getattr(got, field) == getattr(e, field), f"tick {t}, game {k}: {field} at wave start"
                cov["roulette in tick"] = cov.get("roulette in tick", 0) + 1
                queues[k] = []
                continue
            assert_same(e, got, f"tick {t}, game {k} (seed {seeds[k]})")
            assert_events(events, ev, k, f"tick {t}, game {k}")
            compared += 1
            if e.phase != PLAY:
                queues[k] = []
    cov["compared ticks"] = compared
    return cov


def test_load_to_engine_roundtrip(pool):
    vec = VectorEngine(2, layouts=pool)
    for cfg in SCENARIOS:
        e = make_game(7, cfg)
        vec.load(1, e)
        assert_same(e, vec.to_engine(1), f"roundtrip {cfg}", tol=0)


def test_tick_parity(pool):
    cov = run_tick_parity(pool, seeds=list(range(11, 11 + len(SCENARIOS))), ticks=900)
    print(sorted(cov.items()))
    assert cov["compared ticks"] > 9000
    for weapon in range(len(R.WEAPONS)):
        assert cov.get(f"weapon {weapon}", 0) > 1000
    for malus in range(len(R.MALUSES)):
        assert cov.get(f"malus {malus}", 0) > 500
    for bonus in range(len(R.BONUSES)):
        assert cov.get(f"bonus {bonus}", 0) > 500
    for key in ("deaths", "pizzas", "expired", "kills", "harvested", "picked", "hits taken", "bombs exploded",
                "pills taken", "notes exploded", "dash ticks", "menu frozen ticks", "portal switches",
                "upside down ticks", "giant squid ticks", "fleeing drops", "moving portal ticks", "oven dim 0 cooks",
                "projectiles fired", "waves", "game_over", "purchases", "roulette in tick"):
        assert cov.get(key, 0) > 0, f"not covered: {key}"


def test_step_matches_play_decision(pool):
    """``step`` = ``play_decision`` (menu, cooking frozen ticks, early stop, shop purchases)."""
    scenarios = [SCENARIOS[i] for i in (1, 2, 3, 6, 8)]
    n, frame_skip = len(scenarios), 6
    vec = VectorEngine(n, layouts=pool, seed=3)
    rec = Recorder(vec)
    games = [make_game(100 + k, cfg) for k, cfg in enumerate(scenarios)]
    bots = [ScriptedBot(100 + k) for k in range(n)]
    seen = {"buys": 0, "cooks": 0, "decisions": 0}
    for decision in range(200):
        actions = [bots[k](e) if e.phase != OVER else 0 for k, e in enumerate(games)]
        for k, e in enumerate(games):
            vec.load(k, e)
        rec.draws.clear()
        ev = vec.step(torch.tensor(actions))
        assert len(rec.draws) == STEP_DRAWS + TICK_DRAWS * frame_skip
        ticks = [rec.draws[STEP_DRAWS + TICK_DRAWS * i:STEP_DRAWS + TICK_DRAWS * i + 4] for i in range(frame_skip)]
        for k, e in enumerate(games):
            wave = e.wave_num
            e.queue = (k, list(ticks), rec.draws[0])
            e.slots = {id(x): j for j, x in enumerate(e.enemies)}
            try:
                play_decision(e, actions[k], frame_skip)
            finally:
                e.queue = e.slots = None
            events = e.pop_events().as_dict()
            got = vec.to_engine(k)
            if e.wave_num != wave:
                assert (got.phase, got.wave_num, got.pizza_goal, got.extra) == (e.phase, e.wave_num, e.pizza_goal,
                                                                                 e.extra)
                continue
            assert_same(e, got, f"decision {decision}, game {k}")
            assert_events(events, ev, k, f"decision {decision}, game {k}")
            seen["buys"] += events["buys"]
            seen["cooks"] += events["pizzas"]
            seen["decisions"] += 1
    assert seen["buys"] > 0 and seen["cooks"] > 0 and seen["decisions"] > 900


def test_roulette_matches_headless(pool):
    n = 96
    vec = VectorEngine(n, layouts=pool, seed=5)
    rng = random.Random(1)
    prev = [(rng.choice([None, *range(6)]), rng.randrange(3), rng.choice([None, 0, 1, 2])) for _ in range(n)]
    vec.malus = torch.tensor([-1 if m is None else m for m, _, _ in prev])
    vec.last_weapon = torch.tensor([w for _, w, _ in prev])
    vec.last_bonus = torch.tensor([-1 if b is None else b for _, _, b in prev])
    vec.phase = torch.full((n,), SHOP)
    wave = vec._wave_draws()
    vec._leave_shop(torch.ones(n, dtype=torch.bool), wave)
    for k, (m, w, b) in enumerate(prev):
        spins = [R.ROULETTE_SPIN_MIN + (R.ROULETTE_SPIN_MAX - R.ROULETTE_SPIN_MIN) * u
                 for u in wave["roulette"][k].tolist()]
        maluses = [x for x in range(len(R.MALUSES)) if x != m]
        weapons = [x for x in range(len(R.WEAPONS)) if x != w]
        bonuses = [x for x in range(len(R.BONUSES)) if x != b]
        assert vec.malus[k].item() == maluses[roulette_index(spins[0], len(maluses))]
        assert vec.p_weapon[k].item() == vec.last_weapon[k].item() == weapons[roulette_index(spins[1], len(weapons))]
        assert vec.bonus[k].item() == vec.last_bonus[k].item() == bonuses[roulette_index(spins[2], len(bonuses))]
    assert (vec.phase == PLAY).all() and (vec.wave_num == 2).all()


@pytest.mark.parametrize("extra", [0, 3, 20])
def test_begin_wave_structure(pool, extra):
    combos = [(m, b) for m in range(len(R.MALUSES)) for b in range(len(R.BONUSES))]
    n = len(combos) * 4
    vec = VectorEngine(n, layouts=pool, seed=extra)
    malus = torch.tensor([combos[k % len(combos)][0] for k in range(n)])
    bonus = torch.tensor([combos[k % len(combos)][1] for k in range(n)])
    weapon = torch.arange(n) % 3
    vec.pizza_goal[:] = R.PIZZA_GOAL_MAX
    vec.extra[:] = extra - 1
    wave = vec._wave_draws()
    vec.begin_wave(torch.ones(n, dtype=torch.bool), malus, weapon, bonus, wave)
    lay = {k: torch.as_tensor(v) for k, v in pool.arrays.items()}
    index = vec._layout_index(wave)
    ext = min(extra, vec.max_extra)
    for k in range(n):
        m, b, li = malus[k].item(), bonus[k].item(), index[k].item()
        e = vec.to_engine(k)
        assert e.extra == extra and e.pizza_goal == R.PIZZA_GOAL_MAX and e.wave_num == 2 and e.phase == PLAY
        assert e.player.weapon == e.last_weapon == weapon[k].item() and e.malus == m and e.bonus == b
        squids = [x for x in e.enemies if x.kind == R.SQUID and not x.giant]
        giants = [x for x in e.enemies if x.giant]
        tomatoes = [x for x in e.enemies if x.kind == R.TOMATO_ENEMY]
        n_squid = int(lay["squid_ok"][li, :R.BASE_SQUIDS + ext].sum())
        n_tomato = int(lay["tomato_ok"][li, :R.BASE_TOMATOES + ext].sum())
        assert len(tomatoes) == n_tomato
        assert {x.dim for x in tomatoes} == {0 if m == R.ALIEN_TOMATOES else 1}
        if m == R.GIANT_SQUIDS:
            assert not squids and len(giants) == int(lay["giant_ok"][li].sum())
            assert all(x.size == 192 and x.hp == 225.0 and x.dim == 0 for x in giants)
        elif m == R.SQUID_INVASION:
            assert len([x for x in squids if x.dim == 0]) == n_squid
            assert len([x for x in squids if x.dim == 1]) == int(lay["invasion_ok"][li].sum())
        else:
            assert len(squids) == n_squid and all(x.dim == 0 for x in squids) and not giants
        # List order: squids, tomatoes, then the malus squids.
        kinds = [(x.kind, x.giant, x.dim) for x in e.enemies]
        assert kinds == sorted(kinds, key=lambda t: (t[0] == R.SQUID and (t[1] or t[2] == 1), t[0]))
        assert all(0 <= x.shoot_cd < 2 for x in squids + giants)
        assert all(0.5 <= x.timer < 1.5 and x.state == R.IDLE for x in tomatoes)
        assert len(e.res) == int(lay["res_alive"][li].sum()) and not e.res_drops and not e.projectiles
        assert e.oven_dim == (0 if m == R.OVEN_DIMENSION else 1) and e.items_flee == (m == R.FLEEING_ITEMS)
        assert all(q.moving == (m == R.MOVING_PORTALS) for q in e.portals)
        if b == R.BOMBS:
            assert R.BOMBS_COUNT_MIN - 2 <= len(e.bombs) <= R.BOMBS_COUNT_MAX and not e.pills
        elif b == R.PILLS:
            assert R.PILL_COUNT_MIN - 2 <= len(e.pills) <= R.PILL_COUNT_MAX and not e.bombs
        else:
            assert not e.bombs and not e.pills
        assert len(e.enemies) <= ENEMY_SLOTS
        p = e.player
        assert (p.x, p.y, p.hp, p.inventory) == (float(R.SPAWN_X), float(R.SPAWN_Y), p.max_hp, [0, 0, 0])


def test_goal_progression(pool):
    vec = VectorEngine(1, layouts=pool)
    one = torch.ones(1, dtype=torch.bool)
    goals = []
    for _ in range(7):
        vec.begin_wave(one, torch.tensor([R.FLEEING_ITEMS]), torch.tensor([R.PAN]), torch.tensor([R.COMPASS]))
        goals.append((vec.pizza_goal.item(), vec.extra.item()))
    assert goals == [(5, 0), (7, 0), (9, 0), (10, 0), (10, 1), (10, 2), (10, 3)]
    assert vec.en_count.item() == R.BASE_SQUIDS + R.BASE_TOMATOES + 6


def test_wave_end_shop_and_game_over(pool):
    vec = VectorEngine(3, layouts=pool, seed=9)
    for k, (won, pizzas) in enumerate(((True, 0), (True, 12), (False, 0))):
        e = Engine(k)
        e.wave_timer = 2 * DT
        e.round_p = e.pizza_goal if won else 0
        e.pizzas_made = pizzas
        vec.load(k, e)
    ev = vec.step(torch.zeros(3, dtype=torch.long))
    # Game 0: SHOP with nothing affordable -> roulette -> wave 2, which keeps ticking in this decision.
    assert vec.phase.tolist() == [PLAY, SHOP, OVER]
    assert ev["waves"].tolist() == [1, 1, 0] and ev["game_over"].tolist() == [0, 0, 1]
    assert ev["ticks"].tolist() == [6, 2, 2]
    assert vec.wave_num.tolist() == [2, 1, 1] and vec.pizza_goal.tolist() == [5, 3, 3]
    assert vec.wave_timer[0].item() == pytest.approx(R.WAVE_DURATION - 4 * DT)
    assert vec.wave_timer[1].item() == R.SHOP_DURATION
    shop = vec.to_engine(1)
    assert shop.orders[0] is not None and shop.orders[1:] == [None, None]
    assert len(set(shop.shop_cards)) == 3
    mask = vec.action_mask()
    assert not mask[1, :A.BUY_BASE].any() and mask[1, A.BUY_BASE:].all()
    assert mask[2, :A.COOK_BASE].all() and not mask[2, A.COOK_BASE:].any()
    frozen = {name: getattr(vec, name)[2].clone() for name, _, _ in vec.state_spec()}
    ev = vec.step(torch.full((3,), A.BUY_BASE))
    assert ev["buys"].tolist() == [0, 1, 0] and ev["ticks"][2].item() == 0
    for name, value in frozen.items():
        assert torch.equal(getattr(vec, name)[2], value), name


def test_reset_masks_and_start_state(pool):
    vec = VectorEngine(3, layouts=pool, seed=2)
    vec.step(torch.full((3,), 3))
    before = {name: getattr(vec, name)[1].clone() for name, _, _ in vec.state_spec()}
    vec.reset(torch.tensor([True, False, True]))
    for name, value in before.items():
        assert torch.equal(getattr(vec, name)[1], value), name
    ref, got = state_dict(Engine(0)), state_dict(vec.to_engine(0))
    for key in ("res", "enemies", "orders", "shop_cards"):
        ref.pop(key), got.pop(key)
    assert first_difference(ref, got, 0) is None
    e = vec.to_engine(0)
    assert 40 <= len(e.enemies) <= 43 and len(e.orders) == 3 and e.orders[0] and len(set(e.shop_cards)) == 3


def test_host_branches_do_not_change_results(pool):
    """CPU shortcuts (``_host_branches``) give the CUDA code path's results and random stream."""
    games = []
    for host in (True, False):
        vec = VectorEngine(6, layouts=pool, seed=4)
        vec._host_branches = host
        for k, cfg in enumerate(SCENARIOS[5:]):
            vec.load(k, make_game(50 + k, cfg))
        games.append(vec)
    pick = torch.Generator().manual_seed(0)
    for _ in range(30):
        masks = games[0].action_mask()
        assert torch.equal(masks, games[1].action_mask())
        actions = torch.multinomial(masks.double(), 1, generator=pick)[:, 0]
        events = [vec.step(actions) for vec in games]
        for key in EVENT_KEYS:
            assert torch.equal(events[0][key], events[1][key]), key
        for name, _, _ in games[0].state_spec():
            assert torch.equal(getattr(games[0], name), getattr(games[1], name)), name
        over = games[0].phase == OVER
        for vec in games:
            vec.reset(over)


@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_state_keeps_dtype_and_shape(pool, dtype):
    """Static buffers for CUDA graphs: every state tensor keeps its dtype and shape."""
    vec = VectorEngine(8, layouts=pool, dtype=dtype, seed=1)
    vec._host_branches = False
    for k, cfg in enumerate(SCENARIOS[:8]):
        vec.load(k, make_game(70 + k, cfg))
    spec = {name: (getattr(vec, name).dtype, getattr(vec, name).shape) for name, _, _ in vec.state_spec()}
    pick = torch.Generator().manual_seed(1)
    for _ in range(25):
        actions = torch.multinomial(vec.action_mask().to(dtype), 1, generator=pick)[:, 0]
        ev = vec.step(actions)
        assert all(v.dtype == dtype and v.shape == (8,) for v in ev.values())
        vec.reset(vec.phase == OVER)
        for name, expected in spec.items():
            assert (getattr(vec, name).dtype, getattr(vec, name).shape) == expected, name
    assert torch.isfinite(vec.p_x).all() and torch.isfinite(vec.en_x).all()
