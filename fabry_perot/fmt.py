import math

import numpy as np

SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def num(x, digits=4):
    if x is None:
        return "—"
    if isinstance(x, (int, np.integer)):
        return f"{x:,}".replace(",", " ")
    if not math.isfinite(x):
        return "—"
    if x == 0:
        return "0"
    power = math.floor(math.log10(abs(x)))
    if -3 <= power < 6:
        text = f"{x:,.{max(digits - 1 - power, 0)}f}".replace(",", " ")
    else:
        text = f"{x / 10 ** power:.{digits - 1}f}·10" + str(power).translate(SUP)
    return text.replace(".", ",").replace("-", "−")


def short(x):
    return f"{x:g}".replace(".", ",")


def plain(x):
    return "" if x is None else f"{x:.6g}".replace(".", ",")


def pick_unit(x):
    for unit, scale in (("нм", 1e-9), ("пм", 1e-12)):
        if abs(x) >= scale:
            return unit, scale
    return "фм", 1e-15


def length(x):
    if x is None:
        return "—"
    unit, scale = pick_unit(x)
    return f"{num(x / scale)} {unit}"


def div(a, b):
    return None if a is None or b is None or b == 0 else a / b


def with_unit(value, unit):
    return "—" if value is None else f"{num(value)} {unit}".strip()


def rel_error(got, expect):
    if got is None or expect is None or expect == 0:
        return None
    return abs(got - expect) / abs(expect)


def ticks(lo, hi, count=6):
    raw = (hi - lo) / count
    if not raw > 0:
        return [lo], 1.0
    mag = 10 ** math.floor(math.log10(raw))
    step = min((k * mag for k in (1, 2, 5, 10)), key=lambda s: abs(math.log(s / raw)))
    first = math.ceil(lo / step - 1e-9) * step
    total = int(math.floor((hi - first) / step + 1e-9)) + 1
    return [first + i * step for i in range(total)], step


def tick_text(value, step):
    digits = max(0, -math.floor(math.log10(step) + 1e-9))
    text = f"{value:.{digits}f}"
    if float(text) == 0:
        text = text.lstrip("-")
    return text.replace(".", ",").replace("-", "−")
