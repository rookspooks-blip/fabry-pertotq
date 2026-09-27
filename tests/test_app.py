"""Окно запускается (без экрана), считает, плавно переходит к новым значениям и сохраняет файлы."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("numpy")

from fabry_perot.qt import QtCore, QtWidgets  # noqa: E402


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
    row.spin.setValue(10.0)                    # как будто ввели число и нажали Enter
    assert window.shown["d"] == start          # сразу картинка не прыгает
    wait(350)
    assert start < window.shown["d"] < 10.0    # на полпути
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
