"""Comparable snapshots of headless engines, without pygame (``rl.bridge`` needs it).

Same fields as ``rl.bridge.state_dict``. Projectiles are sorted: the vector
engine keeps them in any free slot (their order has no effect on the rules).
"""


def state_dict(e):
    """All gameplay state of an ``Engine`` as plain comparable values (cosmetics excluded)."""
    p = e.player
    return {
        "phase": e.phase, "wave_num": e.wave_num, "wave_timer": e.wave_timer, "score": e.score,
        "pizza_goal": e.pizza_goal, "round_p": e.round_p, "extra": e.extra, "pizzas_made": e.pizzas_made,
        "menu_open": e.menu_open, "last_weapon": e.last_weapon, "last_bonus": e.last_bonus,
        "malus": e.malus, "bonus": e.bonus, "pill_timer": e.pill_timer,
        "orders": [(o.recipe, o.max_time, o.timer) if o else None for o in e.orders],
        "time_mult": e.time_mult, "spawn_timer": e.spawn_timer,
        "upgrade_costs": list(e.upgrade_costs), "shop_cards": list(e.shop_cards),
        "dim": e.dim, "in_portal": e.in_portal, "items_flee": e.items_flee,
        "oven": (e.oven_dim, e.oven_active), "cd": (e.cd, e.cd_limit, e.cd_limit_mult),
        "player": (p.x, p.y, p.rx, p.ry, p.vel, p.hp, p.max_hp, p.inv_timer, p.last_dx, p.last_dy,
                   p.dash_timer, p.dash_vx, p.dash_vy, p.speed_mult, tuple(p.inventory), p.cap, p.weapon),
        "portals": [(q.x, q.y, q.rx, q.ry, q.moving, q.vx, q.vy, q.tvx, q.tvy, q.move_timer) for q in e.portals],
        "notes": [(n.x, n.y, n.dx, n.dy, n.timer) for n in e.notes],
        "res": [(r.kind, r.rx, r.ry, r.hp, r.hit_timer) for r in e.res],
        "res_drops": [(d.kind, d.rx, d.ry, d.dim) for d in e.res_drops],
        "enemy_drops": [(d.kind, d.rx, d.ry, d.dim) for d in e.enemy_drops],
        "enemies": [(n.kind, n.giant, n.x, n.y, n.rx, n.ry, n.size, n.hp, n.max_hp, n.hit_timer, n.dim,
                     n.shoot_cd, n.move_state, n.move_timer, n.wx, n.wy, n.state, n.timer, n.vx, n.vy)
                    for n in e.enemies],
        "projectiles": sorted((q.x, q.y, q.rx, q.ry, q.size, q.vx, q.vy, q.timer, q.dim) for q in e.projectiles),
        "bombs": [(b.rx, b.ry, b.dim, b.attached, b.timer) for b in e.bombs],
        "pills": [(q.rx, q.ry) for q in e.pills],
    }


def first_difference(a, b, tol=1e-9, path="state"):
    """Path and values of the first mismatch (floats within ``tol``), or None."""
    if a == b:
        return None
    if isinstance(a, dict):
        for key in a:
            found = first_difference(a[key], b[key], tol, f"{path}.{key}")
            if found:
                return found
        return None
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return f"{path}: length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            found = first_difference(x, y, tol, f"{path}[{i}]")
            if found:
                return found
        return None
    if isinstance(a, float) or isinstance(b, float):
        if a is None or b is None or abs(a - b) > tol:
            return f"{path}: {a!r} != {b!r}"
        return None
    return None if a == b else f"{path}: {a!r} != {b!r}"
