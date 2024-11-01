
from itertools import islice
from typing import Callable, Iterator


def clamp(x: int, a: int, b: int) -> int:
    if x < a:
        return a
    if b < x:
        return b
    return x

def interval_to_int(x: float) -> int:
    assert -1 <= x <= 1
    # if x < -1 or 1 < x:
    #     raise ValueError(f"{x=}")
    r = int(x * (1 << 15))
    return clamp(r, -(1 << 15), (1 << 15)-1)

def int_to_interval(x: int) -> float:
    ret = x / (1<<15)
    # print(ret)
    assert -1 <= ret <= 1
    return ret

def min_and_max(values: list[float]) -> tuple[float, float]:
    valit = iter(values)
    mi = ma = next(valit)
    for val in valit:
        if val < mi:
            mi = val
            continue
        if val > ma:
            ma = val
    return mi, ma

def rescale_values(
        values: list[float], *,
        hi: float, lo: float = 0,
        source_hi: float | None = None, source_lo : float | None = 0
    ) -> list[float]:
    # lowest and highest point in the data
    scan_lo, scan_hi = min_and_max(values)
    # lowest and highest point in the domain
    real_lo = scan_lo if source_lo is None else source_lo
    real_hi = scan_hi if source_hi is None else source_hi

    factor = (hi - lo) / (real_hi - real_lo)
    return [(val - real_lo) * factor + lo for val in values]

def iter_skip(it: Iterator, skip_n: int) -> int:
    """returns the actual number of skipped elements"""
    if skip_n == 0:
        return 0
    i = 0
    for _ in it:
        i+= 1
        if i == skip_n:
            return skip_n
    return i

def windowed(it: Iterator[float], size: int, step: int = 1) -> Iterator[list[float]]:
    """like a sliding window over the iterator\n
    size: size of the window\n
    step: number of elements between starts of windows"""

    modus_step_pop = step >= size # Step mode if True, else Pop mode
    popnum = min(step, size)
    jumpnum = max(0, step-size)
    print(f"{popnum=} {jumpnum=}")

    # MODES:
    # Step Mode: reset win, win = islice(it, size), size assertion, yield
    # Pop Mode:  Pop (popnum) and append (popnum) new elements, then yield

    win = list(islice(it, size))
    if len(win) != size:
        return

    while True:
        yield win
        # cut off the front: only leaves elements in win if step < size
        win = win[popnum:]
        # skip elements between windows (if step >= size)
        skipped = iter_skip(it, jumpnum)
        if skipped != jumpnum: return
        # append new elements
        new_win_end = list(islice(it, popnum))
        # print()
        if len(new_win_end) != popnum: return
        win += new_win_end

FFFunc = Callable[[float], float]

def forward_function(funcs: list[FFFunc], borders: list[float]) -> FFFunc:
    """Eine Funktion, die an aufsteigenden Positionen abgetastet wird"""
    assert len(funcs) == len(borders) + 1
    current_fun = funcs.pop(0)
    current_border = borders.pop(0)
    end = len(borders) == 0
    def fun(t: float) -> float:
        nonlocal current_fun, current_border, end
        if not end and t > current_border:
            print(f"switching to next function! ({t=})")
            current_fun = funcs.pop(0)
            current_border = borders.pop(0)
            end = len(borders) == 0
        return current_fun(t)
    return fun