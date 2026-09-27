"""Проверки режима лабораторной работы: варианты, МНК, обработка серий."""

import math

import numpy as np
import pytest

from fabry_perot import lab
from fabry_perot import physics as ph


def test_variants_are_stable_and_different():
    a, b = lab.Variant(7), lab.Variant(7)
    assert (a.lam, a.dlam, a.A, a.d_rings, a.f_rings) == (b.lam, b.dlam, b.A, b.d_rings, b.f_rings)
    lams = {lab.Variant(c).lam for c in lab.CODES}
    assert len(lams) == len(lab.CODES)                 # у всех вариантов разные длины волн
    for c in lab.CODES:
        v = lab.Variant(c)
        assert 450 <= v.lam <= 690 and 300 <= v.dlam <= 900 and 0 < v.A <= 0.01


def test_fit_line_exact_and_errors():
    xs = [1, 2, 3, 4, 5]
    fit = lab.fit_line(xs, [2 + 3 * x for x in xs])
    assert fit["a"] == pytest.approx(2) and fit["b"] == pytest.approx(3) and fit["sb"] == pytest.approx(0)
    rng = np.random.default_rng(1)
    ys = [2 + 3 * x + e for x, e in zip(xs, rng.normal(0, 0.1, 5))]
    fit = lab.fit_line(xs, ys)
    slope, icpt = np.polyfit(xs, ys, 1)
    assert fit["b"] == pytest.approx(slope) and fit["a"] == pytest.approx(icpt)
    assert fit["db"] == pytest.approx(3.18 * fit["sb"])
    origin = lab.fit_line([1, 2, 4], [3, 6, 12], through_origin=True)
    assert origin["b"] == pytest.approx(3) and origin["a"] == 0


def test_wavelength_from_ideal_series():
    """По идеальным «измерениям» обработка возвращает ту же длину волны."""
    v = lab.Variant(3)
    lam, n = v.lam * 1e-9, 1.0
    params = {"n": n, "d": v.d_rings, "f": v.f_rings}
    r = ph.ring_radii(lam, v.d_rings * 1e-3, n, v.f_rings * 1e-3, 0.01)[:6] * 1e3
    fit = lab.fit_line(list(range(1, 7)), list(r ** 2))
    name, value, err, unit = lab.derived("rings", fit, params, None)
    assert value == pytest.approx(v.lam, rel=2e-3)
    ds = [1.0, 2.0, 3.0, 5.0, 8.0]
    fsr = [(lam ** 2 / (2 * n * d * 1e-3)) * 1e12 for d in ds]
    fit = lab.fit_line([1 / d for d in ds], fsr, through_origin=True)
    assert lab.derived("fsr", fit, params, None)[1] == pytest.approx(v.lam, rel=1e-6)
    fit = lab.fit_line([1, 2, 3], [40 + k * v.lam / 2 for k in (1, 2, 3)])
    assert lab.derived("shift", fit, params, None)[1] == pytest.approx(v.lam)


def test_realism_keeps_peak_positions():
    """Размытие опускает и уширяет пики, но не сдвигает их — длина волны определяется верно."""
    F = ph.coefficient_f(0.9)
    blur = ph.blur_halfwidth(600e-9, 5e-3, 1.0, 600e-9 / 60, 0.05e-12)
    x = np.linspace(-np.pi, np.pi, 20001)
    T = ph.airy_blurred(x, F, 1.0, blur)
    assert abs(x[np.argmax(T)]) < 1e-3
    assert T.max() < 1.0
    lo, hi = ph.blurred_range(np.linspace(-3, 3, 61), F, 1.0, blur)
    xs = np.linspace(-3, 3, 60001)
    col = np.minimum(((xs + 3) / 0.1).astype(int), 59)
    Ts = ph.airy_blurred(xs, F, 1.0, blur)
    assert np.all(Ts <= hi[col] + 1e-9) and np.all(Ts >= lo[col] - 1e-9)


def test_rayleigh_limit_close_to_width():
    for R in (0.8, 0.9, 0.95):
        th = ph.theory(589e-9, 1e-3, 1.0, R, 0.2)
        limit = ph.rayleigh_limit(th["fsr"], th["F"])
        assert limit == pytest.approx(th["width"], rel=0.06)
        assert ph.dip_ratio(limit, th["fsr"], th["F"]) == pytest.approx(ph.RAYLEIGH, abs=1e-6)


def test_mean_with_error():
    m, e = lab.mean_with_error([1.0, 1.2, 0.8, 1.1, 0.9])
    assert m == pytest.approx(1.0)
    assert e == pytest.approx(2.78 * math.sqrt(0.025 / 5))
