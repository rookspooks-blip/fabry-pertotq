"""Оформление: тёмная и светлая темы, цвет света, значки.

Все виджеты берут цвета из общего объекта THEME во время рисования, поэтому
смена темы — это смена палитры, таблицы стилей и перерисовка окна.
"""

import math

from .qt import QBrush, QColor, QIcon, QImage, QPainter, QPalette, QPen, QPixmap, QPointF, QRadialGradient, QRectF, Qt

# Бирюзовый и оранжевый — фирменные цвета СЭЛФ. Для каждой темы свой оттенок,
# чтобы цвета одинаково хорошо читались на тёмном и на светлом фоне.
DARK = {
    "name": "dark",
    "bg": "#0A0F16",         # фон окна
    "surface": "#111923",    # карточки
    "raised": "#172230",     # поля ввода, наведение
    "border": "#1F2B3A",     # рамки карточек
    "line": "#2A3A4E",       # рамки полей, дорожка ползунка
    "text": "#E7EDF4",       # основной текст
    "muted": "#8795A8",      # подписи, пределы
    "faint": "#5B6A7D",      # совсем второстепенное
    "grid": "#18222F",       # сетка графиков
    "axis": "#2E3D50",       # оси графиков
    "accent": "#35D0BA",     # бирюзовый
    "accent_hover": "#5BE0CD",
    "accent_text": "#04211C",
    "orange": "#FFA54A",     # измерения на графиках
    "ok": ("#0F2E29", "#5EE3C9", "#1D5A50"),     # фон, текст и рамка подложки «различимы»
    "bad": ("#33161A", "#FF8A8A", "#6A2A31"),
    "warn": ("#332812", "#FFC56B", "#6A5020"),
    "info": ("#152131", "#A9B8CB", "#24344A"),
    "glow": True,            # кривые на графиках светятся
}
LIGHT = {
    "name": "light",
    "bg": "#EEF2F6",
    "surface": "#FFFFFF",
    "raised": "#F3F6F9",
    "border": "#DEE4EB",
    "line": "#CCD5DF",
    "text": "#15202B",
    "muted": "#627286",
    "faint": "#94A1B2",
    "grid": "#EDF1F5",
    "axis": "#C5CFDA",
    "accent": "#11A08D",
    "accent_hover": "#0C8A79",
    "accent_text": "#FFFFFF",
    "orange": "#E3700F",
    "ok": ("#E1F5F0", "#0B6B5C", "#B5E4D9"),
    "bad": ("#FCE9E7", "#A2291F", "#F2C3BE"),
    "warn": ("#FFF4DE", "#8A5A00", "#F1DAA6"),
    "info": ("#EDF1F5", "#43505F", "#DEE4EB"),
    "glow": False,
}
SCREEN_BG = "#05080C"    # экран с кольцами тёмный в обеих темах — кольца видны как в опыте
FONTS = ["Segoe UI", "SF Pro Text", ".AppleSystemUIFont", "Helvetica Neue",
         "Inter", "Ubuntu", "Cantarell", "Noto Sans", "DejaVu Sans"]


class Theme:
    """Текущая палитра. Виджеты берут цвета отсюда во время рисования, поэтому
    смена темы — это смена палитры, таблицы стилей и перерисовка окна."""

    def __init__(self):
        self.p = DARK

    def set(self, name):
        self.p = LIGHT if name == "light" else DARK

    @property
    def name(self):
        return self.p["name"]

    @property
    def dark(self):
        return self.p["name"] == "dark"

    def __getitem__(self, key):
        return self.p[key]

    def color(self, key, alpha=None):
        c = QColor(self.p[key])
        if alpha is not None:
            c.setAlpha(alpha)
        return c


THEME = Theme()


def stylesheet():
    """Оформление всех элементов окна (язык стилей Qt похож на CSS веб-страниц)."""
    p = THEME.p
    return f"""
QWidget {{ color: {p['text']}; font-size: 13px; }}
QMainWindow, QScrollArea, QWidget#page, QWidget#side {{ background: {p['bg']}; }}
QLabel {{ background: transparent; }}
QLabel#appTitle {{ font-size: 17px; font-weight: 700; }}
QLabel#appSub, QLabel#hint {{ color: {p['muted']}; font-size: 12px; }}
QLabel#h2 {{ font-size: 16px; font-weight: 700; }}
QLabel#cardTitle {{ font-size: 11px; font-weight: 700; color: {p['muted']}; }}
QLabel#limits {{ color: {p['faint']}; font-size: 11px; }}
QLabel#secret {{ background: {p['raised']}; border: 1px dashed {p['line']}; border-radius: 7px; padding: 3px 8px;
                color: {p['muted']}; font-style: italic; }}
QLabel#tileCaption {{ color: {p['muted']}; font-size: 12px; }}
QLabel#tileValue {{ font-size: 21px; font-weight: 700; }}
QLabel#tileNote {{ color: {p['muted']}; font-size: 11px; }}
QLabel#badge {{ border-radius: 7px; padding: 0px 4px; font-size: 10px; font-weight: 600; }}
QLabel#badge[kind="ok"] {{ background: {p['ok'][0]}; color: {p['ok'][1]}; }}
QLabel#badge[kind="warn"] {{ background: {p['warn'][0]}; color: {p['warn'][1]}; }}
QLabel#badge[kind="bad"] {{ background: {p['bad'][0]}; color: {p['bad'][1]}; }}
QLabel#badge[kind="none"] {{ background: transparent; color: {p['faint']}; }}
QLabel#verdict {{ border-radius: 12px; padding: 12px 14px; }}
QLabel#verdict[kind="ok"] {{ background: {p['ok'][0]}; color: {p['ok'][1]}; border: 1px solid {p['ok'][2]}; }}
QLabel#verdict[kind="bad"] {{ background: {p['bad'][0]}; color: {p['bad'][1]}; border: 1px solid {p['bad'][2]}; }}
QLabel#verdict[kind="info"] {{ background: {p['info'][0]}; color: {p['info'][1]}; border: 1px solid {p['info'][2]}; }}
QFrame#card, QFrame#tile {{ background: {p['surface']}; border: 1px solid {p['border']}; border-radius: 14px; }}
QFrame#screen {{ background: {SCREEN_BG}; border: 1px solid {p['border']}; border-radius: 14px; }}
QFrame#screen QLabel#cardTitle {{ color: #8795A8; }}
QPushButton {{ background: {p['raised']}; border: 1px solid {p['line']}; border-radius: 9px; padding: 6px 12px; }}
QPushButton:hover {{ border-color: {p['accent']}; }}
QPushButton:pressed {{ background: {p['border']}; }}
QPushButton#primary {{ background: {p['accent']}; color: {p['accent_text']}; border: none; font-weight: 700; }}
QPushButton#primary:hover {{ background: {p['accent_hover']}; }}
QPushButton#ghost {{ background: transparent; border: 1px solid transparent; color: {p['muted']}; padding: 6px 9px; }}
QPushButton#ghost:hover {{ background: {p['raised']}; border-color: {p['line']}; color: {p['text']}; }}
QFrame#screen QPushButton#ghost {{ color: #8795A8; }}
QFrame#screen QPushButton#ghost:hover {{ background: #111923; border-color: #2A3A4E; color: #E7EDF4; }}
QPushButton#preset {{ text-align: left; padding: 5px 10px; background: transparent; border: 1px solid {p['border']}; }}
QPushButton#preset:hover {{ background: {p['raised']}; border-color: {p['line']}; }}
QPushButton#preset:checked {{ background: {p['raised']}; border-color: {p['accent']}; font-weight: 600; }}
QSlider {{ min-height: 22px; background: transparent; }}
QSlider::groove:horizontal {{ height: 4px; background: {p['line']}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {p['accent']}; border-radius: 2px; }}
QSlider::handle:horizontal {{ width: 12px; height: 12px; margin: -6px 0; border-radius: 8px;
                             background: {p['surface']}; border: 2px solid {p['accent']}; }}
QSlider::handle:horizontal:hover {{ background: {p['accent']}; }}
QDoubleSpinBox {{ background: {p['raised']}; border: 1px solid {p['border']}; border-radius: 7px; padding: 3px 8px;
                 font-weight: 600; selection-background-color: {p['accent']}; selection-color: {p['accent_text']}; }}
QDoubleSpinBox:hover {{ border-color: {p['line']}; }}
QDoubleSpinBox:focus {{ border-color: {p['accent']}; }}
QTableWidget {{ background: {p['surface']}; border: 1px solid {p['border']}; border-radius: 14px;
               alternate-background-color: {p['raised']}; padding: 4px; }}
QTableWidget::item {{ padding: 3px 6px; border: none; font-size: 12px; }}
QHeaderView::section {{ background: {p['surface']}; color: {p['muted']}; border: none;
                       border-bottom: 1px solid {p['border']}; padding: 7px 6px; font-weight: 700; font-size: 12px; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {p['line']}; border-radius: 3px; min-height: 30px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {p['line']}; border-radius: 3px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QSplitter::handle {{ background: transparent; }}
QToolTip {{ background: {p['surface']}; color: {p['text']}; border: 1px solid {p['line']}; padding: 6px 8px; }}
QStatusBar {{ background: {p['bg']}; color: {p['muted']}; font-size: 12px; }}
QStatusBar::item {{ border: none; }}
QMessageBox {{ background: {p['surface']}; }}
QDialog {{ background: {p['surface']}; }}
QLabel#labBadge {{ background: {p['warn'][0]}; color: {p['warn'][1]}; border: 1px solid {p['warn'][2]};
                  border-radius: 9px; padding: 5px 10px; font-weight: 600; }}
QLabel#owner {{ font-weight: 700; }}
QLabel#journalResult {{ background: {p['surface']}; border: 1px solid {p['border']}; border-radius: 10px;
                       padding: 8px 10px; }}
QPushButton#segment {{ background: {p['raised']}; border: 1px solid {p['line']}; border-radius: 0; padding: 6px 10px;
                      color: {p['muted']}; }}
QPushButton#segment:checked {{ background: {p['accent']}; color: {p['accent_text']}; border-color: {p['accent']};
                              font-weight: 700; }}
QPushButton#segment:disabled {{ color: {p['faint']}; }}
QComboBox, QLineEdit, QSpinBox {{ background: {p['raised']}; border: 1px solid {p['border']}; border-radius: 7px;
                                 padding: 4px 8px; }}
QComboBox:focus, QLineEdit:focus, QSpinBox:focus {{ border-color: {p['accent']}; }}
QComboBox QAbstractItemView {{ background: {p['surface']}; border: 1px solid {p['line']};
                              selection-background-color: {p['raised']}; selection-color: {p['text']}; }}
"""


def qt_palette():
    """Палитра Qt под текущую тему — для стандартных окон (сохранение файла, сообщения)."""
    pal = QPalette()
    roles = QPalette.ColorRole
    for role, key in ((roles.Window, "surface"), (roles.WindowText, "text"), (roles.Base, "raised"),
                      (roles.AlternateBase, "surface"), (roles.Text, "text"), (roles.Button, "raised"),
                      (roles.ButtonText, "text"), (roles.Highlight, "accent"),
                      (roles.HighlightedText, "accent_text"), (roles.ToolTipBase, "surface"),
                      (roles.ToolTipText, "text"), (roles.PlaceholderText, "faint")):
        pal.setColor(role, THEME.color(key))
    return pal


def wavelength_rgb(nm):
    """Примерный цвет света с длиной волны nm (кусочно-линейная схема Брутона), 0…1."""
    if nm < 440:
        r, g, b = (440 - nm) / 60, 0.0, 1.0
    elif nm < 490:
        r, g, b = 0.0, (nm - 440) / 50, 1.0
    elif nm < 510:
        r, g, b = 0.0, 1.0, (510 - nm) / 20
    elif nm < 580:
        r, g, b = (nm - 510) / 70, 1.0, 0.0
    elif nm < 645:
        r, g, b = 1.0, (645 - nm) / 65, 0.0
    else:
        r, g, b = 1.0, 0.0, 0.0
    # у краёв видимого диапазона глаз чувствует свет хуже — цвет тусклее
    if nm < 420:
        k = 0.3 + 0.7 * (nm - 380) / 40
    elif nm > 700:
        k = 0.3 + 0.7 * (780 - nm) / 80
    else:
        k = 1.0
    return r * k, g * k, b * k


def line_color(nm):
    """Цвет кривой на графике: оттенок самого света, подогнанный под фон темы.

    На тёмном фоне тусклые фиолетовые и тёмно-красные цвета осветляются,
    на светлом — яркие жёлто-зелёные затемняются, чтобы кривая читалась.
    """
    r, g, b = wavelength_rgb(nm)
    k = max(r, g, b) or 1.0
    c = QColor.fromRgbF(r / k, g / k, b / k)       # тот же оттенок на полной яркости
    h, s, light = max(c.hslHueF(), 0.0), c.hslSaturationF(), c.lightnessF()
    if THEME.dark:
        light = max(light, 0.62)
    else:
        yellowish = max(0.0, 1 - abs(h - 0.17) / 0.12)    # жёлтый на белом виден хуже всего
        light = min(light, 0.42 - 0.12 * yellowish)
    return QColor.fromHslF(h, min(s, 0.95), light).name()


def spectrum_gradient():
    """Градиент радуги 380…780 нм для дорожки ползунка длины волны."""
    stops = []
    for i in range(21):
        t = i / 20
        r, g, b = wavelength_rgb(380 + 400 * t)
        stops.append(f"stop:{t:.2f} rgb({int(255 * r)},{int(255 * g)},{int(255 * b)})")
    return "qlineargradient(x1:0, y1:0, x2:1, y2:0, " + ", ".join(stops) + ")"


def dot_icon(colors, size=12):
    """Значок из одного-двух цветных кружков — цвета линий готового примера."""
    ratio = 3
    d = size * ratio
    pix = QPixmap(int(d * (1 + 0.65 * (len(colors) - 1))) + 2, d + 2)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    for i, color in enumerate(colors):
        p.setPen(QPen(THEME.color("surface"), ratio * 1.5))
        p.setBrush(QColor(color))
        p.drawEllipse(QRectF(i * 0.65 * d + 1, 1, d, d))
    p.end()
    pix.setDevicePixelRatio(ratio)
    return QIcon(pix)


def app_icon_image(size=512):
    """Значок программы: светящиеся интерференционные кольца на тёмном фоне."""
    img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    c = QPointF(size / 2, size / 2)
    grad = QRadialGradient(c, size * 0.5)
    grad.setColorAt(0.0, QColor("#15263A"))
    grad.setColorAt(1.0, QColor("#05080C"))
    p.setPen(QPen(QColor("#2A3A4E"), size * 0.012))
    p.setBrush(QBrush(grad))
    p.drawRoundedRect(QRectF(size * 0.04, size * 0.04, size * 0.92, size * 0.92), size * 0.22, size * 0.22)
    # радиусы как у настоящей картины колец (r ∝ √k), цвета от бирюзового к красному
    for k, color in enumerate(["#35D0BA", "#6FE0B0", "#C8E86A", "#FFD166", "#FF9F4A", "#FF5A5A"]):
        r = size * 0.075 + size * 0.13 * math.sqrt(k + 0.15)
        glow = QColor(color)
        glow.setAlpha(60)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(glow, size * 0.045))
        p.drawEllipse(c, r, r)
        p.setPen(QPen(QColor(color), size * 0.018))
        p.drawEllipse(c, r, r)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#E9FFFB"))
    p.drawEllipse(c, size * 0.045, size * 0.045)
    p.end()
    return img


def app_icon():
    icon = QIcon()
    for s in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(QPixmap.fromImage(app_icon_image(s * 4).scaled(
            s, s, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
    return icon
