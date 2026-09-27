"""Физика интерферометра Фабри — Перо. Внутри расчёта все величины в СИ: метры и радианы.

Модель: зеркала одинаковые, плоские и строго параллельные, свет каждой
спектральной линии строго одного цвета. Зеркала могут поглощать долю света A
(по умолчанию A = 0 — зеркала без потерь).
"""

import math

import numpy as np

C = 299792458.0        # скорость света в вакууме, м/с


def coefficient_f(R):
    """Коэффициент F = 4R / (1 − R)². Чем ближе R к 1, тем он больше и тем уже пики."""
    return 4.0 * R / (1.0 - R) ** 2


def peak_transmission(R, A=0.0):
    """Высота пиков Tmax = (1 − R − A)² / (1 − R)².

    Без поглощения (A = 0) пики доходят до 1. Каждое зеркало пропускает долю
    1 − R − A; при R, близком к 1, свет много раз ходит между зеркалами и
    каждый раз теряет A, поэтому даже малое поглощение сильно «съедает» пики.
    """
    return (max(1.0 - R - A, 0.0) / (1.0 - R)) ** 2


def phase(lam, d, n, sin_out=0.0):
    """Разность фаз соседних лучей: δ = 4π·d·√(n² − sin²θ) / λ.

    θ — угол луча после интерферометра (в воздухе). Внутри зазора луч
    преломляется по закону Снеллиуса sin θ = n·sin θ', поэтому
    n·cos θ' = √(n² − sin²θ). При n = 1 получается привычное 4π·d·cos θ / λ,
    а при θ = 0 (свет падает перпендикулярно) — 4π·n·d / λ.
    Работает и с числами, и с массивами numpy.
    """
    return 4.0 * np.pi * d * np.sqrt(n * n - sin_out * sin_out) / lam


def airy(delta, F, tmax=1.0):
    """Функция Эйри — доля прошедшего света: T = Tmax / (1 + F·sin²(δ/2)).

    T = Tmax, когда δ = 2πm (все лучи приходят в фазе — максимум),
    и T = Tmax / (1 + F) посередине между максимумами.
    """
    return tmax / (1.0 + F * np.sin(delta / 2.0) ** 2)


def order_at(r, lam, d, n, f):
    """Порядок интерференции в точке экрана на расстоянии r от центра: 2d·√(n² − sin²θ) / λ."""
    s = r / math.hypot(r, f)
    return 2 * d * math.sqrt(n * n - s * s) / lam


def theory(lam, d, n, R, f, A=0.0):
    """Характеристики прибора по формулам — с ними сравниваются измерения."""
    F = coefficient_f(R)
    tmax = peak_transmission(R, A)
    fsr = lam ** 2 / (2 * n * d)                  # расстояние между максимумами Δλ
    res = {
        "F": F,
        "tmax": tmax,                              # высота пиков
        "m0": 2 * n * d / lam,                     # порядок интерференции в центре
        "T": float(airy(phase(lam, d, n), F, tmax)),   # пропускание на самой λ₁
        "fsr": fsr,
        "fsr_nu": C / (2 * n * d),                 # то же расстояние по частоте, Гц
        "finesse_approx": math.pi * math.sqrt(R) / (1 - R),
        "contrast": 1 + F,                         # Tmax / Tmin
        "dr2": f * f * n * lam / d,                # r²(k+1) − r²(k) при малых углах
        "width": None, "finesse": None, "resolving": None,
    }
    # Ширина на половине высоты существует, только если провалы опускаются
    # ниже половины пика, то есть 1/(1 + F) < 0,5, F > 1 (это R > 0,172)
    if F > 1:
        half = 4 * math.asin(1 / math.sqrt(F))     # точная ширина пика по фазе
        res["finesse"] = 2 * math.pi / half        # резкость = Δλ / w
        res["width"] = fsr / res["finesse"]        # ширина пика w
        res["resolving"] = lam / res["width"]      # разрешающая способность = m₀ · резкость
    return res


def ring_radii(lam, d, n, f, r_max, limit=500):
    """Радиусы светлых колец по точной формуле 2d·√(n² − sin²θ) = m·λ.

    Порядок m уменьшается от центра к краю: первое кольцо — наибольшее целое m,
    меньшее m₀ = 2nd/λ. На экране в фокусе линзы радиус r = f·tg θ.
    """
    m0 = 2 * n * d / lam
    a = lam / (2 * d)
    first = math.ceil(m0) - 1
    m = np.arange(first, max(first - limit, 0), -1, dtype=float)
    # sin²θ = n² − (m·a)², записано как a·(m₀ − m)·(n + m·a): так нет потери точности
    s2 = a * (m0 - m) * (n + m * a)
    s2 = s2[(s2 > 0) & (s2 < 1)]
    r = f * np.sqrt(s2 / (1 - s2))                 # tg θ = sin θ / cos θ
    return r[r <= r_max]


def ring_samples(lam, d, n, F, f, r_max):
    """Сколько точек брать по радиусу, чтобы не «проскочить» тонкое кольцо."""
    edge = r_max / math.hypot(r_max, f)                    # sin θ на краю
    change = phase(lam, d, n) - phase(lam, d, n, edge)     # изменение фазы от центра до края
    width = 4 * math.asin(1 / math.sqrt(F)) if F > 1 else 2 * math.pi
    # у края кольца теснее всего: 24 точки на ширину кольца в среднем ≈ 12 у края
    return int(min(max(24 * change / width, 4000), 2e6))


def find_peaks(x, y):
    """Максимумы кривой: номера точек, уточнённые положения и высоты.

    Максимум — точка выше обеих соседних. Точное положение между точками
    находим, проведя параболу через три точки вокруг максимума.
    """
    i = np.flatnonzero((y[1:-1] > y[:-2]) & (y[1:-1] >= y[2:])) + 1
    left, mid, right = y[i - 1], y[i], y[i + 1]
    bend = left - 2 * mid + right
    shift = np.divide(0.5 * (left - right), bend, out=np.zeros(len(i)), where=bend != 0)
    return i, x[i] + shift * (x[1] - x[0]), mid - 0.25 * (left - right) * shift


def measure_curve(x, T, x_line):
    """Измерения «по графику»: Δλ между соседними пиками, ширина пика w и контраст."""
    res = {"fsr": None, "width": None, "contrast": None, "peaks": None, "half": None}
    if T.size < 3 or T.max() <= 0:                 # свет совсем не проходит (R + A = 1)
        return res
    idx, pos, height = find_peaks(x, T)
    if len(pos) < 2:
        return res
    # два соседних пика — слева и справа от линии λ₁
    k = int(np.clip(np.searchsorted(pos, x_line), 1, len(pos) - 1))
    res["fsr"] = pos[k] - pos[k - 1]
    res["peaks"] = (pos[k - 1], pos[k])
    # ширину меряем у пика, ближайшего к λ₁
    j = k if abs(pos[k] - x_line) < abs(pos[k - 1] - x_line) else k - 1
    top, i = height[j], idx[j]
    res["contrast"] = top / T.min()
    half = top / 2
    left = np.flatnonzero(T[:i] < half)            # точки ниже половины слева от пика
    right = np.flatnonzero(T[i:] < half)           # и справа от него
    if left.size and right.size:
        a, b = left[-1], i + right[0]
        # точное место пересечения уровня половины — линейная интерполяция
        x_left = np.interp(half, [T[a], T[a + 1]], [x[a], x[a + 1]])
        x_right = np.interp(half, [T[b], T[b - 1]], [x[b], x[b - 1]])
        res["width"] = x_right - x_left
        res["half"] = (x_left, x_right, half)
    return res


def seamless_shift(lam, n, limit):
    """Наибольший сдвиг зеркала ≤ limit, кратный λ/(2n): после него картина колец повторяется.

    Нужен для анимации микросдвига: сдвиг идёт по кругу 0 → конец → 0 без скачка картинки.
    """
    step = lam / (2 * n)
    return max(step, math.floor(limit / step) * step)
