"""Параметры модели, готовые примеры и строка параметра (ползунок + поле ввода)."""

import math

from .fmt import short
from .qt import Qt, QtWidgets
from .theme import THEME, spectrum_gradient

# ключ, название, единица, минимум, максимум, по умолчанию, знаков после запятой, шаг,
# подсказка, логарифмическая шкала ползунка
PARAMS = [
    ("lam", "Длина волны λ₁", "нм", 380.0, 780.0, 632.8, 1, 0.1,
     "Цвет света: 400 нм — фиолетовый, 530 нм — зелёный, 630 нм — красный.", False),
    ("d", "Зазор между зеркалами d", "мм", 0.1, 20.0, 5.0, 3, 0.01,
     "Расстояние между зеркалами. Больше d — пики ближе друг к другу, колец больше.", False),
    ("dd", "Микросдвиг зеркала Δd", "нм", 0.0, 1000.0, 0.0, 0, 1.0,
     "Тонкая подстройка зазора. Сдвиг на λ/2 рождает в центре одно новое кольцо.", False),
    ("R", "Отражение зеркал R", "", 0.01, 0.99, 0.9, 3, 0.01,
     "Доля света, которую отражает каждое зеркало. Ближе к 1 — пики и кольца тоньше.", False),
    ("A", "Поглощение зеркал A", "", 0.0, 0.1, 0.0, 3, 0.001,
     "Доля света, которую зеркало поглощает. Пики становятся ниже: Tmax = (1 − R − A)² / (1 − R)².",
     False),
    ("n", "Показатель преломления n", "", 1.0, 2.0, 1.0, 3, 0.01,
     "Среда между зеркалами: воздух ≈ 1, стекло ≈ 1,5.", False),
    ("f", "Фокус линзы f", "мм", 50.0, 500.0, 200.0, 0, 1.0,
     "Линза собирает свет на экран. Больше f — кольца крупнее.", False),
    ("screen", "Экран: от центра до края", "мм", 1.0, 100.0, 10.0, 1, 0.5,
     "Какую часть картины колец видно на экране.", False),
]
LINE2 = ("dlam", "Разность длин волн δλ", "пм", 0.01, 2000.0, 2.0, 2, 0.1,
         "λ₂ = λ₁ + δλ; 1 пм = 0,001 нм. Шкала ползунка логарифмическая.", True)

BASE = dict(dd=0.0, A=0.0, n=1.0, f=200.0, screen=10.0)
# название, параметры, δλ второй линии в пм (None — вторая линия выключена)
PRESETS = [
    ("Гелий-неоновый лазер · 632,8 нм", dict(BASE, lam=632.8, d=5.0, R=0.9), None),
    ("Натриевый дублет · 589,0 и 589,6 нм", dict(BASE, lam=589.0, d=0.2, R=0.9, screen=25.0), 600.0),
    ("Предел разрешения: δλ ≈ w", dict(BASE, lam=632.8, d=5.0, R=0.9), 1.5),
    ("Зелёный лазер, R = 0,98 · 532 нм", dict(BASE, lam=532.0, d=2.0, R=0.98), None),
    ("Стеклянный эталон, n = 1,5 · 546,1 нм", dict(BASE, lam=546.1, d=1.0, R=0.85, n=1.5, screen=15.0),
     None),
    ("Зеркала с потерями, A = 0,02", dict(BASE, lam=632.8, d=5.0, R=0.95, A=0.02), None),
    ("Плохие зеркала, R = 0,3", dict(BASE, lam=532.0, d=2.0, R=0.3), None),
]

# главные величины, которые показываются крупно над таблицей:
# (название строки таблицы, короткая подпись на плитке)
TILES = [("Расстояние между пиками Δλ", "Между пиками Δλ"), ("Ширина пика w", "Ширина пика w"),
         ("Резкость Δλ / w", "Резкость Δλ / w"), ("Разрешающая способность", "Разрешающая сила")]


class ParamRow:
    """Строка параметра: название, пределы, ползунок и поле ввода.

    Ползунок и поле связаны: двигаешь одно — меняется другое. Главное окно
    узнаёт, откуда пришло новое значение: от ползунка (картина меняется сразу)
    или из поля ввода — с клавиатуры, колёсиком, стрелками (картина плавно
    переплывает от старого значения к новому).
    """

    STEPS = 1000                                   # сколько положений у ползунка

    def __init__(self, grid, row, spec, on_change):
        self.key, self.name, self.unit, self.lo, self.hi, value, decimals, step, tip, self.log = spec
        self.on_change = on_change
        self.from_slider = False
        self.forced = None                         # плавно или сразу — если решает программа
        units = self.unit or "без единиц"
        label = QtWidgets.QLabel(self.name)
        limits = QtWidgets.QLabel(f"{short(self.lo)} … {short(self.hi)} {units}")   # допустимые значения
        limits.setObjectName("limits")
        limits.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, self.STEPS)
        self.spin = QtWidgets.QDoubleSpinBox()
        self.spin.setRange(self.lo, self.hi)
        self.spin.setDecimals(decimals)
        self.spin.setSingleStep(step)
        self.spin.setFixedWidth(112)
        self.spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        # новое число из поля приходит только после Enter или ухода из поля,
        # а не на каждую нажатую цифру — иначе картина «поплывёт» к 1, потом к 12…
        self.spin.setKeyboardTracking(False)
        # без стрелок: так поле аккуратнее; число меняется колёсиком мыши и клавишами ↑ ↓
        self.spin.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        if self.unit:
            self.spin.setSuffix(" " + self.unit)
        for widget in (label, limits, self.slider, self.spin):
            widget.setToolTip(tip)
        # каждый параметр занимает две строки сетки:
        # сверху название и пределы, снизу ползунок и поле ввода
        label.setContentsMargins(0, 8, 0, 0)
        grid.addWidget(label, 2 * row, 0)
        grid.addWidget(limits, 2 * row, 1)
        grid.addWidget(self.slider, 2 * row + 1, 0)
        grid.addWidget(self.spin, 2 * row + 1, 1, Qt.AlignmentFlag.AlignRight)
        self.slider.valueChanged.connect(self.slider_moved)
        self.spin.valueChanged.connect(self.spin_changed)
        self.set(value)

    def restyle(self):
        """У ползунка длины волны дорожка раскрашена радугой (зависит от темы)."""
        if self.key == "lam":
            self.slider.setStyleSheet(
                f"QSlider::groove:horizontal {{ height: 6px; border-radius: 3px; background: {spectrum_gradient()}; }}"
                "QSlider::sub-page:horizontal { background: transparent; }"
                "QSlider::handle:horizontal { width: 12px; height: 12px; margin: -5px 0; border-radius: 8px;"
                f" background: white; border: 2px solid {THEME['surface'] if THEME.dark else THEME['text']}; }}")

    def to_slider(self, value):
        """Значение → положение ползунка (для δλ шкала логарифмическая)."""
        if self.log:
            t = math.log(value / self.lo) / math.log(self.hi / self.lo)
        else:
            t = (value - self.lo) / (self.hi - self.lo)
        return round(t * self.STEPS)

    def from_slider_pos(self, pos):
        """Положение ползунка → значение."""
        t = pos / self.STEPS
        return self.lo * (self.hi / self.lo) ** t if self.log else self.lo + t * (self.hi - self.lo)

    def slider_moved(self, pos):
        self.from_slider = True                    # поле ввода не должно «дёргать» ползунок назад
        self.spin.setValue(self.from_slider_pos(pos))
        self.from_slider = False

    def spin_changed(self, value):
        if not self.from_slider:
            self.show_on_slider(value)
        if self.from_slider:
            smooth = False                         # ведут ползунок — меняем сразу
        elif self.forced is not None:
            smooth = self.forced
        else:
            smooth = True                          # ввели число — плавный переход
        self.on_change(self.key, smooth)

    def show_on_slider(self, value):
        self.slider.blockSignals(True)
        self.slider.setValue(self.to_slider(value))
        self.slider.blockSignals(False)

    def set(self, value, smooth=False):
        """Выставить значение из программы (готовый пример, сохранённые настройки)."""
        self.forced = smooth
        self.spin.setValue(value)
        self.forced = None
        # если значение не изменилось, поле не пришлёт сигнал — ставим ползунок сами
        self.show_on_slider(self.spin.value())

    def display(self, value):
        """Только показать значение, ничего не пересчитывая (анимация микросдвига)."""
        self.spin.blockSignals(True)
        self.spin.setValue(value)
        self.spin.blockSignals(False)
        self.show_on_slider(value)

    def value(self):
        return self.spin.value()
