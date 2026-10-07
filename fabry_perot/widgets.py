import math

import numpy as np

from .fmt import num, tick_text, ticks
from .physics import airy, airy_mean, order_at, phase, screen_mean
from .qt import (QColor, QFont, QImage, QPainter, QPen, QPixmap, QPointF, QRectF, QSize, Qt, QtGui,
                 QtWidgets, Signal, event_pos)
from .theme import THEME


def paint_card(p, rect, color, border=None):
    p.setPen(QColor(border or THEME["border"]))
    p.setBrush(QColor(color))
    p.drawRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), 14, 14)


def pill(p, left, top, text, background, color, bold=False):
    font = QFont(p.font())
    font.setBold(bold)
    p.setFont(font)
    width = p.fontMetrics().horizontalAdvance(text) + 14
    height = p.fontMetrics().height() + 6
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(background))
    p.drawRoundedRect(QRectF(left, top, width, height), 7, 7)
    p.setPen(QColor(color))
    p.drawText(QRectF(left, top, width, height), Qt.AlignmentFlag.AlignCenter, text)
    return width


def pixel_font(widget, px, bold=False):
    font = QFont(widget.font())
    font.setPixelSize(px)
    font.setBold(bold)
    return font


class Curve:
    def __init__(self, value, span, color, name):
        self.value, self.span, self.color, self.name = value, span, color, name

    def reading(self, x):
        return float(self.value(np.array([x]))[0])


def color_table(color):
    c = QColor(color)
    alpha = np.arange(256, dtype=np.uint32)
    r, g, b = ((alpha * k + 127) // 255 for k in (c.red(), c.green(), c.blue()))
    return (alpha << 24) | (r << 16) | (g << 8) | b


class Plot(QtWidgets.QWidget):
    hovered = Signal(object)
    picked = Signal(float, float)

    def __init__(self, title, xname, ylabel):
        super().__init__()
        self.title, self.xname, self.ylabel = title, xname, ylabel
        self.xlabel, self.xunit = "", ""
        self.full, self.ylim = (0.0, 1.0), (0.0, 1.0)
        self.zoom = None
        self.curves, self.marks, self.spans, self.points = [], [], [], []
        self.hover = None
        self.drag = None
        self.base = None
        self.setMouseTracking(True)
        self.setMinimumSize(260, 190)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def show_data(self, xlabel, xunit, xlim, ylim, curves, marks=(), spans=(), points=()):
        self.xlabel, self.xunit, self.full, self.ylim = xlabel, xunit, xlim, ylim
        self.curves, self.marks, self.spans = list(curves), list(marks), list(spans)
        self.points = list(points)
        self.refresh()

    def refresh(self):
        self.base = None
        self.update()

    def set_hover(self, x):
        if (x is None) != (self.hover is None) and len(self.curves) > 1:
            self.base = None
        self.hover = x
        self.update()

    def area(self):
        return QRectF(64, 64, self.width() - 86, self.height() - 114)

    def view(self):
        x0, x1 = self.full
        if self.zoom is None:
            return x0, x1
        a, b = self.zoom
        return x0 + a * (x1 - x0), x0 + b * (x1 - x0)

    def to_x(self, area, x):
        x0, x1 = self.view()
        return area.left() + (x - x0) / (x1 - x0) * area.width()

    def to_y(self, area, y):
        y0, y1 = self.ylim
        return area.bottom() - (y - y0) / (y1 - y0) * area.height()

    def resizeEvent(self, event):
        self.base = None

    def paintEvent(self, event):
        ratio = self.devicePixelRatioF()
        if self.base is None:
            self.base = QPixmap(int(self.width() * ratio), int(self.height() * ratio))
            self.base.setDevicePixelRatio(ratio)
            self.base.fill(Qt.GlobalColor.transparent)
            p = QPainter(self.base)
            self.draw_base(p)
            p.end()
        p = QPainter(self)
        p.drawPixmap(0, 0, self.base)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.draw_overlay(p)

    def draw_base(self, p):
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        paint_card(p, self.rect(), THEME["surface"])
        area = self.area()
        if area.width() < 40 or area.height() < 40:
            return
        (x0, x1), (y0, y1) = self.view(), self.ylim

        p.setFont(pixel_font(self, 14, True))
        p.setPen(THEME.color("text"))
        p.drawText(QPointF(20, 30), self.title)

        title_end = 20 + p.fontMetrics().horizontalAdvance(self.title) + 16
        p.setFont(pixel_font(self, 12))
        legend = self.curves if len(self.curves) > 1 and self.hover is None else []
        need = sum(p.fontMetrics().horizontalAdvance(c.name) + 40 for c in legend)
        right = self.width() - 20
        line = 30 if self.width() - 20 - need > title_end else 50
        for curve in reversed(legend):
            width = p.fontMetrics().horizontalAdvance(curve.name)
            p.setPen(THEME.color("muted"))
            p.drawText(QPointF(right - width, line), curve.name)
            p.setPen(QPen(QColor(curve.color), 3))
            p.drawLine(QPointF(right - width - 22, line - 5), QPointF(right - width - 8, line - 5))
            right -= width + 40

        p.setFont(pixel_font(self, 11))
        values, step = ticks(x0, x1)
        for v in values:
            X = self.to_x(area, v)
            p.setPen(THEME.color("grid"))
            p.drawLine(QPointF(X, area.bottom()), QPointF(X, area.top()))
            p.setPen(THEME.color("muted"))
            p.drawText(QRectF(X - 45, area.bottom() + 7, 90, 16), Qt.AlignmentFlag.AlignCenter,
                       tick_text(v, step))
        values, step = ticks(y0, y1, 5)
        for v in values:
            Y = self.to_y(area, v)
            p.setPen(THEME.color("grid"))
            p.drawLine(QPointF(area.left(), Y), QPointF(area.right(), Y))
            p.setPen(THEME.color("muted"))
            p.drawText(QRectF(0, Y - 8, area.left() - 10, 16),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, tick_text(v, step))
        p.setFont(pixel_font(self, 12))
        p.drawText(QRectF(area.left(), area.bottom() + 26, area.width(), 18),
                   Qt.AlignmentFlag.AlignCenter, self.xlabel)
        p.save()
        p.translate(18, area.center().y())
        p.rotate(-90)
        p.drawText(QRectF(-120, -9, 240, 18), Qt.AlignmentFlag.AlignCenter, self.ylabel)
        p.restore()

        for curve in self.curves:
            self.draw_curve(p, area, curve)
        p.setPen(QPen(THEME.color("surface"), 1.5))
        p.setBrush(THEME.color("orange"))
        for x, y in self.points:
            if x0 <= x <= x1 and y0 <= y <= y1:
                p.drawEllipse(QPointF(self.to_x(area, x), self.to_y(area, y)), 4.5, 4.5)
        p.setPen(QPen(THEME.color("axis"), 1))
        p.drawLine(area.bottomLeft(), area.bottomRight())
        p.drawLine(area.bottomLeft(), area.topLeft())

        p.setFont(pixel_font(self, 11, True))
        for x, color, label in self.marks:
            if x0 <= x <= x1:
                X = self.to_x(area, x)
                pen = QPen(QColor(color), 1.3)
                pen.setStyle(Qt.PenStyle.DashLine)
                p.setPen(pen)
                p.drawLine(QPointF(X, area.bottom()), QPointF(X, area.top()))
                back = QColor(color)
                back.setAlpha(40)
                pill(p, X + 4, area.bottom() - 26, label, back, color, True)

        p.setFont(pixel_font(self, 12, True))
        orange = THEME["orange"]
        for xa, xb, y, label in self.spans:
            a = QPointF(self.to_x(area, xa), self.to_y(area, y))
            b = QPointF(self.to_x(area, xb), self.to_y(area, y))
            p.setPen(QPen(QColor(orange), 1.6))
            p.drawLine(a, b)
            for q in (a, b):
                p.drawLine(QPointF(q.x(), q.y() - 5), QPointF(q.x(), q.y() + 5))
            width = p.fontMetrics().horizontalAdvance(label) + 14
            left = (a.x() + b.x() - width) / 2
            if b.x() - a.x() < width + 10:
                left = b.x() + 8
            top = a.y() - p.fontMetrics().height() - 12
            pill(p, left, top, label, THEME.color("surface", 235), orange, True)

    def draw_curve(self, p, area, curve):
        ratio = self.devicePixelRatioF()
        width = max(int(round(area.width() * ratio)), 1)
        height = max(int(round(area.height() * ratio)), 1)
        x0, x1 = self.view()
        y0, y1 = self.ylim
        lo, hi = curve.span(np.linspace(x0, x1, width + 1))
        scale = height / (y1 - y0)
        top = ((y1 - hi) * scale).astype(np.float32)[None, :]
        bottom = ((y1 - lo) * scale).astype(np.float32)[None, :]
        rows = np.arange(height, dtype=np.float32)[:, None]
        half = np.float32(0.95 * ratio)
        line = np.minimum(rows + 1, bottom + half)
        line -= np.maximum(rows, top - half)
        np.clip(line, 0, 1, out=line)
        fill = rows + 1 - top
        np.clip(fill, 0, 1, out=fill)
        fade = np.linspace(0.36 if THEME.dark else 0.24, 0.03, height, dtype=np.float32)[:, None]
        fill *= fade
        clear = 1 - line
        clear *= 1 - fill
        if THEME["glow"]:
            dist = np.maximum(top - rows - 0.5, rows + 0.5 - bottom)
            dist /= np.float32(3.2 * ratio)
            np.clip(dist, 0, 1, out=dist)
            glow = 1 - dist
            glow *= glow
            glow *= np.float32(0.3)
            clear *= 1 - glow
        alpha = ((1 - clear) * 255 + 0.5).astype(np.uint8)
        argb = color_table(curve.color)[alpha]
        image = QImage(argb.tobytes(), width, height, 4 * width, QImage.Format.Format_ARGB32_Premultiplied)
        image.setDevicePixelRatio(ratio)
        p.drawImage(area.topLeft(), image)

    def draw_overlay(self, p):
        area = self.area()
        if area.width() < 40 or area.height() < 40:
            return
        p.setFont(pixel_font(self, 12))
        if self.zoom is not None:
            a, b = self.zoom
            text = f"×{num(1 / (b - a), 3)} · двойной щелчок — весь график"
            width = p.fontMetrics().horizontalAdvance(text) + 14
            pill(p, area.right() - width - 4, area.top() + 4, text, THEME.color("raised", 235),
                 THEME["muted"])
        x0, x1 = self.view()
        h = self.hover
        if h is None or not x0 <= h <= x1 or not self.curves:
            return
        X = self.to_x(area, h)
        pen = QPen(THEME.color("text", 110), 1)
        pen.setStyle(Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.drawLine(QPointF(X, area.top()), QPointF(X, area.bottom()))
        parts = [f"{self.xname} = {num(h)} {self.xunit}".strip()]
        for curve in self.curves:
            v = curve.reading(h)
            Y = min(max(self.to_y(area, v), area.top()), area.bottom())
            p.setPen(QPen(THEME.color("surface"), 2))
            p.setBrush(QColor(curve.color))
            p.drawEllipse(QPointF(X, Y), 4.5, 4.5)
            parts.append(f"{curve.name} = {num(v, 3)}")
        text = "   ".join(parts)
        width = p.fontMetrics().horizontalAdvance(text) + 14
        title = pixel_font(self, 14, True)
        title_end = 20 + QtGui.QFontMetrics(title).horizontalAdvance(self.title) + 12
        top = 14 if self.width() - width - 16 > title_end else 36
        pill(p, max(self.width() - width - 16, 8), top, text, THEME.color("raised"), THEME["text"])

    def mousePressEvent(self, event):
        pos, area = event_pos(event), self.area()
        if event.button() == Qt.MouseButton.RightButton and area.contains(pos) and self.curves:
            x0, x1 = self.view()
            x = x0 + (pos.x() - area.left()) / area.width() * (x1 - x0)
            self.picked.emit(x, self.curves[-1].reading(x))
            return
        if event.button() == Qt.MouseButton.LeftButton and self.zoom is not None:
            self.drag = (event_pos(event).x(), self.zoom)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        self.drag = None
        self.setCursor(Qt.CursorShape.CrossCursor)

    def mouseMoveEvent(self, event):
        pos, area = event_pos(event), self.area()
        if self.drag is not None:
            start, (a, b) = self.drag
            shift = (pos.x() - start) / area.width() * (b - a)
            shift = min(max(shift, b - 1), a)
            self.zoom = (a - shift, b - shift)
            self.base = None
        x = None
        if area.contains(pos):
            x0, x1 = self.view()
            x = x0 + (pos.x() - area.left()) / area.width() * (x1 - x0)
        self.set_hover(x)
        self.hovered.emit(x)

    def leaveEvent(self, event):
        self.set_hover(None)
        self.hovered.emit(None)

    def mouseDoubleClickEvent(self, event):
        self.zoom = None
        self.refresh()

    def wheelEvent(self, event):
        steps = event.angleDelta().y() / 120
        area = self.area()
        if not steps or area.width() < 40:
            return
        a, b = self.zoom or (0.0, 1.0)
        at = min(max((event.position().x() - area.left()) / area.width(), 0.0), 1.0)
        span = min(max((b - a) * 0.8 ** steps, 1e-4), 1.0)
        center = a + at * (b - a)
        a = min(max(center - at * span, 0.0), 1.0 - span)
        self.zoom = None if span > 0.999 else (a, a + span)
        self.refresh()
        event.accept()


class RingView(QtWidgets.QWidget):
    hovered = Signal(object)
    picked = Signal(float, float)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(220, 220)
        self.setMouseTracking(True)
        self.data = None
        self.image = None
        self.index = {}
        self.glow = True
        self.hover = None
        self.scale = 1.0
        self.center = (0.0, 0.0)
        self.drag = None
        self.show_order = True

    def show_data(self, lines, half, caption, geom, F, tmax, defocus=0.0):
        if self.data is not None and abs(self.data[1] - half) > 1e-12:
            self.scale, self.center = 1.0, (0.0, 0.0)
        self.data = (lines, half, caption, geom, F, tmax, defocus)
        self.image = None
        self.update()

    def set_glow(self, on):
        self.glow = on
        self.image = None
        self.update()

    def set_hover(self, r_mm):
        self.hover = None if r_mm is None else r_mm * 1e-3
        self.update()

    def resizeEvent(self, event):
        self.image = None

    def place(self):
        size = min(self.width(), self.height()) - 12
        return size, (self.width() - size) / 2, (self.height() - size) / 2

    def to_screen(self, pos):
        size, left, top = self.place()
        pixel = 2 * self.data[1] / (size * self.scale)
        return (self.center[0] + (pos.x() - left - size / 2) * pixel,
                self.center[1] + (pos.y() - top - size / 2) * pixel)

    def brightness(self, r):
        lines, _, _, (d, n, L), F, tmax, rho = self.data
        if rho > 0:
            return sum(screen_mean(max(r - rho, 0.0), r + rho, lam, d, n, L, F, tmax) for lam, _ in lines) / len(lines)
        s = r / np.hypot(r, L)
        return sum(airy(phase(lam, d, n, s), F, tmax) for lam, _ in lines) / len(lines)

    def make_image(self, side, scale=None, center=None):
        lines, half, _, (d, n, f), F, tmax, rho = self.data
        scale = self.scale if scale is None else scale
        cx, cy = self.center if center is None else center
        pixel = 2 * half / (side * scale)
        key = (side, scale, cx, cy)
        index = self.index.get(key)
        if index is None:
            c = (np.arange(side) + 0.5 - side / 2) * pixel
            index = (4 * np.hypot(c[None, :] + cx, c[:, None] + cy) / pixel).astype(np.intp)
            self.index = {key: index}
        count = int(index.max()) + 1
        center_r = (np.arange(count) + 0.5) * pixel / 4
        r1, r2 = np.maximum(center_r - pixel / 2 - rho, 0.0), center_r + pixel / 2 + rho
        s1, s2 = r1 / np.hypot(r1, f), r2 / np.hypot(r2, f)
        if self.glow:
            sigma = max(side / 180, 2.0)
            half_k = int(3 * sigma)
            kernel = np.exp(-0.5 * (np.arange(-half_k, half_k + 1) / sigma) ** 2)
            kernel /= kernel.sum()
        rgb = np.zeros((count, 3))
        for lam, color in lines:
            bright = airy_mean(phase(lam, d, n, s1), phase(lam, d, n, s2), F, tmax) / len(lines)
            if self.glow:
                padded = np.pad(bright, half_k, mode="reflect")
                bright = bright + 0.6 * np.convolve(padded, kernel, mode="valid")
            rgb += np.clip(bright, 0, 1)[:, None] ** (1 / 2.2) * np.array(color)
        alpha = np.clip(half / pixel - (np.arange(count) + 0.5) / 4 + 0.5, 0, 1)
        v = (np.clip(rgb, 0, 1) * alpha[:, None] * 255 + 0.5).astype(np.uint32)
        a = (alpha * 255 + 0.5).astype(np.uint32)
        table = (a << 24) | (v[:, 0] << 16) | (v[:, 1] << 8) | v[:, 2]
        argb = table[index]
        return QImage(argb.tobytes(), side, side, 4 * side,
                      QImage.Format.Format_ARGB32_Premultiplied).copy()

    def decorate(self, image, size):
        p = QPainter(image)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c, R = QPointF(size / 2, size / 2), size / 2 - 0.6
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 50), 1.2))
        p.drawEllipse(c, R, R)
        for k in range(72):
            angle = math.radians(5 * k)
            long = k % 6 == 0
            p.setPen(QPen(QColor(255, 255, 255, 80 if long else 35), 1))
            inner = R - (8 if long else 4)
            p.drawLine(QPointF(c.x() + inner * math.cos(angle), c.y() + inner * math.sin(angle)),
                       QPointF(c.x() + R * math.cos(angle), c.y() + R * math.sin(angle)))
        p.end()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        size, left, top = self.place()
        if self.data is None or size < 40:
            return
        ratio = self.devicePixelRatioF()
        if self.image is None:
            self.image = self.make_image(int(size * ratio))
            self.image.setDevicePixelRatio(ratio)
            if self.scale == 1.0 and self.center == (0.0, 0.0):
                self.decorate(self.image, size)
        p.drawImage(QPointF(left, top), self.image)
        half = self.data[1]
        pixel = 2 * half / (size * self.scale)
        c = QPointF(left + size / 2 - self.center[0] / pixel, top + size / 2 - self.center[1] / pixel)

        dark = QColor(0, 0, 0, 170)
        p.setFont(pixel_font(self, 12))
        caption = self.data[2] + (f" · лупа ×{num(self.scale, 3)}" if self.scale > 1 else "")
        pill(p, 4, 4, caption, dark, "#DDE5EE")
        view_mm = 2 * half / self.scale * 1e3
        bar = ticks(0, view_mm, 4)[1]
        bar_px = bar / view_mm * size
        y = self.height() - 10
        pill(p, 4, y - p.fontMetrics().height() - 18, f"{tick_text(bar, bar)} мм", dark, "#DDE5EE")
        p.setPen(QPen(QColor("white"), 2))
        p.drawLine(QPointF(10, y), QPointF(10 + bar_px, y))

        if self.hover is not None and self.hover <= half:
            rp = self.hover / pixel
            pen = QPen(QColor(THEME["accent"]), 1.4)
            pen.setStyle(Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(c, rp, rp)
            bright = float(self.brightness(self.hover))
            text = f"r = {num(self.hover * 1e3)} мм"
            if self.show_order:
                lam = self.data[0][0][0]
                d, n, f = self.data[3]
                text += f" · m = {num(order_at(self.hover, lam, d, n, f), 7)}"
            text += f" · I = {num(bright, 3)}"
            p.setFont(pixel_font(self, 12 if self.width() > 380 else 11))
            pill(p, 4, p.fontMetrics().height() + 16, text, dark, "#5BE0CD")

    def mouseMoveEvent(self, event):
        if self.data is None:
            return
        pos = event_pos(event)
        if self.drag is not None:
            start, center = self.drag
            size = self.place()[0]
            pixel = 2 * self.data[1] / (size * self.scale)
            self.center = (center[0] - (pos.x() - start.x()) * pixel, center[1] - (pos.y() - start.y()) * pixel)
            self.image = None
        x, y = self.to_screen(pos)
        r = math.hypot(x, y)
        self.hover = r if r <= self.data[1] else None
        self.hovered.emit(None if self.hover is None else self.hover * 1e3)
        self.update()

    def mousePressEvent(self, event):
        if self.data is None:
            return
        pos = event_pos(event)
        if event.button() == Qt.MouseButton.RightButton and self.hover is not None:
            bright = float(self.brightness(self.hover))
            self.picked.emit(self.hover * 1e3, bright)
        elif event.button() == Qt.MouseButton.LeftButton and self.scale > 1:
            self.drag = (pos, self.center)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        self.drag = None
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseDoubleClickEvent(self, event):
        self.scale, self.center = 1.0, (0.0, 0.0)
        self.image = None
        self.update()

    def wheelEvent(self, event):
        if self.data is None:
            return
        steps = event.angleDelta().y() / 120
        new = min(max(self.scale * 1.25 ** steps, 1.0), 40.0)
        if new == self.scale:
            return
        x, y = self.to_screen(event.position())
        k = self.scale / new
        self.center = (x - (x - self.center[0]) * k, y - (y - self.center[1]) * k)
        self.scale = new
        if new == 1.0:
            self.center = (0.0, 0.0)
        self.image = None
        self.update()
        event.accept()

    def leaveEvent(self, event):
        self.hover = None
        self.hovered.emit(None)
        self.update()


class ToggleSwitch(QtWidgets.QCheckBox):
    def __init__(self, text, text_color=None):
        super().__init__(text)
        self.text_color = text_color

    def sizeHint(self):
        fm = self.fontMetrics()
        return QSize(40 + fm.horizontalAdvance(self.text()), max(22, fm.height() + 4))

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = 32, 18
        y = (self.height() - h) / 2
        on = self.isChecked()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(THEME.color("accent") if on else THEME.color("line"))
        p.drawRoundedRect(QRectF(0, y, w, h), h / 2, h / 2)
        p.setBrush(QColor("white"))
        p.drawEllipse(QRectF((w - h + 2) if on else 2, y + 2, h - 4, h - 4))
        p.setPen(QColor(self.text_color) if self.text_color else THEME.color("text"))
        p.drawText(QRectF(w + 8, 0, self.width() - w - 8, self.height()),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())


def card_title(text):
    label = QtWidgets.QLabel(text.upper())
    label.setObjectName("cardTitle")
    font = QFont(label.font())
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
    label.setFont(font)
    return label


def make_card(title=None, name="card"):
    frame = QtWidgets.QFrame()
    frame.setObjectName(name)
    layout = QtWidgets.QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 14)
    layout.setSpacing(6)
    if title:
        layout.addWidget(card_title(title))
    return frame, layout


def polish(widget, kind):
    widget.setProperty("kind", kind)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
