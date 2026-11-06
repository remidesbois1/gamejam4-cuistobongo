"""Observation ``CuistoBongo-v1``: a fixed-size vector computed on the device from engine tensors.

Egocentric: entity positions are relative to the centre of the player, in
screen units (x / 1280, y / 800), so a situation looks the same anywhere on the
map; the player's absolute position on the map is given once. Variable lists
(enemies, resources, drops...) become the ``k`` nearest entities, sorted by
distance, each with a presence flag. Everything the game shows a human (bag,
orders and their timers, wave timer, malus, bonus, shop cards) is included,
plus exact timers a human only sees indirectly (cooldowns, tomato states).

The schema is versioned: changing a segment, its order or its meaning needs a
new ``SCHEMA`` (old checkpoints become incompatible).
"""

import torch

from ..actions import ACTION_COUNT
from ..headless import rules as R

SCHEMA = "CuistoBongo-v1"

K_DANGER = 8   # nearest enemies in the player's dimension
K_TOMATO = 6   # nearest tomato enemies, any dimension (targets)
K_PROJ = 8     # nearest projectiles in the player's dimension
K_RES = 6      # nearest trees and nearest cheese ores (each)
K_DROP = 8     # nearest dropped ingredients (both managers)
K_BOMB = 4
K_PILL = 4
K_NOTE = 2

SX, SY = 1280.0, 800.0
FAR = 1e9

SEGMENTS = (
    ("player", 24),
    ("context", 24 + 7 + 4),
    ("oven", 5),
    ("orders", 3 * 13),
    ("shop", 3 * 7 + 5),
    ("portals", 4 * 7),
    ("danger", K_DANGER * 19),
    ("tomatoes", K_TOMATO * 6),
    ("projectiles", K_PROJ * 7),
    ("resources", 2 * K_RES * 5),
    ("drops", K_DROP * 9),
    ("bombs", K_BOMB * 6),
    ("pills", K_PILL * 3),
    ("notes", K_NOTE * 4),
)
FEATURE_SIZE = sum(size for _, size in SEGMENTS)
SLICES = {}
_start = 0
for _name, _size in SEGMENTS:
    SLICES[_name] = slice(_start, _start + _size)
    _start += _size

_TABLES = {}


def _tables(device, dtype):
    key = (device, dtype)
    if key not in _TABLES:
        _TABLES[key] = {
            "need": torch.tensor([r[1] for r in R.RECIPES], device=device, dtype=torch.long),
            "points": torch.tensor([r[2] for r in R.RECIPES], device=device, dtype=dtype),
            "res_half": torch.tensor([[t[4] // 2, t[5] // 2] for t in R.RESOURCE_TYPES], device=device,
                                     dtype=torch.long),
        }
    return _TABLES[key]


def _onehot(index, n):
    """One-hot of ``index`` (any shape) without ``F.one_hot`` (comparison only, graph friendly)."""
    return (index.unsqueeze(-1) == torch.arange(n, device=index.device)).float()


def _nearest(dist, valid, k):
    """Indices [N, k] of the ``k`` smallest distances among valid slots, and their validity."""
    k = min(k, dist.shape[1])
    d = torch.where(valid, dist, torch.full_like(dist, FAR))
    value, idx = torch.topk(d, k, dim=1, largest=False)
    return idx, value < FAR


def _pad(t, k):
    """Pad the slot axis (dim 1) with zero rows up to ``k``."""
    if t.shape[1] == k:
        return t
    return torch.cat((t, t.new_zeros(t.shape[0], k - t.shape[1], *t.shape[2:])), dim=1)


def _rows(ok, *columns):
    """[N, k, C] block of float columns, zeroed where the slot is empty."""
    block = torch.stack([c.float() for c in (ok, *columns)], dim=-1)
    return block * ok.unsqueeze(-1).float()


def player_centre(e):
    half = R.PLAYER_SIZE // 2
    return (e.p_rx + half).to(e.p_x.dtype), (e.p_ry + half).to(e.p_x.dtype)


def orders_missing(e):
    """[N, 3, 3] ingredients still missing per order slot, and [N, 3] cookable-with-bag flags."""
    t = _tables(e.p_x.device, e.p_x.dtype)
    need = t["need"][e.order_recipe]
    missing = (need - e.p_inventory.unsqueeze(1)).clamp(min=0)
    ready = e.order_alive & (missing.sum(-1) == 0)
    return missing * e.order_alive.unsqueeze(-1), ready


@torch.no_grad()
def encode(e):
    """float32 [N, FEATURE_SIZE] observation of a ``VectorEngine``."""
    t = _tables(e.p_x.device, e.p_x.dtype)
    n = e.p_x.shape[0]
    pcx, pcy = player_centre(e)
    dim = e.dim

    def rel(cx, cy):
        dx = (cx.to(pcx.dtype) - pcx.unsqueeze(1))
        dy = (cy.to(pcy.dtype) - pcy.unsqueeze(1))
        return dx, dy, torch.sqrt(dx * dx + dy * dy)

    parts = []
    # Player (24)
    inv = e.p_inventory.float()
    cap = e.p_cap.float().unsqueeze(1)
    parts += [torch.stack([
        pcx / R.MAP_W, pcy / R.MAP_H, e.p_hp / e.p_max_hp, e.p_max_hp / R.PLAYER_HP,
        e.p_inv_timer.clamp(min=0), e.p_dash_timer / R.DASH_TIME, e.p_last_dx, e.p_last_dy,
        e.p_vel / R.PLAYER_SPEED, e.p_speed_mult - 1, e.cd, e.cd_limit / R.CD_LIMIT,
        (e.cd <= 0).to(e.cd.dtype), e.menu_open.to(e.cd.dtype), e.p_cap / R.INVENTORY_CAP,
    ], dim=1).float(), inv / cap, (inv >= cap).float(), _onehot(e.p_weapon, 3)]

    # Context (24 + 7 + 4)
    remaining = (e.pizza_goal - e.round_p).clamp(min=0).float()
    seconds_left = e.wave_timer.float().clamp(min=1)
    parts += [torch.stack([
        (e.phase == 0).float(), (e.phase == 1).float(), e.wave_timer.float() / R.WAVE_DURATION,
        e.wave_num.float() / 10, e.pizza_goal.float() / 10, e.round_p.float() / 10, remaining / 10,
        remaining * 60 / seconds_left / 10, e.pizzas_made.float() / 10, e.extra.float() / 10, dim.float(),
        e.oven_dim.float(), e.oven_active.float(), e.in_portal.float(), e.items_flee.float(),
        e.pill_timer.float() / R.PILL_DURATION_TIME, e.time_mult.float(), e.cd_limit_mult.float(),
        e.spawn_timer.float() / R.ORDER_SPAWN_TIME, e.order_alive.float().sum(1) / 3,
        e.p_inventory.sum(1).float() / 9, e.score.float() / 1000, e.p_cap.float() / 10,
        e.menu_open.float(),
    ], dim=1), _onehot(torch.where(e.malus < 0, 6, e.malus), 7), _onehot(torch.where(e.bonus < 0, 3, e.bonus), 4)]

    # Oven (5)
    odx, ody, od = rel(torch.full_like(e.p_rx, R.OVEN_CX).unsqueeze(1), torch.full_like(e.p_ry, R.OVEN_CY).unsqueeze(1))
    parts.append(torch.cat([odx / SX, ody / SY, od / 2000, (e.oven_dim == dim).unsqueeze(1).to(od.dtype),
                            (od < R.OVEN_ACTIVE_DIST).to(od.dtype)], dim=1).float())

    # Orders (3 x 13)
    missing, ready = orders_missing(e)
    frac = (e.order_timer / e.order_max_time.clamp(min=1e-6)).clamp(min=0)
    value = t["points"][e.order_recipe] * frac.clamp(min=0.5) / 100
    need = t["need"][e.order_recipe].float()
    orders = torch.cat([
        e.order_alive.unsqueeze(-1).float(), _onehot(e.order_recipe, 4), frac.unsqueeze(-1).float(),
        (e.order_timer / 50).unsqueeze(-1).float(), missing.float(), ready.unsqueeze(-1).float(),
        value.unsqueeze(-1).float(), need.sum(-1, keepdim=True) / 3,
    ], dim=-1) * e.order_alive.unsqueeze(-1).float()
    parts.append(orders.reshape(n, -1))

    # Shop (3 x 7 + 5)
    cost = e.upgrade_costs.gather(1, e.shop_cards)
    affordable = (e.phase == 1).unsqueeze(1) & (e.pizzas_made.unsqueeze(1) >= cost)
    cards = torch.cat([_onehot(e.shop_cards, 5), (cost.float() / 10).unsqueeze(-1), affordable.unsqueeze(-1).float()],
                      dim=-1)
    parts += [cards.reshape(n, -1), e.upgrade_costs.float() / 10]

    # Portals (4 x 7)
    half = R.PORTAL_SIZE // 2
    pdx, pdy, pd = rel(e.portal_rx + half, e.portal_ry + half)
    parts.append(torch.stack([pdx / SX, pdy / SY, pd / 2000, e.portal_moving.to(pd.dtype), (pd < 64).to(pd.dtype),
                              e.portal_vx / 250, e.portal_vy / 250], dim=-1).float().reshape(n, -1))

    # Enemies near, in the player's dimension (K_DANGER x 19)
    ehalf = e.en_size // 2
    edx, edy, ed = rel(e.en_rx + ehalf, e.en_ry + ehalf)
    idx, ok = _nearest(ed, e.en_alive & (e.en_dim == dim.unsqueeze(1)), K_DANGER)
    g = lambda x: x.gather(1, idx)
    kind = g(e.en_kind)
    giant = g(e.en_giant)
    is_tomato = kind == R.TOMATO_ENEMY
    danger = torch.cat([
        _rows(ok, g(edx) / SX, g(edy) / SY, g(ed) / 1000, is_tomato, (kind == R.SQUID) & ~giant, giant,
              g(e.en_hp) / g(e.en_max_hp).clamp(min=1), g(e.en_hit_timer) > 0, g(e.en_vx) / R.TOMATO_ROLL_SPEED,
              g(e.en_vy) / R.TOMATO_ROLL_SPEED, torch.where(is_tomato, g(e.en_timer), g(e.en_shoot_cd)) / 2,
              g(e.en_move_timer) * ~is_tomato),
        _onehot(g(e.en_state), 6) * (ok & is_tomato).unsqueeze(-1).float(),
    ], dim=-1)
    parts.append(_pad(danger, K_DANGER).reshape(n, -1))

    # Tomato enemies, any dimension (K_TOMATO x 6)
    idx, ok = _nearest(ed, e.en_alive & (e.en_kind == R.TOMATO_ENEMY), K_TOMATO)
    tomatoes = _rows(ok, g(edx) / SX, g(edy) / SY, g(ed) / 2000, g(e.en_dim) == dim.unsqueeze(1),
                     g(e.en_hp) / R.TOMATO_HP)
    parts.append(_pad(tomatoes, K_TOMATO).reshape(n, -1))

    # Projectiles in the player's dimension (K_PROJ x 7)
    qhalf = e.proj_size // 2
    qdx, qdy, qd = rel(e.proj_rx + qhalf, e.proj_ry + qhalf)
    idx, ok = _nearest(qd, e.proj_alive & (e.proj_dim == dim.unsqueeze(1)), K_PROJ)
    projectiles = _rows(ok, g(qdx) / SX, g(qdy) / SY, g(e.proj_vx) / R.PROJECTILE_SPEED,
                        g(e.proj_vy) / R.PROJECTILE_SPEED, g(e.proj_size) / (3 * R.PROJECTILE_SIZE),
                        g(e.proj_timer) / R.PROJECTILE_LIFETIME)
    parts.append(_pad(projectiles, K_PROJ).reshape(n, -1))

    # Resources: nearest trees, nearest cheese ores (2 x K_RES x 5)
    rhalf = t["res_half"][e.res_kind]
    rdx, rdy, rd = rel(e.res_rx + rhalf[..., 0], e.res_ry + rhalf[..., 1])
    blocks = []
    for kind_id, max_hp in ((R.TREE, R.RESOURCE_TYPES[0][6]), (R.CHEESE_ORE, R.RESOURCE_TYPES[1][6])):
        idx, ok = _nearest(rd, e.res_alive & (e.res_kind == kind_id), K_RES)
        blocks.append(_pad(_rows(ok, g(rdx) / SX, g(rdy) / SY, g(e.res_hp) / max_hp, g(e.res_hit_timer) > 0),
                           K_RES).reshape(n, -1))
    parts += blocks

    # Drops of both managers (K_DROP x 9)
    dhalf = R.DROP_SIZE // 2
    a_dx, a_dy, a_d = rel(e.rdrop_rx + dhalf, e.rdrop_ry + dhalf)
    b_dx, b_dy, b_d = rel(e.edrop_rx + dhalf, e.edrop_ry + dhalf)
    kinds = torch.cat([e.rdrop_kind, torch.full_like(e.edrop_rx, R.TOMATO)], dim=1)
    # Resource-manager drops are visible in dimension 1 for tomatoes, 0 otherwise.
    drop_dim = torch.cat([(e.rdrop_kind == R.TOMATO).long(), e.edrop_dim], dim=1)
    ddx, ddy, dd = torch.cat([a_dx, b_dx], 1), torch.cat([a_dy, b_dy], 1), torch.cat([a_d, b_d], 1)
    idx, ok = _nearest(dd, torch.cat([e.rdrop_alive, e.edrop_alive], 1), K_DROP)
    dk = g(kinds)
    full = e.p_inventory.gather(1, dk) >= e.p_cap.unsqueeze(1)
    drops = torch.cat([_rows(ok, g(ddx) / SX, g(ddy) / SY, g(dd) / 2000, g(drop_dim) == dim.unsqueeze(1), full),
                       _onehot(dk, 3) * ok.unsqueeze(-1).float()], dim=-1)
    parts.append(_pad(drops, K_DROP).reshape(n, -1))

    # Bombs (K_BOMB x 6) and pills (K_PILL x 3)
    bhalf = R.BOMB_SIZE // 2
    bdx, bdy, bd = rel(e.bomb_rx + bhalf, e.bomb_ry + bhalf)
    idx, ok = _nearest(bd, e.bomb_alive, K_BOMB)
    bombs = _rows(ok, g(bdx) / SX, g(bdy) / SY, g(e.bomb_dim) == dim.unsqueeze(1), g(e.bomb_attached),
                  g(e.bomb_timer) / R.BOMB_FUSE)
    parts.append(_pad(bombs, K_BOMB).reshape(n, -1))
    lhalf = R.PILL_SIZE // 2
    ldx, ldy, ld = rel(e.pill_rx + lhalf, e.pill_ry + lhalf)
    idx, ok = _nearest(ld, e.pill_alive, K_PILL)
    parts.append(_pad(_rows(ok, g(ldx) / SX, g(ldy) / SY), K_PILL).reshape(n, -1))

    # Saxophone notes in flight (K_NOTE x 4)
    ndx, ndy, nd = rel(e.note_x, e.note_y)
    idx, ok = _nearest(nd, e.note_alive, K_NOTE)
    parts.append(_pad(_rows(ok, g(ndx) / SX, g(ndy) / SY, g(e.note_timer) / R.NOTE_TIME), K_NOTE).reshape(n, -1))

    obs = torch.cat([p.float() for p in parts], dim=1)
    return obs


__all__ = ["ACTION_COUNT", "FEATURE_SIZE", "SCHEMA", "SEGMENTS", "SLICES", "encode", "orders_missing",
           "player_centre"]
