"""Снимки окна программы для методичек (запускается без экрана, QT_QPA_PLATFORM=offscreen).

Результат — картинки в docs/img/. Вызывается из tools/build_docs.py.
"""

import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fabry_perot.qt import QtCore, QtWidgets, QColor, QFont, QPainter, QPen, QPointF, QRectF, Qt  # noqa: E402

# настройки программы — во временной папке, чтобы не зависеть от прошлых запусков
QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat, QtCore.QSettings.Scope.UserScope, tempfile.mkdtemp())

from fabry_perot.app import create_app  # noqa: E402
from fabry_perot.params import PRESETS  # noqa: E402
from fabry_perot.theme import THEME  # noqa: E402
from fabry_perot.window import MainWindow  # noqa: E402

OUT = os.path.join(ROOT, "docs", "img")


def wait(ms):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def settle(win):
    """Дождаться конца плавных переходов и перерисовки."""
    wait(1100)
    win.recalc()
    QtWidgets.QApplication.processEvents()
    wait(100)


def rect_in(win, widget):
    top_left = widget.mapTo(win, QtCore.QPoint(0, 0))
    return QRectF(top_left.x(), top_left.y(), widget.width(), widget.height())


def callouts(image, marks):
    """Номера-кружки поверх снимка: marks — [(номер, точка)]."""
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

    # 1. Окно целиком с номерами частей (светлая тема — для печати)
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

    # 2. Измерение курсором: увеличенный пик и перекрестие на половине высоты
    xa, xb = win.plot_t.spans[1][:2]               # ширина пика на половине высоты
    (f0, f1), c, w = win.plot_t.full, (xa + xb) / 2, xb - xa
    win.plot_t.zoom = ((c - 4 * w - f0) / (f1 - f0), (c + 4 * w - f0) / (f1 - f0))
    win.plot_t.set_hover(xa)
    win.plot_t.refresh()
    QtWidgets.QApplication.processEvents()
    win.plot_t.grab().save(os.path.join(OUT, "plot_zoom.png"))
    win.plot_t.zoom = None
    win.plot_t.set_hover(None)

    # 3. Кольца с курсором и связанный разрез
    win.ring_view.set_hover(3.003)
    win.plot_r.set_hover(3.003)
    QtWidgets.QApplication.processEvents()
    win.ring_view.parentWidget().grab().save(os.path.join(OUT, "rings_hover.png"))
    win.plot_r.grab().save(os.path.join(OUT, "profile_hover.png"))
    win.ring_view.set_hover(None)
    win.plot_r.set_hover(None)

    # 4. Кольца при разном отражении зеркал
    for R in (0.5, 0.9, 0.98):
        win.params["R"].set(R)
        win.shown["R"] = R
        win.recalc()
        win.write_rings(os.path.join(OUT, f"rings_R{int(R * 100)}.png"), side=520)

    # 5. Натриевый дублет: различимы и не различимы
    win.apply_preset(PRESETS[1][1], PRESETS[1][2])
    settle(win)
    win.write_rings(os.path.join(OUT, "doublet_resolved.png"), side=520)
    win.params["dlam"].set(20.0)
    win.shown["dlam"] = 20.0
    win.recalc()
    win.write_rings(os.path.join(OUT, "doublet_merged.png"), side=520)

    # 6. Тёмная тема целиком (для методички по визуальной части)
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
