
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
