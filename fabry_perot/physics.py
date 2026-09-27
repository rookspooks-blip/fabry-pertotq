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


def airy_mean(d1, d2, F, tmax=1.0):
    """Среднее пропускание на отрезке фазы [δ₁, δ₂] — точно, без перебора точек.

    У функции Эйри есть первообразная: на каждом периоде
    ∫ dδ / (1 + F·sin²(δ/2)) = (2/√(1+F))·arctg(√(1+F)·tg(δ/2)),
    а за целый период набегает 2π/√(1+F). Так яркость пикселя экрана, внутри
    которого помещаются хоть тысячи тонких колец, считается одной формулой.
    """
    q = np.sqrt(1.0 + F)
    k1 = np.floor(d1 / (2 * np.pi) + 0.5)          # номер периода: δ = 2πk + φ, φ ∈ [−π, π)
    k2 = np.floor(d2 / (2 * np.pi) + 0.5)
    a1 = np.arctan(q * np.tan((d1 - 2 * np.pi * k1) / 2))
    a2 = np.arctan(q * np.tan((d2 - 2 * np.pi * k2) / 2))
    width = d2 - d1
    tiny = np.abs(width) < 1e-9                    # отрезок почти нулевой — берём значение в середине
    mean = (2 / q) * (np.pi * (k2 - k1) + (a2 - a1)) / np.where(tiny, 1.0, width)
    return tmax * np.where(tiny, airy((d1 + d2) / 2, F), mean)


def airy_range(edges, F, tmax=1.0):
    """Наименьшее и наибольшее пропускание на каждом отрезке между соседними фазами edges.

    Внутри отрезка функция Эйри достигает Tmax, если на нём есть δ = 2πm, и
    Tmax/(1 + F), если есть δ = π(2m + 1); иначе крайние значения — на концах.
    По этим парам график рисуется точно при любом масштабе: узкий пик не
    «проскочит» между точками, сколько бы пиков ни было.
    """
    a, b = np.minimum(edges[:-1], edges[1:]), np.maximum(edges[:-1], edges[1:])
    ta, tb = airy(a, F, tmax), airy(b, F, tmax)
    period = 2 * np.pi
    has_peak = np.floor(b / period) * period >= a
    has_dip = np.floor((b - np.pi) / period) * period + np.pi >= a
    hi = np.where(has_peak, tmax, np.maximum(ta, tb))
    lo = np.where(has_dip, tmax / (1 + F), np.minimum(ta, tb))
    return lo, hi


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


def curve_samples(span, width, fsr):
    """Сколько точек брать для измерений по графику T(λ): не меньше 30 на ширину пика."""
    return int(min(max(30 * span / (width or fsr), 20000), 2e6))


def measure_rings(lam, d, n, f, r_max, F, tmax, per_period=6, cap=150000, refine=300):
    """Светлые кольца «по картинке»: максимумы яркости от центра до края экрана.

    Яркость просматривается равномерно по u = sin²θ: фаза почти линейна по u,
    поэтому на каждое кольцо приходится одинаковое число точек (per_period),
    и ни одно кольцо не пропадает. Каждый найденный максимум (первые refine)
    уточняется трижды: вокруг него берутся всё более частые точки — как если
    бы мы увеличивали картинку в микроскоп. Возвращает (радиусы, м; «центр», м):
    кольца ближе «центра» не считаются, их не отличить от яркого пятна в центре.
    """
    s2_max = (r_max / math.hypot(r_max, f)) ** 2
    periods = (phase(lam, d, n) - phase(lam, d, n, math.sqrt(s2_max))) / (2 * np.pi)
    count = int(min(max(per_period * periods, 2000), cap))
    u = np.linspace(0.0, s2_max, count)
    du = u[1] - u[0]

    def bright(uu):
        return airy(4.0 * np.pi * d * np.sqrt(n * n - uu) / lam, F, tmax)

    T = bright(u)
    near_u = 2 * du
    near = f * math.sqrt(near_u / (1 - near_u))
    if tmax <= 0:
        return np.zeros(0), near
    idx = np.flatnonzero((T[1:-1] > T[:-2]) & (T[1:-1] >= T[2:])) + 1
    peaks = u[idx]
    if idx.size:
        # уточнение: три раза по 33 точки вокруг лучшей точки, шаг каждый раз в 16 раз мельче
        center, step = peaks[:refine].copy(), du
        offsets = np.linspace(-1.0, 1.0, 33)
        for _ in range(3):
            grid = np.clip(center[:, None] + step * offsets[None, :], 0.0, s2_max)
            values = bright(grid)
            best = np.argmax(values, axis=1)
            center = grid[np.arange(len(center)), best]
            step = step / 16
        peaks[:refine] = center
    peaks = peaks[(peaks > near_u)]
    return f * np.sqrt(peaks / (1 - peaks)), near


def seamless_shift(lam, n, limit):
    """Наибольший сдвиг зеркала ≤ limit, кратный λ/(2n): после него картина колец повторяется.

    Нужен для анимации микросдвига: сдвиг идёт по кругу 0 → конец → 0 без скачка картинки.
    """
    step = lam / (2 * n)
    return max(step, math.floor(limit / step) * step)
