"""Режим лабораторной работы: варианты со скрытыми параметрами, серии измерений, метод наименьших квадратов.

Модуль без Qt — только расчёты, поэтому его легко проверить тестами и использовать
при сборке ответов для преподавателя (tools/docs_tables.py).
"""

import math
import random

from .physics import ring_radii

CODES = range(1, 31)                               # коды вариантов, которые выдаёт преподаватель

# Коэффициенты Стьюдента для доверительной вероятности 0,95 (число степеней свободы 1…30)
STUDENT_95 = [12.71, 4.30, 3.18, 2.78, 2.57, 2.45, 2.36, 2.31, 2.26, 2.23, 2.20, 2.18, 2.16, 2.14, 2.13,
              2.12, 2.11, 2.10, 2.09, 2.09, 2.08, 2.07, 2.07, 2.06, 2.06, 2.06, 2.05, 2.05, 2.05, 2.04]


def student(dof):
    """Коэффициент Стьюдента t(0,95; dof); для больших dof — 1,96."""
    if dof < 1:
        return float("nan")
    return STUDENT_95[dof - 1] if dof <= len(STUDENT_95) else 1.96


class Variant:
    """Вариант лабораторной работы по коду 1…30.

    Скрытые величины (их определяет студент): длина волны «неизвестного источника»
    λx, разность длин волн «неизвестного дублета» δλx, поглощение зеркал Ax.
    Открытые: d и линза f (из набора) для задания с кольцами.
    Всё получается из кода одинаково на любом компьютере (random.Random со строкой).
    """

    def __init__(self, code):
        self.code = int(code)
        rng = random.Random(f"fabry-perot-variant-{self.code}")
        self.lam = round(rng.uniform(450.0, 690.0), 1)                 # нм
        self.dlam = float(round(rng.uniform(300.0, 900.0)))             # пм
        self.A = rng.choice([0.002, 0.003, 0.004, 0.005, 0.006, 0.008, 0.010])
        # два значения больше не используются, но берутся из генератора по-прежнему,
        # чтобы d и f задания 4 (и ответы преподавателю) у всех вариантов остались прежними
        rng.choice([100, 120, 150, 180, 200])
        rng.choice([0.02, 0.03, 0.05, 0.08])
        # d и f для колец: не меньше шести колец на экране радиусом 10 мм
        options = [(d, f) for d in (2.0, 3.0, 4.0, 5.0, 6.0) for f in (150.0, 200.0, 250.0, 300.0)]
        rng.shuffle(options)
        for d, f in options:
            if len(ring_radii(self.lam * 1e-9, d * 1e-3, 1.0, f * 1e-3, 0.010)) >= 7:
                break
        self.d_rings, self.f_rings = d, f


def fit_line(xs, ys, through_origin=False):
    """Прямая y = a + b·x методом наименьших квадратов (МНК) с погрешностями.

    Возвращает словарь: a, b, σa, σb (стандартные отклонения), n, t (Стьюдент, 0,95),
    Δa, Δb (доверительные границы = t·σ). Через начало координат — y = b·x.
    Формулы:
        b = Σ(x − x̄)(y − ȳ) / Σ(x − x̄)²,  a = ȳ − b·x̄,
        s² = Σ(y − a − b·x)² / (n − 2),     σb = s / √Σ(x − x̄)²,  σa = s·√(1/n + x̄²/Σ(x − x̄)²).
    """
    n = len(xs)
    if n < (1 if through_origin else 2):
        return None
    if through_origin:
        sxx = sum(x * x for x in xs)
        if sxx == 0:
            return None
        b = sum(x * y for x, y in zip(xs, ys)) / sxx
        a = 0.0
        dof = n - 1
        s2 = sum((y - b * x) ** 2 for x, y in zip(xs, ys)) / dof if dof > 0 else float("nan")
        sb, sa = math.sqrt(s2 / sxx) if dof > 0 else float("nan"), 0.0
    else:
        mx, my = sum(xs) / n, sum(ys) / n
        sxx = sum((x - mx) ** 2 for x in xs)
        if sxx == 0:
            return None
        b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
        a = my - b * mx
        dof = n - 2
        s2 = sum((y - a - b * x) ** 2 for x, y in zip(xs, ys)) / dof if dof > 0 else float("nan")
        sb = math.sqrt(s2 / sxx) if dof > 0 else float("nan")
        sa = math.sqrt(s2 * (1 / n + mx * mx / sxx)) if dof > 0 else float("nan")
    t = student(dof)
    return {"a": a, "b": b, "sa": sa, "sb": sb, "n": n, "dof": dof, "t": t, "da": t * sa, "db": t * sb}


class Series:
    """Серия измерений одного задания.

    kind — как записывается точка:
      "pair"  — два щелчка по графику T(λ): y = |x₂ − x₁| (пм);
      "ring"  — щелчок по кольцу или разрезу: y = r² (мм²), x — номер кольца по порядку;
      "param" — запоминается значение параметра (ключ source), x — номер по порядку или параметр xkey;
      "point" — просто показание курсора (x, y).
    """

    def __init__(self, key, title, kind, xlabel, ylabel, hint, xkey=None, xfunc=None, source=None,
                 through_origin=False, fit=True):
        self.key, self.title, self.kind = key, title, kind
        self.xlabel, self.ylabel, self.hint = xlabel, ylabel, hint
        self.xkey, self.xfunc, self.source = xkey, xfunc, source
        self.through_origin, self.fit = through_origin, fit


SERIES = [
    Series("fsr", "Задание 2. Область свободной дисперсии", "pair", "1/d, мм⁻¹", "Δλ, пм",
           "Для каждого d: правый щелчок по одному максимуму графика T(λ), затем по соседнему.",
           xkey="d", xfunc=lambda d: 1.0 / d, through_origin=True),
    Series("width", "Задание 3. Ширина полосы пропускания", "pair", "(1 − R)/√R", "w, пм",
           "Для каждого R: правый щелчок в точке T = Tmax/2 слева от максимума, затем справа.",
           xkey="R", xfunc=lambda R: (1 - R) / math.sqrt(R)),
    Series("rings", "Задание 4. Радиусы колец", "ring", "номер кольца k", "r², мм²",
           "Правый щелчок по светлым кольцам от центра к краю (на картине или на разрезе)."),
    Series("shift", "Задание 5. Сдвиг зеркала", "param", "число новых колец N", "Δd, нм",
           "Когда центр картины максимально ярок, нажмите «Записать»: запомнится текущий Δd.",
           source="dd"),
    Series("doublet", "Задание 6.1. Совпадение колец дублета", "param", "№ измерения", "d*, мм",
           "Когда кольца двух линий совпали, нажмите «Записать»: запомнится текущий d.",
           source="d", fit=False),
    Series("resolve", "Задание 6.2. Предел разрешения", "param", "R", "δλmin, пм",
           "Когда провал между линиями стал 0,81 от максимума, нажмите «Записать».",
           xkey="R", source="dlam", fit=False),
    Series("tmax", "Задание 7. Поглощение: высота максимумов", "point", "R", "Tmax",
           "Правый щелчок по вершине максимума графика T(λ).", xkey="R", fit=False),
    Series("free", "Произвольные измерения", "point", "x", "y",
           "Правый щелчок по графику или кольцам записывает показание курсора.", fit=False),
]
BY_KEY = {s.key: s for s in SERIES}


def derived(key, fit, params, known):
    """Искомая величина по наклону прямой: (название, значение, погрешность, единица) или None.

    params — текущие параметры окна (n, d, f в мм), known — уже найденная длина волны, нм.
    """
    if fit is None or not fit["b"] or not math.isfinite(fit["b"]):
        return None
    b, db = fit["b"], fit["db"]
    n = params["n"]
    if key == "fsr":           # Δλ = λ²/(2nd): b [пм·мм] = λ²/(2n) → λ = √(2n·b·10⁻¹⁵) м
        lam = math.sqrt(2 * n * b * 1e-15) * 1e9
        return ("λ", lam, lam * db / (2 * b), "нм")
    if key == "width":         # w ≈ Δλ·(1 − R)/(π√R) → Δλ = π·b
        return ("Δλ", math.pi * b, math.pi * db, "пм")
    if key == "rings":         # r² = f²nλ/d·(k − 1 + ε) → λ = b·d/(f²n)
        lam = b * params["d"] / (params["f"] ** 2 * n) * 1e6
        return ("λ", lam, lam * db / b, "нм")
    if key == "shift":         # Δd_N = Δd₀ + N·λ/(2n) → λ = 2n·b
        return ("λ", 2 * n * b, 2 * n * db, "нм")
    return None


def mean_with_error(values):
    """Среднее и доверительная граница (0,95) для ряда повторных измерений."""
    n = len(values)
    if n == 0:
        return None, None
    m = sum(values) / n
    if n == 1:
        return m, None
    s = math.sqrt(sum((v - m) ** 2 for v in values) / (n - 1))
    return m, student(n - 1) * s / math.sqrt(n)
