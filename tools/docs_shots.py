import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fabry_perot.qt import QtCore, QtWidgets, QColor, QFont, QPainter, QPen, QPointF, QRectF, Qt

QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat, QtCore.QSettings.Scope.UserScope, tempfile.mkdtemp())

from fabry_perot.app import create_app
from fabry_perot.params import PRESETS
from fabry_perot.theme import THEME
from fabry_perot.window import MainWindow

OUT = os.path.join(ROOT, "docs", "img")


def wait(ms):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def settle(win):
    wait(1100)
    win.recalc()
    QtWidgets.QApplication.processEvents()
    wait(100)


def rect_in(win, widget):
    top_left = widget.mapTo(win, QtCore.QPoint(0, 0))
    return QRectF(top_left.x(), top_left.y(), widget.width(), widget.height())


def callouts(image, marks):
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    font = QFont("Liberation Sans")
    font.setPixelSize(17)
    font.setBold(True)
    p.setFont(font)
    for number, point in marks:
        p.setPen(QPen(QColor("white"), 3))
        p.setBrush(QColor("#d9660b"))
        p.drawEllipse(point, 15, 15)
        p.setPen(QColor("white"))
        p.drawText(QRectF(point.x() - 15, point.y() - 15, 30, 30), Qt.AlignmentFlag.AlignCenter, str(number))
    p.end()


def main():
    os.makedirs(OUT, exist_ok=True)
    app = create_app(["docs"])
    win = MainWindow()
    win.resize(1600, 1230)
    win.show()
    THEME.set("light")
    win.apply_theme()
    win.apply_preset(PRESETS[0][1], PRESETS[0][2])
    settle(win)

    image = win.grab().toImage()
    side = win.centralWidget().layout().itemAt(1).widget().widget(0).widget()
    cards = [c for c in side.findChildren(QtWidgets.QFrame) if c.objectName() == "card"]
    marks = []
    for number, card in zip((1, 2, 3, 4), cards):
        r = rect_in(win, card)
        marks.append((number, QPointF(r.right() - 26, r.top() + 22)))
    for number, widget in ((5, win.plot_t), (6, win.ring_view.parentWidget()), (7, win.plot_r)):
        r = rect_in(win, widget)
        marks.append((number, QPointF(r.right() - 26, r.bottom() - 26)))
    tile = rect_in(win, win.tiles[0][0].parentWidget())
    marks.append((8, QPointF(tile.right() + 5, tile.bottom() + 5)))
    r = rect_in(win, win.table)
    marks.append((9, QPointF(r.right() - 26, r.bottom() - 26)))
    r = rect_in(win, win.verdict)
    marks.append((10, QPointF(r.right() - 14, r.top() - 4)))
    r = rect_in(win, win.theme_button)
    marks.append((11, QPointF(r.left() - 380, r.bottom() + 12)))
    callouts(image, marks)
    image.save(os.path.join(OUT, "window_light.png"))

    xa, xb = win.plot_t.spans[1][:2]
    (f0, f1), c, w = win.plot_t.full, (xa + xb) / 2, xb - xa
    win.plot_t.zoom = ((c - 4 * w - f0) / (f1 - f0), (c + 4 * w - f0) / (f1 - f0))
    win.plot_t.set_hover(xa)
    win.plot_t.refresh()
    QtWidgets.QApplication.processEvents()
    win.plot_t.grab().save(os.path.join(OUT, "plot_zoom.png"))
    win.plot_t.zoom = None
    win.plot_t.set_hover(None)

    win.ring_view.set_hover(3.003)
    win.plot_r.set_hover(3.003)
    QtWidgets.QApplication.processEvents()
    win.ring_view.parentWidget().grab().save(os.path.join(OUT, "rings_hover.png"))
    win.plot_r.grab().save(os.path.join(OUT, "profile_hover.png"))
    win.ring_view.set_hover(None)
    win.plot_r.set_hover(None)

    for R in (0.5, 0.9, 0.98):
        win.params["R"].set(R)
        win.shown["R"] = R
        win.recalc()
        win.write_rings(os.path.join(OUT, f"rings_R{int(R * 100)}.png"), side=520)

    win.apply_preset(PRESETS[1][1], PRESETS[1][2])
    settle(win)
    win.write_rings(os.path.join(OUT, "doublet_resolved.png"), side=520)
    win.params["dlam"].set(20.0)
    win.shown["dlam"] = 20.0
    win.recalc()
    win.write_rings(os.path.join(OUT, "doublet_merged.png"), side=520)

    from fabry_perot.lab import Variant
    from fabry_perot import physics as ph
    import random
    win.resize(1600, 1000)
    win.student = ("Иванов И. И.", "СМ1-21")
    win.journal.clear_all()
    v = Variant(0)
    win.set_lab(v)
    for key, value in (("d", v.d_rings), ("f", v.f_rings), ("L", v.f_rings), ("screen", 10.0), ("R", 0.9),
                       ("dd", 0.0)):
        win.params[key].set(value)
        win.shown[key] = value
    win.second.setChecked(False)
    win.recalc()
    win.journal.select("rings")
    rng = random.Random("example-rings")
    radii = ph.ring_radii(v.lam * 1e-9, v.d_rings * 1e-3, 1.0, v.f_rings * 1e-3, 0.010)[:6] * 1e3
    for r in radii:
        win.ring_view.picked.emit(round(float(r) + rng.gauss(0, 0.006), 3), 0.8)
    win.ring_view.set_hover(float(radii[3]))
    win.plot_r.set_hover(float(radii[3]))
    QtWidgets.QApplication.processEvents()
    wait(200)
    image = win.grab().toImage()
    marks = []
    r = rect_in(win, win.lab_badge)
    marks.append((1, QPointF(r.left() - 16, r.center().y())))
    r = rect_in(win, win.params["lam"].secret)
    marks.append((2, QPointF(r.left() - 18, r.center().y())))
    r = rect_in(win, win.params["L"].label)
    marks.append((3, QPointF(r.left() + 250, r.center().y())))
    r = rect_in(win, win.journal.combo)
    marks.append((4, QPointF(r.left() - 16, r.center().y())))
    r = rect_in(win, win.journal.table)
    marks.append((5, QPointF(r.right() - 22, r.top() + 22)))
    r = rect_in(win, win.journal.record_button)
    marks.append((6, QPointF(r.left() - 16, r.center().y())))
    r = rect_in(win, win.journal.plot)
    marks.append((7, QPointF(r.right() - 22, r.top() + 22)))
    r = rect_in(win, win.journal.result)
    marks.append((8, QPointF(r.right() - 20, r.top() - 2)))
    callouts(image, marks)
    image.save(os.path.join(OUT, "window_lab.png"))
    win.journal.grab().save(os.path.join(OUT, "journal.png"))

    win.ring_view.scale, win.ring_view.center = 6.0, (float(radii[4]) * 1e-3, 0.0)
    win.ring_view.image = None
    win.ring_view.set_hover(float(radii[4]))
    QtWidgets.QApplication.processEvents()
    win.ring_view.parentWidget().grab().save(os.path.join(OUT, "rings_zoom.png"))
    win.ring_view.scale, win.ring_view.center = 1.0, (0.0, 0.0)
    win.ring_view.image = None
    win.set_lab(None)

    win.apply_preset(dict(lam=589.0, d=1.0, dd=0.0, R=0.9, A=0.0, n=1.0, f=200.0, screen=10.0), 6.2)
    settle(win)
    win.plot_r.zoom = (0.30, 0.42)
    win.plot_r.refresh()
    win.plot_r.set_hover(3.715)
    QtWidgets.QApplication.processEvents()
    win.plot_r.grab().save(os.path.join(OUT, "profile_sum.png"))
    win.plot_r.zoom = None

    THEME.set("dark")
    win.apply_theme()
    win.resize(1600, 960)
    win.apply_preset(PRESETS[0][1], PRESETS[0][2])
    settle(win)
    win.plot_t.set_hover(12.0)
    win.ring_view.set_hover(3.0)
    win.plot_r.set_hover(3.0)
    QtWidgets.QApplication.processEvents()
    win.grab().save(os.path.join(OUT, "window_dark.png"))
    print("docs/img: снимки готовы")
    app.quit()


if __name__ == "__main__":
    main()
