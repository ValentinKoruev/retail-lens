import time
from contextlib import contextmanager

TIMINGS: dict[str, float] = {}


@contextmanager
def timed(stage: str):
    start = time.perf_counter()
    print(f"[{stage}] starting...")
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        TIMINGS[stage] = elapsed
        print(f"[{stage}] done in {elapsed:.2f}s")
