from __future__ import annotations

import argparse
import gc
import statistics
import time
from collections.abc import Callable
from typing import Any

from bench_overhead import FakeWidget

from taut import nodes

# Measures cost of adding owner context to a teeny callback

def time_callback(callback: Callable[[int], Any], iterations: int) -> float:
    started = time.perf_counter()
    for value in range(iterations):
        callback(value)
    return time.perf_counter() - started


def sample_callback(
    callback: Callable[[int], Any],
    *,
    iterations: int,
    repeats: int,
    warmups: int,
) -> list[float]:
    for _ in range(warmups):
        time_callback(callback, max(1, iterations // 10))

    was_enabled = gc.isenabled()
    gc.disable()
    try:
        return [time_callback(callback, iterations) for _ in range(repeats)]
    finally:
        if was_enabled:
            gc.enable()


def benchmark_callback_dispatch(
    *, iterations: int, repeats: int, warmups: int
) -> None:
    received = 0

    def callback(value: int) -> None:
        nonlocal received
        received = value

    node = nodes.WidgetNode(FakeWidget)
    cases = [
        ("direct callback", callback),
        ("owned callback", node.owned_callback(callback)),
    ]
    results: dict[str, float] = {}

    print(f"callback dispatch: {iterations:,} calls/sample, {repeats} samples")
    print()
    print(f"{'case':<22} {'median/sample':>15} {'per call':>14}")
    print("-" * 53)
    for name, fn in cases:
        samples = sample_callback(
            fn,
            iterations=iterations,
            repeats=repeats,
            warmups=warmups,
        )
        median = statistics.median(samples)
        results[name] = median
        print(
            f"{name:<22} {median * 1_000_000:>12,.1f} us "
            f"{median / iterations * 1_000_000_000:>11,.1f} ns"
        )

    direct = results["direct callback"]
    owned = results["owned callback"]
    extra_ns = (owned - direct) / iterations * 1_000_000_000
    ratio = owned / direct if direct else float("inf")
    print()
    print(f"owner restoration overhead: {ratio:.2f}x, +{extra_ns:,.1f} ns/call")
    assert received == iterations - 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark owner restoration overhead for Taut callbacks."
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1_000_000,
        help="callback dispatches per sample",
    )
    parser.add_argument("--repeats", type=int, default=7, help="timed samples")
    parser.add_argument("--warmups", type=int, default=2, help="untimed samples")
    args = parser.parse_args()

    benchmark_callback_dispatch(
        iterations=args.iterations,
        repeats=args.repeats,
        warmups=args.warmups,
    )


if __name__ == "__main__":
    main()
