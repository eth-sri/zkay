def zk__div(a: int, b: int) -> int:
    if (a < 0) ^ (b < 0):
        return -(-a // b)
    else:
        return a // b


def zk__mod(a: int, b: int) -> int:
    sign = -1 if a < 0 else 1
    abs_res = abs(a) % abs(b)
    return sign * abs_res
