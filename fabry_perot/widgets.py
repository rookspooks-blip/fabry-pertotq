"""Виджеты: график, картина колец, переключатель и карточки."""

import math

import numpy as np

from .fmt import num, tick_text, ticks
from .physics import order_at
from .qt import (QBrush, QColor, QFont, QImage, QLinearGradient, QLineF, QPainter, QPen, QPixmap,
                 QPointF, QPolygonF, QRectF, QSize, Qt, QtGui, QtWidgets, Signal, event_pos)
from .theme import THEME


def paint_card(p, rect, color, border=None):
    """Фон виджета: карточка со скруглёнными углами."""
    p.setPen(QColor(border or THEME["border"]))
    p.setBrush(QColor(color))
    p.drawRoundedRect(QRectF(rect).adjusted(0.5, 0.5, -0.5, -0.5), 14, 14)


def pill(p, left, top, text, background, color, bold=False):
    """Подпись на скруглённой подложке, чтобы её было видно поверх рисунка.
    Возвращает ширину подложки."""
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


class Plot(QtWidgets.QWidget):
    """График на QPainter: сетка, подписи, кривые, вертикальные метки и отрезки-измерения.

    Узкий пик бывает тоньше пикселя. Чтобы он не пропал, для каждого столбца
    пикселей берутся минимум и максимум всех точек, попавших в этот столбец,
    и рисуется чёрточка между ними (так рисуют цифровые осциллографы).

    Мышь: наведение — значения под курсором, колёсико — масштаб по горизонтали,
    перетаскивание — сдвиг, двойной щелчок — вернуть весь график.
    Готовый рисунок хранится в картинке-«кэше», поэтому движение мыши
    перерисовывает только перекрестие, а не всю кривую.
    """

    hovered = Signal(object)                       # x под курсором или None

    def __init__(self, title, xname, ylabel):
        super().__init__()
        self.title, self.xname, self.ylabel = title, xname, ylabel
        self.xlabel, self.xunit = "", ""
        self.full, self.ylim = (0.0, 1.0), (0.0, 1.0)
        self.zoom = None                           # видимая часть графика: доли (от, до) всей ширины
        self.curves, self.marks, self.spans = [], [], []
        self.hover = None
        self.drag = None
        self.base = None                           # кэш: готовый рисунок без перекрестия
        self.setMouseTracking(True)
        self.setMinimumSize(260, 190)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def show_data(self, xlabel, xunit, xlim, ylim, curves, marks=(), spans=()):
        """curves: (x, y, цвет, имя); marks: (x, цвет, подпись); spans: (x1, x2, y, подпись)."""
        self.xlabel, self.xunit, self.full, self.ylim = xlabel, xunit, xlim, ylim
        self.curves, self.marks, self.spans = list(curves), list(marks), list(spans)
        self.refresh()

    def refresh(self):
        self.base = None                           # старый рисунок выбрасываем
        self.update()                              # попросить Qt перерисовать виджет

    def set_hover(self, x):
        """Перекрестие по команде другого виджета (курсор над картиной колец)."""
        if (x is None) != (self.hover is None) and len(self.curves) > 1:
            self.base = None                       # легенда уступает место значениям
        self.hover = x
        self.update()

    def area(self):
        return QRectF(64, 64, self.width() - 86, self.height() - 114)   # поле графика

    def view(self):
        """Видимый диапазон по горизонтали с учётом масштаба."""
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
        ratio = self.devicePixelRatioF()           # экраны с масштабом 125–200 %, Retina
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

        # легенда справа от заголовка: цветная чёрточка и имя кривой
        p.setFont(pixel_font(self, 12))
        right = self.width() - 20
        legend = self.curves if len(self.curves) > 1 and self.hover is None else []
        for x, y, color, name in reversed(legend):
            width = p.fontMetrics().horizontalAdvance(name)
            p.setPen(THEME.color("muted"))
            p.drawText(QPointF(right - width, 30), name)
            p.setPen(QPen(QColor(color), 3))
            p.drawLine(QPointF(right - width - 22, 25), QPointF(right - width - 8, 25))
            right -= width + 40

        # сетка и подписи делений по горизонтали и вертикали
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
        p.save()                                   # подпись оси Y — повёрнутая
        p.translate(18, area.center().y())
        p.rotate(-90)
        p.drawText(QRectF(-120, -9, 240, 18), Qt.AlignmentFlag.AlignCenter, self.ylabel)
        p.restore()

        # кривые рисуем только внутри поля графика
        p.setClipRect(area.adjusted(0, -2, 0, 0))
        for x, y, color, _ in self.curves:
            self.draw_curve(p, area, x, y, QColor(color))
        p.setClipping(False)
        p.setPen(QPen(THEME.color("axis"), 1))     # оси: только слева и снизу
        p.drawLine(area.bottomLeft(), area.bottomRight())
        p.drawLine(area.bottomLeft(), area.topLeft())

        # вертикальные пунктирные метки: положения спектральных линий, радиусы колец
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

        # отрезки-измерения: Δλ между пиками и ширина пика на половине высоты
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
            if b.x() - a.x() < width + 10:         # отрезок короче подписи — пишем справа
                left = b.x() + 8
            top = a.y() - p.fontMetrics().height() - 12
            pill(p, left, top, label, THEME.color("surface", 235), orange, True)

    def draw_curve(self, p, area, x, y, color):
        """Кривая с заливкой: по минимумам и максимумам в столбцах пикселей или по точкам."""
        x0, x1 = self.view()
        y0, y1 = self.ylim
        # берём только видимую часть (плюс по точке с краёв)
        i0 = max(int(np.searchsorted(x, x0)) - 1, 0)
        i1 = min(int(np.searchsorted(x, x1)) + 1, len(x))
        x, y = x[i0:i1], y[i0:i1]
        if x.size < 2:
            return
        px = area.left() + (x - x0) / (x1 - x0) * area.width()
        scale = area.height() / (y1 - y0)
        if x.size <= 2 * area.width():
            # точек меньше, чем пикселей (график увеличен) — соединяем точки как есть
            xs, top = px.tolist(), (area.bottom() - (y - y0) * scale).tolist()
            lines = [QLineF(a, b, c, d) for a, b, c, d in zip(xs, top, xs[1:], top[1:])]
        else:
            col = np.floor(px - area.left()).astype(int)
            start = np.flatnonzero(np.r_[True, col[1:] != col[:-1]])    # начало каждого столбца
            low, high = np.minimum.reduceat(y, start), np.maximum.reduceat(y, start)
            xs = (area.left() + col[start] + 0.5).tolist()
            top = (area.bottom() - (high - y0) * scale).tolist()
            bottom = (area.bottom() - (low - y0) * scale).tolist()
            # отрезки от столбца к соседнему и вертикальные чёрточки там, где кривая
            # внутри столбца поднимается и падает
            lines = [QLineF(a, b, c, d) for a, b, c, d in zip(xs, top, xs[1:], top[1:])]
            lines += [QLineF(a, b, a, c) for a, b, c in zip(xs, top, bottom) if c - b > 1]

        # 1. Заливка под кривой: сверху цвет кривой, книзу прозрачная. Сглаживание ей не нужно.
        grad = QLinearGradient(0, area.top(), 0, area.bottom())
        c1, c2 = QColor(color), QColor(color)
        c1.setAlpha(90 if THEME.dark else 60)
        c2.setAlpha(8)
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawPolygon(QPolygonF([QPointF(xs[0], area.bottom())]
                                + [QPointF(a, b) for a, b in zip(xs, top)]
                                + [QPointF(xs[-1], area.bottom())]))

        # 2. Сама кривая. Перо «косметическое»: его толщина задаётся прямо в точках
        #    экрана. На Retina-экране (масштаб 2) обычное перо превращает каждую линию
        #    в сложную фигуру, и узкие пики рисуются в десятки раз медленнее.
        ratio = self.devicePixelRatioF()
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setBrush(Qt.BrushStyle.NoBrush)
        if THEME["glow"]:                          # в тёмной теме — мягкое свечение под линией
            glow = QColor(color)
            glow.setAlpha(55)
            pen = QPen(glow, 5 * ratio)
            pen.setCosmetic(True)
            p.setPen(pen)
            p.drawLines(lines)
        pen = QPen(color, 1.7 * ratio)
        pen.setCosmetic(True)
        p.setPen(pen)
        p.drawLines(lines)

    def draw_overlay(self, p):
        """Поверх готового рисунка: перекрестие со значениями и значок масштаба."""
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
        for x, y, color, name in self.curves:
            if not x[0] <= h <= x[-1]:
                continue
            v = float(np.interp(h, x, y))
            Y = min(max(self.to_y(area, v), area.top()), area.bottom())
            p.setPen(QPen(THEME.color("surface"), 2))
            p.setBrush(QColor(color))
            p.drawEllipse(QPointF(X, Y), 4.5, 4.5)
            parts.append(f"{name} = {num(v, 3)}")
        # значения пишем в строке заголовка, справа — там они не закрывают измерения
        text = "   ".join(parts)
        width = p.fontMetrics().horizontalAdvance(text) + 14
        title = pixel_font(self, 14, True)
        title_end = 20 + QtGui.QFontMetrics(title).horizontalAdvance(self.title) + 12
        top = 14 if self.width() - width - 16 > title_end else 36
        pill(p, self.width() - width - 16, top, text, THEME.color("raised"), THEME["text"])

    # --- мышь ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.zoom is not None:
            self.drag = (event_pos(event).x(), self.zoom)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        self.drag = None
        self.setCursor(Qt.CursorShape.CrossCursor)

    def mouseMoveEvent(self, event):
        pos, area = event_pos(event), self.area()
        if self.drag is not None:                  # перетаскивание: сдвиг видимой части
            start, (a, b) = self.drag
            shift = (pos.x() - start) / area.width() * (b - a)
            shift = min(max(shift, b - 1), a)      # не уходить за края графика
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
        center = a + at * (b - a)                  # точка под курсором остаётся на месте
        a = min(max(center - at * span, 0.0), 1.0 - span)
        self.zoom = None if span > 0.999 else (a, a + span)
        self.refresh()
        event.accept()


class RingView(QtWidgets.QWidget):
    """Картина колец на круглом экране в фокусе линзы — как в окуляре.

    Яркость пикселя — среднее значение T по его ширине: у края кольца бывают
    тоньше пикселя, и без усреднения картинка покрылась бы муаром.
    """

    hovered = Signal(object)                       # радиус под курсором в мм или None

    def __init__(self):
        super().__init__()
        self.setMinimumSize(220, 220)
        self.setMouseTracking(True)
        self.data = None
        self.image = None
        self.index = {}                            # для каждого размера — номер ячейки каждого пикселя
        self.glow = True
        self.hover = None                          # радиус под курсором, м

    def show_data(self, r, layers, half, caption, geom):
        """r — радиусы, м; layers — [(T(r), цвет)] по одному на линию; half — радиус экрана, м;
        geom — (λ, d, n, f) для подсказки о порядке кольца."""
        self.data = (r, layers, half, caption, geom)
        self.image = None                          # старую картинку выбрасываем
        self.update()

    def set_glow(self, on):
        self.glow = on
        self.image = None
        self.update()

    def set_hover(self, r_mm):
        self.hover = None if r_mm is None else r_mm * 1e-3
        self.update()

    def resizeEvent(self, event):
        self.image = None                          # размер изменился — пересчитаем картинку

    def place(self):
        """Где стоит круглый экран: (размер, левый край, верхний край)."""
        size = min(self.width(), self.height()) - 12
        return size, (self.width() - size) / 2, (self.height() - size) / 2

    def make_image(self, side):
        """Круглая картинка диаметром side пикселей (за кругом — прозрачно).

        Цвет зависит только от расстояния до центра. Поэтому сначала считаем
        цвет для каждого расстояния с шагом в четверть пикселя (это короткая
        «таблица цветов»), а потом каждый пиксель просто берёт цвет из неё.
        """
        r, layers, half = self.data[:3]
        index = self.index.get(side)
        if index is None:
            # расстояние каждого пикселя от центра в четвертях пикселя; зависит
            # только от размера картинки, поэтому считаем один раз
            c = np.arange(side) + 0.5 - side / 2
            index = (4 * np.hypot(c[None, :], c[:, None])).astype(np.intp)
            self.index = {side: index}
        count = int(index.max()) + 1
        pixel = 2 * half / side                    # размер одного пикселя на экране, м
        radius = (np.arange(count) + 0.5) * pixel / 4    # расстояния из таблицы, м
        step = r[1] - r[0]
        k = max(1, int(round(pixel / step)))       # сколько точек профиля в одном пикселе
        if self.glow:
            # свечение: к яркости добавляем её размытую копию (как ореол на фотографии)
            sigma = max(side / 180, 2.0)           # в четвертях пикселя
            half_k = int(3 * sigma)
            kernel = np.exp(-0.5 * (np.arange(-half_k, half_k + 1) / sigma) ** 2)
            kernel /= kernel.sum()
        rgb = np.zeros((count, 3))
        for T, color in layers:
            # скользящее среднее по k точкам через накопленные суммы — быстро
            sums = np.concatenate(([0.0], np.cumsum(T)))
            mean = (sums[k:] - sums[:-k]) / k
            centers = r[:len(mean)] + (k - 1) / 2 * step
            bright = np.interp(radius, centers, mean) / len(layers)   # две линии делят свет пополам
            if self.glow:
                padded = np.pad(bright, half_k, mode="reflect")
                bright = bright + 0.6 * np.convolve(padded, kernel, mode="valid")
            # гамма монитора: без неё тусклые кольца слились бы с чёрным фоном
            rgb += np.clip(bright, 0, 1)[:, None] ** (1 / 2.2) * np.array(color)
        rgb = np.clip(rgb, 0, 1)
        # край круга сглаженный: прозрачность плавно растёт на последнем пикселе
        alpha = np.clip(side / 2 - (np.arange(count) + 0.5) / 4 + 0.5, 0, 1)
        v = (rgb * 255 + 0.5).astype(np.uint32)
        a = (alpha * 255 + 0.5).astype(np.uint32)
        table = (a << 24) | (v[:, 0] << 16) | (v[:, 1] << 8) | v[:, 2]
        argb = table[index].astype(np.uint32)      # каждому пикселю — цвет по его расстоянию
        return QImage(argb.tobytes(), side, side, 4 * side, QImage.Format.Format_ARGB32).copy()

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
        p.drawImage(QPointF(left, top), self.image)
        c, R = QPointF(left + size / 2, top + size / 2), size / 2
        half = self.data[2]

        # оправа окуляра: тонкий ободок и деления через 5°, длинные — через 30°
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

        dark = QColor(0, 0, 0, 170)
        p.setFont(pixel_font(self, 12))
        # подпись и масштабная линейка «круглой» длины
        pill(p, 4, 4, self.data[3], dark, "#DDE5EE")
        half_mm = half * 1e3
        bar = ticks(0, 2 * half_mm, 4)[1]
        bar_px = bar / (2 * half_mm) * size
        y = self.height() - 10
        pill(p, 4, y - p.fontMetrics().height() - 18, f"{tick_text(bar, bar)} мм", dark, "#DDE5EE")
        p.setPen(QPen(QColor("white"), 2))
        p.drawLine(QPointF(10, y), QPointF(10 + bar_px, y))

        # курсор: окружность выбранного радиуса и значения на ней
        if self.hover is not None and self.hover <= half:
            rp = self.hover / half * R
            pen = QPen(QColor(THEME["accent"]), 1.4)
            pen.setStyle(Qt.PenStyle.DashLine)
            p.setPen(pen)
            p.drawEllipse(c, rp, rp)
            r, layers = self.data[0], self.data[1]
            lam, d, n, f = self.data[4]
            bright = sum(float(np.interp(self.hover, r, T)) for T, _ in layers) / len(layers)
            text = (f"r = {num(self.hover * 1e3)} мм · m = {num(order_at(self.hover, lam, d, n, f), 7)}"
                    f" · I = {num(bright, 3)}")
            pill(p, 4, p.fontMetrics().height() + 14, text, dark, "#5BE0CD")

    def mouseMoveEvent(self, event):
        if self.data is None:
            return
        size, left, top = self.place()
        pos = event_pos(event)
        dist = math.hypot(pos.x() - left - size / 2, pos.y() - top - size / 2)
        self.hover = dist / (size / 2) * self.data[2] if dist <= size / 2 else None
        self.hovered.emit(None if self.hover is None else self.hover * 1e3)
        self.update()

    def leaveEvent(self, event):
        self.hover = None
        self.hovered.emit(None)
        self.update()


class ToggleSwitch(QtWidgets.QCheckBox):
    """Переключатель-«тумблер» вместо обычной галочки."""

    def __init__(self, text, text_color=None):
        super().__init__(text)
        self.text_color = text_color               # None — цвет текста из темы

    def sizeHint(self):
        fm = self.fontMetrics()
        return QSize(40 + fm.horizontalAdvance(self.text()), max(22, fm.height() + 4))

    def hitButton(self, pos):
        return self.rect().contains(pos)           # щёлкать можно и по подписи

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
    """Заголовок карточки мелкими заглавными буквами с разрядкой."""
    label = QtWidgets.QLabel(text.upper())
    label.setObjectName("cardTitle")
    font = QFont(label.font())
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
    label.setFont(font)
    return label


def make_card(title=None, name="card"):
    """Карточка со скруглёнными углами и заголовком."""
    frame = QtWidgets.QFrame()
    frame.setObjectName(name)
    layout = QtWidgets.QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 14)
    layout.setSpacing(6)
    if title:
        layout.addWidget(card_title(title))
    return frame, layout


def polish(widget, kind):
    """Сменить вид подложки (свойство kind в таблице стилей) и применить его сразу."""
    widget.setProperty("kind", kind)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
