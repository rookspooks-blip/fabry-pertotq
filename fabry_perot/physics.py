import math

import numpy as np

C = 299792458.0


def coefficient_f(R):
    return 4.0 * R / (1.0 - R) ** 2


def peak_transmission(R, A=0.0):
    return (max(1.0 - R - A, 0.0) / (1.0 - R)) ** 2


def phase(lam, d, n, sin_out=0.0):
    return 4.0 * np.pi * d * np.sqrt(n * n - sin_out * sin_out) / lam


def airy(delta, F, tmax=1.0):
    return tmax / (1.0 + F * np.sin(delta / 2.0) ** 2)


def airy_mean(d1, d2, F, tmax=1.0):
    q = np.sqrt(1.0 + F)
    k1 = np.floor(d1 / (2 * np.pi) + 0.5)
    k2 = np.floor(d2 / (2 * np.pi) + 0.5)
    a1 = np.arctan(q * np.tan((d1 - 2 * np.pi * k1) / 2))
    a2 = np.arctan(q * np.tan((d2 - 2 * np.pi * k2) / 2))
    width = d2 - d1
    tiny = np.abs(width) < 1e-9
    mean = (2 / q) * (np.pi * (k2 - k1) + (a2 - a1)) / np.where(tiny, 1.0, width)
    return tmax * np.where(tiny, airy((d1 + d2) / 2, F), mean)


def airy_range(edges, F, tmax=1.0):
    a, b = np.minimum(edges[:-1], edges[1:]), np.maximum(edges[:-1], edges[1:])
    ta, tb = airy(a, F, tmax), airy(b, F, tmax)
    period = 2 * np.pi
    has_peak = np.floor(b / period) * period >= a
    has_dip = np.floor((b - np.pi) / period) * period + np.pi >= a
    hi = np.where(has_peak, tmax, np.maximum(ta, tb))
    lo = np.where(has_dip, tmax / (1 + F), np.minimum(ta, tb))
    return lo, hi


APERTURE = 0.010


def defocus_radius(L, f, aperture=APERTURE):
    return aperture / 2 * abs(L - f) / f


def screen_mean(r1, r2, lam, d, n, L, F, tmax=1.0):
    s1, s2 = r1 / np.hypot(r1, L), r2 / np.hypot(r2, L)
    return airy_mean(phase(lam, d, n, s1), phase(lam, d, n, s2), F, tmax)


def dip_ratio(dlam, fsr, F):
    shift = 2 * np.pi * dlam / fsr
    x = np.linspace(-shift, 2 * shift, 6001)
    total = airy(x, F) + airy(x - shift, F)
    middle = float(airy(shift / 2, F) * 2)
    return middle / float(total.max())


RAYLEIGH = 0.81


def rayleigh_limit(fsr, F):
    lo, hi = 1e-6 * fsr, 0.5 * fsr
    if dip_ratio(hi, fsr, F) > RAYLEIGH:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2
        if dip_ratio(mid, fsr, F) > RAYLEIGH:
            lo = mid
        else:
            hi = mid
    return hi


def order_at(r, lam, d, n, f):
    s = r / math.hypot(r, f)
    return 2 * d * math.sqrt(n * n - s * s) / lam


def theory(lam, d, n, R, f, A=0.0):
    F = coefficient_f(R)
    tmax = peak_transmission(R, A)
    fsr = lam ** 2 / (2 * n * d)
    res = {
        "F": F,
        "tmax": tmax,
        "m0": 2 * n * d / lam,
        "T": float(airy(phase(lam, d, n), F, tmax)),
        "fsr": fsr,
        "fsr_nu": C / (2 * n * d),
        "finesse_approx": math.pi * math.sqrt(R) / (1 - R),
        "contrast": 1 + F,
        "dr2": f * f * n * lam / d,
        "width": None, "finesse": None, "resolving": None,
    }
    if F > 1:
        half = 4 * math.asin(1 / math.sqrt(F))
        res["finesse"] = 2 * math.pi / half
        res["width"] = fsr / res["finesse"]
        res["resolving"] = lam / res["width"]
    return res


def ring_radii(lam, d, n, f, r_max, limit=500):
    m0 = 2 * n * d / lam
    a = lam / (2 * d)
    first = math.ceil(m0) - 1
    m = np.arange(first, max(first - limit, 0), -1, dtype=float)
    s2 = a * (m0 - m) * (n + m * a)
    s2 = s2[(s2 > 0) & (s2 < 1)]
    r = f * np.sqrt(s2 / (1 - s2))
    return r[r <= r_max]


def find_peaks(x, y):
    i = np.flatnonzero((y[1:-1] > y[:-2]) & (y[1:-1] >= y[2:])) + 1
    left, mid, right = y[i - 1], y[i], y[i + 1]
    bend = left - 2 * mid + right
    shift = np.divide(0.5 * (left - right), bend, out=np.zeros(len(i)), where=bend != 0)
    return i, x[i] + shift * (x[1] - x[0]), mid - 0.25 * (left - right) * shift


def measure_curve(x, T, x_line):
    res = {"fsr": None, "width": None, "contrast": None, "peaks": None, "half": None}
    if T.size < 3 or T.max() <= 0:
        return res
    idx, pos, height = find_peaks(x, T)
    if len(pos) < 2:
        return res
    k = int(np.clip(np.searchsorted(pos, x_line), 1, len(pos) - 1))
    res["fsr"] = pos[k] - pos[k - 1]
    res["peaks"] = (pos[k - 1], pos[k])
    j = k if abs(pos[k] - x_line) < abs(pos[k - 1] - x_line) else k - 1
    top, i = height[j], idx[j]
    res["contrast"] = top / T.min()
    half = top / 2
    left = np.flatnonzero(T[:i] < half)
    right = np.flatnonzero(T[i:] < half)
    if left.size and right.size:
        a, b = left[-1], i + right[0]
        x_left = np.interp(half, [T[a], T[a + 1]], [x[a], x[a + 1]])
        x_right = np.interp(half, [T[b], T[b - 1]], [x[b], x[b - 1]])
        res["width"] = x_right - x_left
        res["half"] = (x_left, x_right, half)
    return res


def curve_samples(span, width, fsr):
    return int(min(max(30 * span / (width or fsr), 20000), 2e6))


def measure_rings(lam, d, n, f, r_max, F, tmax, per_period=6, cap=150000, refine=300):
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
    step = lam / (2 * n)
    return max(step, math.floor(limit / step) * step)
