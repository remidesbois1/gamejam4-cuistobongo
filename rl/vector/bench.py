"""Throughput of ``VectorEngine.step`` with uniformly random valid actions.

    python -m rl.vector.bench --envs 1024 --decisions 200
"""

import argparse
import time

import torch

from .engine import OVER, VectorEngine
from .layouts import load_pool

DTYPES = {"float64": torch.float64, "float32": torch.float32}


def bench(envs, decisions, device, dtype, pool, warmup=5, seed=0):
    vec = VectorEngine(envs, device=device, dtype=dtype, layouts=pool, seed=seed)
    pick = torch.Generator(device=vec.device).manual_seed(seed)

    def run(count):
        for _ in range(count):
            actions = torch.multinomial(vec.action_mask().to(dtype), 1, generator=pick)[:, 0]
            vec.step(actions)
            vec.reset(vec.phase == OVER)

    run(warmup)
    if vec.device.type == "cuda":
        torch.cuda.synchronize()
    start = time.perf_counter()
    run(decisions)
    if vec.device.type == "cuda":
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    return envs * decisions / elapsed, elapsed


def main(argv=None):
    parser = argparse.ArgumentParser(description="VectorEngine decisions per second")
    parser.add_argument("--envs", type=int, default=1024)
    parser.add_argument("--decisions", type=int, default=200)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--dtype", choices=[*DTYPES, "both"], default="both")
    parser.add_argument("--pool", type=int, default=None, help="layout pool size (default: the engine default)")
    parser.add_argument("--threads", type=int, default=None, help="torch CPU threads")
    args = parser.parse_args(argv)
    if args.threads:
        torch.set_num_threads(args.threads)
    pool = load_pool() if args.pool is None else load_pool(args.pool)
    names = list(DTYPES) if args.dtype == "both" else [args.dtype]
    for name in names:
        rate, elapsed = bench(args.envs, args.decisions, args.device, DTYPES[name], pool)
        print(f"{args.device} {name}: {args.envs} envs x {args.decisions} decisions in {elapsed:.1f}s "
              f"-> {rate:,.0f} decisions/s")


if __name__ == "__main__":
    main()
