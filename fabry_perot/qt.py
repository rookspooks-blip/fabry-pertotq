"""Подключение Qt: PyQt6 (Windows 10/11, macOS, Linux) или PyQt5 (Windows 7, 8, 8.1).

Qt 6 не работает на Windows 7, 8 и 8.1, поэтому там ставится PyQt5 — программа
подключит его сама. Переменная окружения FABRY_QT=5 заставляет взять PyQt5
даже там, где есть PyQt6 (так проверяется сборка для старых Windows).
Здесь же собраны мелкие различия между Qt 5 и Qt 6.
"""

import os

QT6 = False
if os.environ.get("FABRY_QT") != "5":
    try:
        from PyQt6 import QtCore, QtGui, QtWidgets
        QT6 = True
    except ImportError:
        pass
if not QT6:
    from PyQt5 import QtCore, QtGui, QtWidgets

Qt = QtCore.Qt
Signal = QtCore.pyqtSignal
QPointF, QRectF, QLineF, QSize = QtCore.QPointF, QtCore.QRectF, QtCore.QLineF, QtCore.QSize
QBrush, QColor, QFont, QIcon, QImage = QtGui.QBrush, QtGui.QColor, QtGui.QFont, QtGui.QIcon, QtGui.QImage
QLinearGradient, QRadialGradient = QtGui.QLinearGradient, QtGui.QRadialGradient
QPainter, QPalette, QPen, QPixmap, QPolygonF = (QtGui.QPainter, QtGui.QPalette, QtGui.QPen,
                                                QtGui.QPixmap, QtGui.QPolygonF)
# QAction в Qt 6 переехал из QtWidgets в QtGui
QAction = QtGui.QAction if QT6 else QtWidgets.QAction


def event_pos(event):
    """Положение мыши в событии как QPointF (в Qt 5 и Qt 6 метод называется по-разному)."""
    return event.position() if QT6 else event.localPos()
