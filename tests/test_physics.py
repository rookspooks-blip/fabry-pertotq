"""Проверки физики: формулы против прямого сложения лучей и измерений по графикам."""

import math

import numpy as np
import pytest

from fabry_perot import physics as ph

LAM, D, N, F_LENS = 632.8e-9, 5e-3, 1.0, 0.2


def test_airy_matches_sum_of_beams():
    """Функция Эйри совпадает с прямым сложением многократно отражённых лучей."""
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
    """На радиусах колец по формуле пропускание максимально (порядок — целое число)."""
    radii = ph.ring_radii(LAM, D, N, F_LENS, 0.01)
    assert len(radii) == 19
    for r in radii:
        m = ph.order_at(r, LAM, D, N, F_LENS)
        assert m == pytest.approx(round(m), abs=1e-6)
    # r₂² − r₁² ≈ f²nλ/d при малых углах
    th = ph.theory(LAM, D, N, 0.9, F_LENS)
    assert radii[1] ** 2 - radii[0] ** 2 == pytest.approx(th["dr2"], rel=1e-3)


def test_seamless_shift_is_multiple_of_half_wave():
    shift = ph.seamless_shift(LAM, 1.5, 1000e-9)
    step = LAM / 3
    assert shift <= 1000e-9 and math.isclose(shift / step, round(shift / step))
