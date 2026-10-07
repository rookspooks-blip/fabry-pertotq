import sys

from .qt import QT6, QFont, Qt, QtCore, QtGui, QtWidgets
from .theme import FONTS, app_icon
from .window import MainWindow


def create_app(argv=None):
    if not QT6:
        QtWidgets.QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        QtWidgets.QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    try:
        QtGui.QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except AttributeError:
        pass
    app = QtWidgets.QApplication(sys.argv if argv is None else argv)
    app.setApplicationName("FabryPerot")
    app.setStyle("Fusion")
    font = QFont(app.font())
    font.setFamilies(FONTS)
    app.setFont(font)
    app.setWindowIcon(app_icon())
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.Language.Russian, QtCore.QLocale.Country.Russia))
    return app


def main():
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
