
"""Only works for PCM ints"""

from math import sin, tau
from typing import Callable, Iterator

IterMono = Iterator[float]

IterPoly = Iterator[tuple[float]]
ListPoly = list[tuple[float]]

ListPolyInt = list[tuple[int]]  # Output format

SAMPLE_RATE = 48000

# ======================

def do_reverse(track: ListPoly) -> None:
    track.reverse()

def track_reversed(track: ListPoly) -> IterPoly:
    return reversed(track)

def shape_volume_mul(track: IterMono | IterPoly, t_volume_func: Callable[[float], float], *, start_t: float = 0) -> IterPoly:
    t = start_t
    dt = 1/SAMPLE_RATE

    for sample in track:
        vol = t_volume_func(t)
        t += dt
        yield tuple(channel*vol for channel in sample) if isinstance(sample, tuple) else sample*vol

