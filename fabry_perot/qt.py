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
QAction = QtGui.QAction if QT6 else QtWidgets.QAction


def event_pos(event):
    return event.position() if QT6 else event.localPos()
