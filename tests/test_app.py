import os

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("numpy")

from fabry_perot.qt import QtCore, QtWidgets


@pytest.fixture(scope="module")
def window(tmp_path_factory):
    home = tmp_path_factory.mktemp("settings")
    QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat, QtCore.QSettings.Scope.UserScope, str(home))
    from fabry_perot.app import create_app
    from fabry_perot.window import MainWindow
    app = QtWidgets.QApplication.instance() or create_app(["test"])
    win = MainWindow()
    win.resize(1400, 900)
    win.show()
    app.processEvents()
    yield win
    win.close()


def wait(ms):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def rows(win):
    return {name: (got, expect) for name, got, expect, _, _ in win.results}


def test_first_preset_measurements(window):
    got, expect = rows(window)["Колец на экране"]
    assert got == expect == 19
    got, expect = rows(window)["Расстояние между пиками Δλ"]
    assert got == pytest.approx(expect, rel=1e-3)


def test_typed_value_glides(window):
    row = window.params["d"]
    start = window.shown["d"]
    row.spin.setValue(10.0)
    assert window.shown["d"] == start
    wait(350)
    assert start < window.shown["d"] < 10.0
    wait(900)
    assert window.shown["d"] == 10.0


def test_slider_is_instant(window):
    row = window.params["R"]
    row.slider.setValue(row.to_slider(0.5))
    assert window.shown["R"] == pytest.approx(0.5, abs=1e-3)


def test_presets_and_theme(window):
    from fabry_perot.params import PRESETS
    for name, values, dlam in PRESETS:
        window.apply_preset(values, dlam)
        wait(1000)
        assert window.shown["lam"] == pytest.approx(values["lam"])
    window.toggle_theme()
    window.toggle_theme()


def test_scan_animation(window):
    window.toggle_scan()
    before = window.shown["dd"]
    wait(200)
    window.toggle_scan()
    assert window.shown["dd"] != before


def test_exports(window, tmp_path):
    window.write_csv(str(tmp_path / "t.csv"))
    window.write_png(str(tmp_path / "w.png"))
    window.write_rings(str(tmp_path / "r.png"), side=512)
    text = (tmp_path / "t.csv").read_text(encoding="utf-8-sig")
    assert "Ширина пика w" in text
    assert (tmp_path / "w.png").stat().st_size > 1000
    assert (tmp_path / "r.png").stat().st_size > 1000


def test_fast_step_is_short(window):
    row = window.params["dd"]
    before = window.shown["dd"]
    row.spin.stepBy(10)
    wait(300)
    assert row.value() > before
    assert window.shown["dd"] == pytest.approx(row.value())


def test_lab_mode_hides_and_records(window, tmp_path):
    from fabry_perot.lab import Variant
    window.journal.clear_all()
    window.set_lab(Variant(5))
    assert window.params["L"].label.isVisibleTo(window)
    assert window.params["f"].combo.isVisibleTo(window)
    assert window.params["lam"].hidden and window.params["A"].hidden
    assert window.pages.currentIndex() == 1
    assert window.context()["lam"] is None
    assert not window.ring_view.show_order
    window.journal.select("rings")
    for r in (1.0, 2.0, 3.0):
        window.ring_view.picked.emit(r, 0.5)
    rows = window.journal.data["rings"]
    assert [row["x"] for row in rows] == [1, 2, 3]
    assert rows[1]["y"] == pytest.approx(4.0)
    window.journal.select("fsr")
    window.plot_t.picked.emit(-10.0, 0.9)
    window.plot_t.picked.emit(30.0, 0.9)
    assert window.journal.data["fsr"][0]["y"] == pytest.approx(40.0)
    window.write_csv(str(tmp_path / "lab.csv"))
    text = (tmp_path / "lab.csv").read_text(encoding="utf-8-sig")
    assert "Вариант" in text and str(Variant(5).lam).replace(".", ",") not in text
    window.set_lab(None)
    assert not window.params["L"].label.isVisibleTo(window)
    assert not window.params["lam"].hidden and window.pages.currentIndex() == 0


def test_screen_out_of_focus_blurs_rings(window):
    from fabry_perot.lab import Variant
    window.set_lab(Variant(3))
    f = window.params["f"].value()
    window.params["L"].set(f)
    window.shown["L"] = f
    window.recalc()
    rv = window.ring_view
    rs = np.linspace(5e-3, 9e-3, 20000)
    sharp = np.array([rv.brightness(r) for r in rs])
    window.params["L"].set(f + 15)
    window.shown["L"] = f + 15
    window.recalc()
    blurred = np.array([rv.brightness(r) for r in rs])
    assert blurred.std() < 0.5 * sharp.std()
    window.set_lab(None)


def test_ring_zoom_and_sum_curve(window):
    ring = window.ring_view
    ring.scale, ring.center = 4.0, (0.002, 0.0)
    ring.image = None
    ring.repaint()
    image = ring.make_image(200)
    assert image.width() == 200
    ring.mouseDoubleClickEvent(None)
    assert ring.scale == 1.0
    window.second.setChecked(True)
    window.recalc()
    assert window.plot_r.curves[-1].name == "сумма"
    window.second.setChecked(False)
