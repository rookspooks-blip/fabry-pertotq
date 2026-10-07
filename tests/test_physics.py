import math

import numpy as np
import pytest

from fabry_perot import physics as ph

LAM, D, N, F_LENS = 632.8e-9, 5e-3, 1.0, 0.2


def test_airy_matches_sum_of_beams():
    R, A = 0.9, 0.01
    delta = np.linspace(0, 4 * np.pi, 2001)
    t = 1 - R - A
    field = t * np.sum([(R * np.exp(1j * delta)) ** k for k in range(800)], axis=0)
    direct = np.abs(field) ** 2
    formula = ph.airy(delta, ph.coefficient_f(R), ph.peak_transmission(R, A))
    assert np.allclose(direct, formula, rtol=1e-9, atol=1e-12)


@pytest.mark.parametrize("R", [0.3, 0.7, 0.9, 0.98])
def test_measured_curve_matches_theory(R):
    th = ph.theory(LAM, D, N, R, F_LENS)
    lo, hi = -1.5 * th["fsr"], 1.5 * th["fsr"]
    x = LAM + np.linspace(lo, hi, int(min(max(30 * (hi - lo) / (th["width"] or th["fsr"]), 20000), 2e6)))
    T = ph.airy(ph.phase(x, D, N), th["F"])
    meas = ph.measure_curve(x, T, LAM)
    assert meas["fsr"] == pytest.approx(th["fsr"], rel=2e-3)
    assert meas["width"] == pytest.approx(th["width"], rel=5e-3)
    assert meas["contrast"] == pytest.approx(th["contrast"], rel=1e-2)


def test_no_light_when_mirrors_absorb_everything():
    th = ph.theory(LAM, D, N, 0.9, F_LENS, A=0.1)
    assert th["tmax"] == 0
    x = LAM + np.linspace(-th["fsr"], th["fsr"], 5000)
    meas = ph.measure_curve(x, ph.airy(ph.phase(x, D, N), th["F"], th["tmax"]), LAM)
    assert meas["fsr"] is None and meas["width"] is None


def test_losses_lower_peaks():
    assert ph.peak_transmission(0.95, 0.02) == pytest.approx((0.03 / 0.05) ** 2)
    assert ph.peak_transmission(0.9) == 1.0


def test_ring_radii_are_bright():
    radii = ph.ring_radii(LAM, D, N, F_LENS, 0.01)
    assert len(radii) == 19
    for r in radii:
        m = ph.order_at(r, LAM, D, N, F_LENS)
        assert m == pytest.approx(round(m), abs=1e-6)
    th = ph.theory(LAM, D, N, 0.9, F_LENS)
    assert radii[1] ** 2 - radii[0] ** 2 == pytest.approx(th["dr2"], rel=1e-3)


def test_seamless_shift_is_multiple_of_half_wave():
    shift = ph.seamless_shift(LAM, 1.5, 1000e-9)
    step = LAM / 3
    assert shift <= 1000e-9 and math.isclose(shift / step, round(shift / step))


def test_airy_mean_matches_dense_average():
    F = ph.coefficient_f(0.95)
    for a, b in [(1e5 + 0.1, 1e5 + 7.3), (2e6, 2e6 - 5.5), (3.0, 3.0 + 1e-3), (10.0, 10.0 + 1e-12)]:
        x = np.linspace(a, b, 1_000_001)
        dense = ph.airy(x, F).mean()
        exact = ph.airy_mean(np.array([a]), np.array([b]), F)[0]
        assert exact == pytest.approx(dense, rel=1e-4)


def test_airy_range_contains_every_sample():
    F = ph.coefficient_f(0.99)
    edges = np.linspace(1e5, 1e5 + 40, 201)
    lo, hi = ph.airy_range(edges, F)
    x = np.linspace(edges[0], edges[-1], 400_001)
    col = np.minimum(((x - edges[0]) / (edges[1] - edges[0])).astype(int), 199)
    T = ph.airy(x, F)
    assert np.all(T >= lo[col] - 1e-12) and np.all(T <= hi[col] + 1e-12)
    assert hi.max() == 1.0


def test_measured_rings_match_formula():
    F = ph.coefficient_f(0.9)
    measured, near = ph.measure_rings(LAM, D, N, F_LENS, 0.01, F, 1.0)
    predicted = ph.ring_radii(LAM, D, N, F_LENS, 0.01)
    predicted = predicted[predicted > near]
    assert len(measured) == len(predicted) == 19
    assert np.allclose(measured, predicted, rtol=1e-5)


def test_many_thin_rings_are_all_found():
    lam, d, n, f, half = 380e-9, 0.02, 2.0, 0.05, 0.1
    measured, near = ph.measure_rings(lam, d, n, f, half, ph.coefficient_f(0.99), 1.0)
    predicted = ph.ring_radii(lam, d, n, f, half, limit=10 ** 6)
    predicted = predicted[predicted > near]
    assert abs(len(measured) - len(predicted)) <= 1
    assert np.allclose(measured[:50], predicted[:50], rtol=1e-4)
