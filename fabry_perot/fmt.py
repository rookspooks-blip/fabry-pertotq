"""Запись чисел по-русски (запятая вместо точки) и деления осей графиков."""

import math

import numpy as np

SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")   # цифры для степеней 10ⁿ


def num(x, digits=4):
    """Число с четырьмя значащими цифрами: 40,04 · 0,05320 · 4,708·10⁶."""
    if x is None:
        return "—"
    if isinstance(x, (int, np.integer)):          # целые (например, число колец)
        return f"{x:,}".replace(",", " ")
    if not math.isfinite(x):
        return "—"
    if x == 0:
        return "0"
    power = math.floor(math.log10(abs(x)))
    if -3 <= power < 6:
        # обычная запись; тысячи отделяем неразрывным пробелом: 15 803
        text = f"{x:,.{max(digits - 1 - power, 0)}f}".replace(",", " ")
    else:
        # очень большие и очень маленькие числа — через степень десяти
        text = f"{x / 10 ** power:.{digits - 1}f}·10" + str(power).translate(SUP)
    return text.replace(".", ",").replace("-", "−")


def short(x):
    """Короткая запись без лишних нулей: 380, 0,01, 2000."""
    return f"{x:g}".replace(".", ",")


def plain(x):
    """Число для файла CSV: 6 значащих цифр и запятая (так его понимает русский Excel)."""
    return "" if x is None else f"{x:.6g}".replace(".", ",")


def pick_unit(x):
    """Удобная единица для малой длины x (в метрах): нм, пм или фм."""
    for unit, scale in (("нм", 1e-9), ("пм", 1e-12)):
        if abs(x) >= scale:
            return unit, scale
    return "фм", 1e-15


def length(x):
    """Длина в удобных единицах, например «40,04 пм»."""
    if x is None:
        return "—"
    unit, scale = pick_unit(x)
    return f"{num(x / scale)} {unit}"


def div(a, b):
    """a / b, если оба числа известны; иначе None (в таблице будет прочерк)."""
    return None if a is None or b is None or b == 0 else a / b


def with_unit(value, unit):
    """Число с единицей для таблицы: «40,04 пм»; нет значения — «—»."""
    return "—" if value is None else f"{num(value)} {unit}".strip()


def rel_error(got, expect):
    """Относительное расхождение измерения и формулы (None — сравнивать нечего)."""
    if got is None or expect is None or expect == 0:
        return None
    return abs(got - expect) / abs(expect)


def ticks(lo, hi, count=6):
    """Деления оси с «круглым» шагом 1, 2 или 5·10ⁿ. Возвращает (значения, шаг)."""
    raw = (hi - lo) / count
    if not raw > 0:
        return [lo], 1.0
    mag = 10 ** math.floor(math.log10(raw))
    # из «круглых» шагов берём ближайший к нужному
    step = min((k * mag for k in (1, 2, 5, 10)), key=lambda s: abs(math.log(s / raw)))
    first = math.ceil(lo / step - 1e-9) * step
    total = int(math.floor((hi - first) / step + 1e-9)) + 1
    return [first + i * step for i in range(total)], step


def tick_text(value, step):
    """Подпись деления: столько знаков после запятой, сколько требует шаг."""
    digits = max(0, -math.floor(math.log10(step) + 1e-9))
    text = f"{value:.{digits}f}"
    if float(text) == 0:
        text = text.lstrip("-")                   # без «−0»
    return text.replace(".", ",").replace("-", "−")
