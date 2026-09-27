"""Запуск программы: приложение Qt с нашим шрифтом, значком и оформлением."""

import sys

from .qt import QT6, QFont, Qt, QtCore, QtGui, QtWidgets
from .theme import FONTS, app_icon
from .window import MainWindow


def create_app(argv=None):
    """Приложение Qt с нашим шрифтом, значком и оформлением."""
    if not QT6:
        # в Qt 5 чёткость на экранах с масштабом 125–150 % включается вручную
        QtWidgets.QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        QtWidgets.QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    try:
        # масштаб 125 % остаётся 125 %, а не округляется до 100 или 200 %
        QtGui.QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except AttributeError:
        pass
    app = QtWidgets.QApplication(sys.argv if argv is None else argv)
    app.setApplicationName("FabryPerot")
    app.setStyle("Fusion")                         # одинаковый вид на Windows, macOS и Linux
    font = QFont(app.font())
    font.setFamilies(FONTS)
    app.setFont(font)
    app.setWindowIcon(app_icon())
    # десятичная запятая в полях ввода
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.Language.Russian, QtCore.QLocale.Country.Russia))
    return app


def main():
    # --selftest: открыть окно, посчитать и закрыться (проверка собранной программы)
    selftest = "--selftest" in sys.argv
    app = create_app([arg for arg in sys.argv if arg != "--selftest"])
    window = MainWindow()
    window.show()
    if selftest:
        def finish():
            window.recalc()
            print("selftest ok" if window.results else "selftest failed", flush=True)
            app.exit(0 if window.results else 1)
        QtCore.QTimer.singleShot(1500, finish)
    sys.exit(app.exec())
