"""Pool of wave layouts for the vector engine, drawn by the headless spawn code.

A wave starts with ``WorldManager.spawn`` (resources, squids, tomatoes), then the
malus (invasion squids, giant squids) and the bonus (bombs, pills). Its
rejection sampling (``_random_spot`` + ``is_safe``, up to 50 tries per entity) is
sequential and data dependent, so the vector engine does not run it: it draws a
layout from a pool produced here, in worker processes, by the headless
engine's own code, and cached on disk.

One layout is ``Engine(seed)`` (``Game.start()``: resources spawned with the
default portal positions) plus i.i.d. candidate spots for every other entity,
each with a ``placed`` flag (``False`` when the 50 tries all failed, like the
game which then skips that entity). Spots only test the resources, the portals
and the oven, exactly like ``is_safe``, so they are independent of each other:

=========  =====================  =========  ================================
group      spots                  safe size  used for
=========  =====================  =========  ================================
squid      15 + max_extra         100        ``spawn``: first 15 + extra spots
tomato     28 + max_extra         80         ``spawn``: first 28 + extra spots
invasion   5                      100        SQUID_INVASION malus (dim 1)
giant      8                      200        GIANT_SQUIDS malus
bomb       8                      50         BOMBS bonus: first randint(6, 8)
pill       8                      50         PILLS bonus: first randint(5, 8)
=========  =====================  =========  ================================

Known approximation: the game spawns the next wave with the portals where they
are (displaced after the moving-portals malus); the pool always uses the
default positions.
"""

import hashlib
import inspect
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from ..headless import engine as H
from ..headless import rules as R

POOL_VERSION = 1
MAX_EXTRA = 12
DEFAULT_POOL_SIZE = 4096
DEFAULT_CACHE_DIR = Path(__file__).resolve().parents[2] / "runs" / "cache"
SPOT_GROUPS = ("squid", "tomato", "invasion", "giant", "bomb", "pill")


def spot_table(max_extra):
    """``{group: (count, safe size)}`` in generation order."""
    return {
        "squid": (R.BASE_SQUIDS + max_extra, 100),
        "tomato": (R.BASE_TOMATOES + max_extra, 80),
        "invasion": (R.INVASION_SQUIDS, 100),
        "giant": (R.GIANT_SQUID_COUNT, 200),
        "bomb": (R.BOMBS_COUNT_MAX, 50),
        "pill": (R.PILL_COUNT_MAX, 50),
    }


def generate_layout(seed, max_extra=MAX_EXTRA):
    """One layout (dict of numpy arrays) from ``random.Random(seed)``."""
    eng = H.Engine(seed)
    count = len(eng.res)
    if count > R.MAX_RESOURCES:
        raise ValueError("more resources than RES_SLOTS")
    out = {
        "res_alive": np.zeros(R.MAX_RESOURCES, dtype=bool),
        "res_kind": np.zeros(R.MAX_RESOURCES, dtype=np.int64),
        "res_rx": np.zeros(R.MAX_RESOURCES, dtype=np.int64),
        "res_ry": np.zeros(R.MAX_RESOURCES, dtype=np.int64),
    }
    out["res_alive"][:count] = True
    out["res_kind"][:count] = [r.kind for r in eng.res]
    out["res_rx"][:count] = [r.rx for r in eng.res]
    out["res_ry"][:count] = [r.ry for r in eng.res]
    for group, (spots, size) in spot_table(max_extra).items():
        xs, ys, placed = np.zeros(spots), np.zeros(spots), np.zeros(spots, dtype=bool)
        for k in range(spots):
            for _ in range(R.SPAWN_TRIES):
                x, y = eng._random_spot()
                if eng.is_safe(x, y, size):
                    xs[k], ys[k], placed[k] = x, y, True
                    break
        out[f"{group}_x"], out[f"{group}_y"], out[f"{group}_ok"] = xs, ys, placed
    return out


class LayoutPool:
    """Stacked layouts: ``arrays[name]`` has a leading dimension ``size``."""

    def __init__(self, arrays, max_extra):
        self.arrays = arrays
        self.max_extra = max_extra
        self.size = len(arrays["res_alive"])

    @classmethod
    def generate(cls, size, max_extra=MAX_EXTRA, seed=0, workers=0):
        seeds = [f"cuisto-layout:{seed}:{k}" for k in range(size)]
        if workers:
            with ProcessPoolExecutor(workers) as pool:
                layouts = list(pool.map(generate_layout, seeds, [max_extra] * size,
                                        chunksize=max(1, size // (4 * workers))))
        else:
            layouts = [generate_layout(s, max_extra) for s in seeds]
        arrays = {name: np.stack([lay[name] for lay in layouts]) for name in layouts[0]}
        return cls(arrays, max_extra)


def pool_key(size, max_extra, seed):
    """Cache key: rules, headless engine source, pool parameters."""
    digest = hashlib.sha256()
    for module in (R, H):
        digest.update(inspect.getsource(module).encode())
    digest.update(f"v{POOL_VERSION}:{size}:{max_extra}:{seed}".encode())
    return digest.hexdigest()[:16]


def load_pool(size=DEFAULT_POOL_SIZE, max_extra=MAX_EXTRA, seed=0, cache_dir=DEFAULT_CACHE_DIR, workers=None):
    """The pool from ``cache_dir`` (``None``: no cache), generated on a miss.

    ``workers=None`` uses up to 8 processes for large pools, 0 runs in-process.
    """
    path = None
    if cache_dir is not None:
        path = Path(cache_dir) / f"layouts-{pool_key(size, max_extra, seed)}.npz"
        if path.exists():
            with np.load(path) as data:
                return LayoutPool({name: data[name] for name in data.files}, max_extra)
    if workers is None:
        workers = min(8, os.cpu_count() or 1) if size >= 256 else 0
    pool = LayoutPool.generate(size, max_extra, seed, workers)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.stem + f".{os.getpid()}.tmp.npz")
        np.savez_compressed(tmp, **pool.arrays)
        os.replace(tmp, path)
    return pool
