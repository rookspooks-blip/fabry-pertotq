"""Главное окно: параметры слева, графики и кольца в середине, измерения справа."""

import csv

import numpy as np

from . import APP_TITLE, __version__
from .fmt import length, num, pick_unit, plain, rel_error, short, with_unit, div
from .physics import (C, airy, airy_range, curve_samples, measure_curve, measure_rings, phase,
                      ring_radii, seamless_shift, theory)
from .params import LINE2, PARAMS, PRESETS, TILES, ParamRow
from .qt import QAction, QBrush, QColor, QImage, QPainter, QPixmap, Qt, QtCore, QtGui, QtWidgets
from .theme import (SCREEN_BG, THEME, app_icon_image, dot_icon, line_color, qt_palette,
                    stylesheet, wavelength_rgb)
from .widgets import Curve, Plot, RingView, ToggleSwitch, card_title, make_card, polish

TWEEN_MS = 850         # сколько длится плавный переход к новому значению, мс


def ease(t):
    """Плавный разгон и торможение: 0 → 1 по S-образной кривой (ease-in-out cubic)."""
    return 4 * t ** 3 if t < 0.5 else 1 - (2 - 2 * t) ** 3 / 2


class MainWindow(QtWidgets.QMainWindow):
    """Сверху заголовок и кнопки, слева параметры, в середине графики и кольца,
    справа измерения."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.ready = False                         # пока окно строится, плавных переходов нет
        self.applying = False                      # выставляется готовый пример
        self.results = []                          # строки таблицы (нужны для CSV)
        self.curve = (np.zeros(0), np.zeros(0))    # последний график T(λ) (для CSV)
        self.radii = (np.zeros(0), np.zeros(0))    # радиусы колец: по картинке и по формуле
        self.shown = {}                            # значения, которые сейчас на картинке
        self.tweens = {}                           # плавные переходы: ключ → (от, до, начало, лог.)
        self.clock = QtCore.QElapsedTimer()
        self.clock.start()
        # настройки в INI-файле (на Windows — в папке %APPDATA%, а не в реестре)
        self.settings = QtCore.QSettings(QtCore.QSettings.Format.IniFormat, QtCore.QSettings.Scope.UserScope,
                                         "SELF-BMSTU", "FabryPerot")

        # Пересчёт не чаще раза в 15 мс: ползунок шлёт много сигналов подряд
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(15)
        self.timer.timeout.connect(self.recalc)
        # Кадры плавного перехода — примерно 60 в секунду
        self.tween_timer = QtCore.QTimer(self)
        self.tween_timer.setInterval(16)
        self.tween_timer.timeout.connect(self.tween_step)
        # Анимация микросдвига зеркала
        self.scan_timer = QtCore.QTimer(self)
        self.scan_timer.setInterval(30)
        self.scan_timer.timeout.connect(self.scan_step)

        page = QtWidgets.QWidget()
        page.setObjectName("page")
        column = QtWidgets.QVBoxLayout(page)
        column.setContentsMargins(14, 10, 14, 0)
        column.setSpacing(10)
        column.addLayout(self.build_header())
        splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.build_controls())
        splitter.addWidget(self.build_views())
        splitter.addWidget(self.build_results())
        splitter.setStretchFactor(1, 1)            # при растяжении окна растут графики
        splitter.setChildrenCollapsible(False)     # колонки нельзя «схлопнуть» до нуля
        splitter.setHandleWidth(12)                # промежутки между колонками
        column.addWidget(splitter, 1)
        self.setCentralWidget(page)
        self.build_actions()
        version = QtWidgets.QLabel(f"v{__version__} · Qt {QtCore.QT_VERSION_STR}")
        version.setObjectName("hint")
        self.statusBar().addPermanentWidget(version)
        self.statusBar().showMessage("Колёсико над графиком — масштаб, наведение на кольца — "
                                     "радиус и порядок кольца", 10000)

        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.92), int(screen.height() * 0.9))
        self.restore()
        self.ready = True

    # --- постройка окна ---
    def build_header(self):
        """Шапка: значок, название, кнопки сохранения, тема и справка."""
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(6)
        logo = QtWidgets.QLabel()
        pix = QPixmap.fromImage(app_icon_image(160))
        pix.setDevicePixelRatio(4)
        logo.setPixmap(pix)
        row.addWidget(logo)
        names = QtWidgets.QVBoxLayout()
        names.setSpacing(0)
        title = QtWidgets.QLabel(APP_TITLE)
        title.setObjectName("appTitle")
        sub = QtWidgets.QLabel("интерактивная модель · проект СЭЛФ, МГТУ им. Н. Э. Баумана")
        sub.setObjectName("appSub")
        names.addWidget(title)
        names.addWidget(sub)
        row.addSpacing(6)
        row.addLayout(names)
        row.addStretch()
        self.header_buttons = []
        for text, slot, tip in (("Снимок окна PNG", self.save_png, "Ctrl+S"),
                                ("Кольца PNG", self.save_rings, "Ctrl+Shift+S — картинка колец 2048 × 2048"),
                                ("Таблица CSV", self.save_csv, "Ctrl+E — для Excel"),
                                ("Копировать", self.copy_table, "Ctrl+Shift+C — таблица в буфер обмена")):
            button = QtWidgets.QPushButton(text)
            button.setObjectName("ghost")
            button.setToolTip(tip)
            button.clicked.connect(slot)
            row.addWidget(button)
        self.theme_button = QtWidgets.QPushButton()
        self.theme_button.setObjectName("ghost")
        self.theme_button.setToolTip("Ctrl+T")
        self.theme_button.clicked.connect(self.toggle_theme)
        row.addWidget(self.theme_button)
        help_button = QtWidgets.QPushButton("Справка")
        help_button.setObjectName("ghost")
        help_button.setToolTip("F1")
        help_button.clicked.connect(self.show_help)
        row.addWidget(help_button)
        return row

    def build_controls(self):
        """Левая колонка: готовые примеры, параметры, анимация, вторая линия."""
        panel = QtWidgets.QWidget()
        panel.setObjectName("side")
        column = QtWidgets.QVBoxLayout(panel)
        column.setContentsMargins(0, 0, 10, 10)
        column.setSpacing(10)

        box, layout = make_card("Готовые примеры")
        layout.setSpacing(4)
        self.preset_group = QtWidgets.QButtonGroup(self)
        self.preset_buttons = []
        for name, values, dlam in PRESETS:
            button = QtWidgets.QPushButton(name)
            button.setObjectName("preset")
            button.setCheckable(True)
            button.clicked.connect(lambda _, v=values, s=dlam: self.apply_preset(v, s))
            self.preset_group.addButton(button)
            self.preset_buttons.append((button, values, dlam))
            layout.addWidget(button)
        column.addWidget(box)

        box, layout = make_card("Параметры")
        grid = QtWidgets.QGridLayout()
        grid.setColumnStretch(0, 1)
        grid.setVerticalSpacing(2)
        grid.setHorizontalSpacing(10)
        self.params = {}
        for row, spec in enumerate(PARAMS):
            self.params[spec[0]] = ParamRow(grid, row, spec, self.param_changed)
        layout.addLayout(grid)
        hint = QtWidgets.QLabel("Ползунок меняет картину сразу, число из поля — плавно. "
                                "Поле понимает Enter, колёсико и стрелки ↑ ↓.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        layout.addSpacing(6)
        layout.addWidget(hint)
        column.addWidget(box)

        box, layout = make_card("Анимация")
        text = QtWidgets.QLabel("Зеркало медленно сдвигается: каждые λ/2 в центре рождается "
                                "новое кольцо, а пики бегут по графику.")
        text.setObjectName("hint")
        text.setWordWrap(True)
        layout.addWidget(text)
        self.scan_button = QtWidgets.QPushButton()
        self.scan_button.setObjectName("primary")
        self.scan_button.setToolTip("Пробел")
        self.scan_button.clicked.connect(self.toggle_scan)
        layout.addWidget(self.scan_button)
        column.addWidget(box)

        box, layout = make_card("Вторая спектральная линия")
        self.second = ToggleSwitch("Показать λ₂ = λ₁ + δλ")
        self.second.toggled.connect(self.second_toggled)
        layout.addWidget(self.second)
        grid = QtWidgets.QGridLayout()
        grid.setColumnStretch(0, 1)
        grid.setVerticalSpacing(2)
        self.params["dlam"] = ParamRow(grid, 0, LINE2, self.param_changed)
        layout.addLayout(grid)
        self.lam2_label = QtWidgets.QLabel()
        self.lam2_label.setObjectName("hint")
        layout.addWidget(self.lam2_label)
        column.addWidget(box)
        column.addStretch()

        scroll = QtWidgets.QScrollArea()           # на маленьком экране колонку можно прокрутить
        scroll.setWidget(panel)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(min(panel.sizeHint().width() + 26, 340))
        scroll.setMaximumWidth(panel.sizeHint().width() + 90)
        return scroll

    def build_views(self):
        """Середина: график пропускания, картина колец и её разрез по радиусу."""
        self.plot_t = Plot("Пропускание T(λ) — свет падает перпендикулярно", "λ − λ₁", "Пропускание T")
        self.plot_r = Plot("Разрез колец по радиусу", "r", "Яркость I / I₀")
        self.ring_view = RingView()
        # наведение на кольца показывает тот же радиус на разрезе — и наоборот
        self.ring_view.hovered.connect(self.plot_r.set_hover)
        self.plot_r.hovered.connect(self.ring_view.set_hover)

        screen, layout = make_card(None, "screen")
        layout.setContentsMargins(12, 10, 12, 12)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(card_title("Кольца на экране"))
        top.addStretch()
        self.glow_switch = ToggleSwitch("свечение", "#C9D3DF")
        self.glow_switch.setChecked(True)
        self.glow_switch.setToolTip("Мягкий ореол вокруг ярких колец, как на фотографии")
        self.glow_switch.toggled.connect(self.ring_view.set_glow)
        top.addWidget(self.glow_switch)
        layout.addLayout(top)
        layout.addWidget(self.ring_view, 1)

        bottom = QtWidgets.QSplitter(Qt.Orientation.Horizontal)
        bottom.addWidget(screen)
        bottom.addWidget(self.plot_r)
        bottom.setSizes([470, 530])                # доли ширины: кольца 47 %, разрез 53 %
        views = QtWidgets.QSplitter(Qt.Orientation.Vertical)
        views.addWidget(self.plot_t)
        views.addWidget(bottom)
        views.setSizes([420, 580])                 # доли высоты: график 42 %, кольца 58 %
        for splitter in (bottom, views):
            splitter.setChildrenCollapsible(False)
            splitter.setHandleWidth(12)
        return views

    def build_results(self):
        """Правая колонка: главные величины крупно, таблица «по графику / по формуле», вывод."""
        panel = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(panel)
        column.setContentsMargins(10, 0, 0, 10)
        column.setSpacing(10)

        # плитки 2 × 2: крупно — значение по графику, под ним — по формуле и расхождение
        tiles = QtWidgets.QGridLayout()
        tiles.setSpacing(10)
        self.tiles = []
        for i, (_, name) in enumerate(TILES):
            tile = QtWidgets.QFrame()
            tile.setObjectName("tile")
            box = QtWidgets.QVBoxLayout(tile)
            box.setContentsMargins(10, 9, 10, 9)
            box.setSpacing(2)
            caption, value = QtWidgets.QLabel(name), QtWidgets.QLabel()
            caption.setObjectName("tileCaption")
            value.setObjectName("tileValue")
            note, badge = QtWidgets.QLabel(), QtWidgets.QLabel()
            note.setObjectName("tileNote")
            badge.setObjectName("badge")
            badge.setToolTip("Расхождение измерения по графику и формулы")
            foot = QtWidgets.QHBoxLayout()         # формула и справа значок расхождения
            foot.setSpacing(4)
            foot.addWidget(note)
            foot.addStretch()
            foot.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)
            box.addWidget(caption)
            box.addWidget(value)
            box.addLayout(foot)
            tiles.addWidget(tile, i // 2, i % 2)
            self.tiles.append((value, note, badge))
        column.addLayout(tiles)

        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Величина", "По графику", "По формуле"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)   # строки через одну чуть другого цвета
        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.TextElideMode.ElideNone)   # длинные названия переносятся
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # высоту строк пересчитываем, только когда меняется ширина столбца (а не на каждом кадре)
        header.sectionResized.connect(lambda *args: self.table.resizeRowsToContents())
        column.addWidget(self.table, 1)
        note = QtWidgets.QLabel("«По графику» — программа сама меряет пики на кривых, «по формуле» — "
                                "теория. Формула видна при наведении мыши на строку.")
        note.setObjectName("hint")
        note.setWordWrap(True)
        column.addWidget(note)
        self.verdict = QtWidgets.QLabel()
        self.verdict.setObjectName("verdict")
        self.verdict.setWordWrap(True)
        column.addWidget(self.verdict)
        panel.setMinimumWidth(380)
        return panel

    def build_actions(self):
        """Сочетания клавиш."""
        for keys, slot in (("Ctrl+S", self.save_png), ("Ctrl+Shift+S", self.save_rings),
                           ("Ctrl+E", self.save_csv), ("Ctrl+Shift+C", self.copy_table),
                           ("Ctrl+T", self.toggle_theme), ("F1", self.show_help),
                           ("F11", self.toggle_fullscreen), ("Space", self.toggle_scan)):
            action = QAction(self)
            action.setShortcut(QtGui.QKeySequence(keys))
            action.triggered.connect(slot)
            self.addAction(action)

    # --- изменение параметров и плавные переходы ---
    def param_changed(self, key, smooth):
        """Параметр изменился: сразу (ползунок) или плавным переходом (число из поля)."""
        if key not in self.params:                 # строка параметра ещё строится
            return
        target = self.params[key].value()
        if key == "dd" and self.scan_timer.isActive():
            self.scan_timer.stop()                 # микросдвиг взяли в руки — анимация останавливается
            self.update_scan_button()
        if smooth and self.ready and key in self.shown:
            # переход начинается с того, что на картинке сейчас, — даже если
            # предыдущий переход ещё не закончился
            self.tweens[key] = (self.shown[key], target, self.clock.elapsed(), self.params[key].log)
            if not self.tween_timer.isActive():
                self.tween_timer.start()
        else:
            self.tweens.pop(key, None)
            self.shown[key] = target
            self.schedule()
        if not self.applying:                      # параметр меняли руками — пример больше не выбран
            self.check_preset(None)

    def tween_step(self):
        """Один кадр плавного перехода: значения на картинке чуть ближе к новым."""
        now = self.clock.elapsed()
        for key, (a, b, start, log) in list(self.tweens.items()):
            t = min((now - start) / TWEEN_MS, 1.0)
            e = ease(t)
            # на логарифмической шкале (δλ) переход тоже идёт по логарифму
            self.shown[key] = a * (b / a) ** e if log and a > 0 and b > 0 else a + (b - a) * e
            if t >= 1.0:
                self.shown[key] = b
                del self.tweens[key]
        if not self.tweens:
            self.tween_timer.stop()
        self.recalc()

    def schedule(self, *args):
        """Параметр изменился — пересчёт через 15 мс, если он ещё не запланирован."""
        if not self.timer.isActive():
            self.timer.start()

    def second_toggled(self, on):
        self.params["dlam"].slider.setEnabled(on)
        self.params["dlam"].spin.setEnabled(on)
        if not self.applying:
            self.check_preset(None)
        self.schedule()

    def check_preset(self, values):
        """Подсветить кнопку выбранного примера (None — снять подсветку со всех)."""
        self.preset_group.setExclusive(False)
        for button, v, _ in self.preset_buttons:
            button.setChecked(v is values)
        self.preset_group.setExclusive(True)

    def apply_preset(self, values, dlam):
        """Готовый пример: параметры плавно переходят к новым значениям."""
        self.applying = True
        for key, value in values.items():
            self.params[key].set(value, smooth=True)
        self.second.setChecked(dlam is not None)
        if dlam is not None:
            self.params["dlam"].set(dlam, smooth=True)
        self.applying = False
        self.check_preset(values)
        self.schedule()

    def toggle_scan(self):
        if self.scan_timer.isActive():
            self.scan_timer.stop()
            self.params["dd"].set(self.shown["dd"])     # поле и картина совпадают
        else:
            self.tweens.pop("dd", None)
            self.scan_timer.start()
        self.update_scan_button()

    def update_scan_button(self):
        self.scan_button.setText("■  Остановить" if self.scan_timer.isActive() else "▶  Двигать зеркало")

    def scan_step(self):
        """Кадр анимации микросдвига: примерно одно новое кольцо за 1,7 секунды."""
        lam, n = self.shown["lam"], self.shown["n"]
        end = seamless_shift(lam, n, self.params["dd"].hi)
        value = self.shown["dd"] + lam / (2 * n) / 56
        if value > end:
            value -= end                           # по кругу без скачка картинки
        self.shown["dd"] = value
        self.params["dd"].display(value)
        self.recalc()

    # --- главный расчёт ---
    def recalc(self):
        """Берём параметры, считаем физику, обновляем графики и таблицу."""
        self.timer.stop()
        v = self.shown
        lam = v["lam"] * 1e-9                      # нм → м
        d = v["d"] * 1e-3 + v["dd"] * 1e-9         # зазор вместе с микросдвигом, м
        R, n = v["R"], v["n"]
        A = min(v["A"], 1 - R)                     # зеркало не может отразить и поглотить больше 100 %
        f, half = v["f"] * 1e-3, v["screen"] * 1e-3
        two = self.second.isChecked()
        lam2 = lam + v["dlam"] * 1e-12
        th = theory(lam, d, n, R, f, A)
        F, fsr, tmax = th["F"], th["fsr"], th["tmax"]
        self.lam2_label.setText(f"λ₂ = {num(lam2 * 1e9, 9)} нм" if two else "Вторая линия выключена")

        # 1. Измерения по графику T(λ): по полтора Δλ слева и справа от λ₁,
        #    не меньше 30 точек на ширину пика (это десятки тысяч точек, не больше).
        x = lam + np.linspace(-1.5 * fsr, 1.5 * fsr, curve_samples(3 * fsr, th["width"], fsr))
        T = airy(phase(x, d, n), F, tmax)
        meas = measure_curve(x, T, lam)
        self.curve = (x, T)
        # а сам график рисуется по формуле — точно при любом масштабе (см. Plot.draw_curve)
        lo, hi = -1.5 * fsr, (lam2 - lam if two else 0.0) + 1.5 * fsr
        self.show_transmission(lam, lam2 if two else None, lo, hi, meas, d, n, F, tmax)

        # 2. Кольца: картинка считается по формуле прямо в виджете
        lines = [(lam, "λ₁")] + ([(lam2, "λ₂")] if two else [])
        caption = f"экран ⌀ {short(round(2 * v['screen'], 1))} мм · f = {short(round(v['f']))} мм"
        self.ring_view.show_data([(wl, wavelength_rgb(wl * 1e9)) for wl, _ in lines], half, caption,
                                 (d, n, f), F, tmax)

        # 3. Радиусы колец: по картинке (максимумы яркости) и по формуле
        measured, near = measure_rings(lam, d, n, f, half, F, tmax)   # «кольцо» в самом центре не считаем
        predicted = ring_radii(lam, d, n, f, half)
        predicted = predicted[predicted > near]
        self.radii = (measured, predicted)
        marks = [(rk * 1e3, THEME["muted"], label) for rk, label in zip(measured[:2], ("r₁", "r₂"))]
        # разрез: у каждой линии своя кривая своего цвета; две линии делят свет пополам
        share = len(lines)

        def ring_curve(wl, name):
            def sin_out(x_mm):
                r = x_mm * 1e-3
                return r / np.hypot(r, f)

            def value(x_mm):
                return airy(phase(wl, d, n, sin_out(x_mm)), F, tmax) / share

            def span(edges):
                lo_, hi_ = airy_range(phase(wl, d, n, sin_out(edges)), F, tmax)
                return lo_ / share, hi_ / share
            return Curve(value, span, line_color(wl * 1e9), name if two else "I / I₀")

        self.plot_r.show_data("Расстояние от центра r, мм", "мм", (0.0, v["screen"]), (0.0, 1.15),
                              [ring_curve(wl, name) for wl, name in lines], marks)

        self.fill_table(lam, th, meas, measured, predicted)
        kind, text = self.verdict_text(two, lam2 - lam, th)
        self.verdict.setText(text)
        if self.verdict.property("kind") != kind:
            polish(self.verdict, kind)             # цвет подложки: серый, зелёный или красный

    def show_transmission(self, lam, lam2, lo, hi, meas, d, n, F, tmax):
        """График T(λ): по оси — отступ от λ₁; метки линий и измерения Δλ и w."""
        unit, scale = ("нм", 1e-9) if hi - lo >= 2e-9 else ("пм", 1e-12)
        color = line_color(lam * 1e9)
        marks = [(0.0, color, "λ₁")]
        if lam2 is not None:
            marks.append(((lam2 - lam) / scale, line_color(lam2 * 1e9), "λ₂"))
        spans = []
        if meas["peaks"]:
            a, b = meas["peaks"]
            spans.append(((a - lam) / scale, (b - lam) / scale, 1.07, f"Δλ = {length(meas['fsr'])}"))
        if meas["half"]:
            a, b, level = meas["half"]
            spans.append(((a - lam) / scale, (b - lam) / scale, level, f"w = {length(meas['width'])}"))
        curve = Curve(lambda x: airy(phase(lam + x * scale, d, n), F, tmax),
                      lambda edges: airy_range(phase(lam + edges * scale, d, n), F, tmax), color, "T")
        self.plot_t.show_data(f"Отступ от λ₁: λ − λ₁, {unit}", unit, (lo / scale, hi / scale), (0.0, 1.15),
                              [curve], marks, spans)

    def fill_table(self, lam, th, meas, measured, predicted):
        """Таблица: что намерено по графикам и что дают формулы."""
        f_unit, f_scale = pick_unit(th["fsr"])
        w_unit, w_scale = pick_unit(th["width"] or th["fsr"])
        m_fsr, m_w = meas["fsr"], meas["width"]
        r1m, r2m = (list(measured[:2]) + [None, None])[:2]
        r1t, r2t = (list(predicted[:2]) + [None, None])[:2]
        dr2 = (r2m ** 2 - r1m ** 2) * 1e6 if r2m is not None else None
        top = float(self.curve[1].max()) if self.curve[1].size else None
        # название, по графику, по формуле, единица, подсказка с формулой
        self.results = [
            ("Порядок в центре m₀", None, th["m0"], "",
             "m₀ = 2nd/λ — сколько длин волн укладывается в путь туда и обратно"),
            ("Коэффициент F", None, th["F"], "", "F = 4R / (1 − R)²"),
            ("Пропускание на λ₁", None, th["T"], "",
             "T = Tmax / (1 + F·sin²(δ/2)), δ = 4πnd/λ"),
            ("Высота пиков Tmax", top, th["tmax"], "",
             "Tmax = (1 − R − A)² / (1 − R)² — без поглощения (A = 0) пики доходят до 1"),
            ("Расстояние между пиками Δλ", div(m_fsr, f_scale), th["fsr"] / f_scale, f_unit,
             "Δλ ≈ λ² / (2nd) — область свободной дисперсии"),
            ("То же по частоте Δν", div(m_fsr, lam ** 2 / C * 1e9), th["fsr_nu"] / 1e9, "ГГц",
             "Δν = c / (2nd)"),
            ("Ширина пика w", div(m_w, w_scale), div(th["width"], w_scale), w_unit,
             "Ширина пика на половине высоты: w = Δλ·δ½ / 2π, где δ½ = 4·arcsin(1/√F)"),
            ("Резкость Δλ / w", div(m_fsr, m_w), th["finesse"], "",
             "Резкость = Δλ / w = 2π / δ½ — во сколько раз пик уже расстояния между пиками"),
            ("Резкость ≈ π√R / (1 − R)", None, th["finesse_approx"], "",
             "π√R / (1 − R) — хорошо работает при R > 0,5"),
            ("Разрешающая способность", div(lam, m_w), th["resolving"], "",
             "A = λ / w = m₀ · резкость; две линии различимы, если δλ ≥ w"),
            ("Контраст Tmax / Tmin", meas["contrast"], th["contrast"], "", "Tmax / Tmin = 1 + F"),
            ("Колец на экране", len(measured), len(predicted), "",
             "Сколько светлых колец помещается от центра до края экрана"),
            ("Радиус кольца r₁", div(r1m, 1e-3), div(r1t, 1e-3), "мм",
             "Точно: 2d·√(n² − sin²θ) = mλ, r = f·tg θ"),
            ("Радиус кольца r₂", div(r2m, 1e-3), div(r2t, 1e-3), "мм",
             "Точно: 2d·√(n² − sin²θ) = mλ, r = f·tg θ"),
            ("r₂² − r₁²", dr2, th["dr2"] * 1e6, "мм²",
             "r₂² − r₁² ≈ f²nλ / d — одинакова для любых соседних колец (малые углы)"),
        ]
        self.table.setRowCount(len(self.results))
        for i, (name, got, expect, unit, tip) in enumerate(self.results):
            for j, text in enumerate((name, with_unit(got, unit), with_unit(expect, unit))):
                item = self.table.item(i, j)
                if item is None:
                    item = QtWidgets.QTableWidgetItem()
                    self.table.setItem(i, j, item)
                item.setText(text)
                item.setToolTip(tip)
                if j == 1:
                    item.setForeground(QBrush(THEME.color("text")))
                elif j == 2:
                    item.setForeground(QBrush(THEME.color("muted")))
        if not self.tweens and not self.scan_timer.isActive():
            self.table.resizeRowsToContents()      # высота строк — только когда картина стоит
        # плитки над таблицей: крупно — по графику, мелко — по формуле и расхождение
        rows = {name: (got, expect, unit) for name, got, expect, unit, _ in self.results}
        for (name, _), (value, note, badge) in zip(TILES, self.tiles):
            got, expect, unit = rows[name]
            value.setText(with_unit(got, unit))
            note.setText("теория " + with_unit(expect, unit))
            note.setToolTip("Значение по формуле")
            err = rel_error(got, expect)
            if err is None:
                badge.setText("")
                kind = "none"
            else:
                badge.setText("<0,01%" if err < 1e-4 else f"{num(100 * err, 2)}%")
                kind = "ok" if err < 0.01 else ("warn" if err < 0.05 else "bad")
            if badge.property("kind") != kind:
                polish(badge, kind)

    def verdict_text(self, two, dlam, th):
        """Вывод о второй линии: различает ли её прибор. Возвращает (вид, текст),
        вид — «info» (подсказка), «ok» (различимы) или «bad» (не различимы)."""
        w, fsr = th["width"], th["fsr"]
        if th["tmax"] <= 0:
            return "bad", "R + A ≥ 1: зеркала отражают и поглощают весь свет, через прибор ничего не проходит."
        if not two:
            return "info", ("Чтобы проверить разрешающую способность, включите вторую линию и уменьшайте δλ, "
                            "пока двойные кольца не сольются в одинарные.")
        if w is None:
            return "bad", ("Зеркала слишком слабые (R < 0,172): пропускание нигде не падает до половины, "
                           "отдельных пиков нет, и линии не разделить.")
        if dlam < w:
            return "bad", (f"δλ = {length(dlam)} меньше ширины пика w = {length(w)}: "
                           "линии сливаются, прибор их не различает.")
        if dlam > fsr - w:
            return "bad", (f"δλ = {length(dlam)} близко к Δλ = {length(fsr)} или больше: кольца λ₂ ложатся "
                           "на соседние кольца λ₁ (перекрытие порядков), линии путаются.")
        return "ok", (f"δλ = {length(dlam)} больше ширины пика w = {length(w)}: "
                      "линии различимы — кольца двойные.")

    # --- тема, справка, полноэкранный режим ---
    def apply_theme(self):
        app = QtWidgets.QApplication.instance()
        app.setPalette(qt_palette())
        app.setStyleSheet(stylesheet())
        self.theme_button.setText("Светлая тема" if THEME.dark else "Тёмная тема")
        for row in self.params.values():
            row.restyle()
        for button, values, dlam in self.preset_buttons:
            colors = [line_color(values["lam"])]
            if dlam is not None:
                colors.append(line_color(values["lam"] + dlam * 1e-3))
            button.setIcon(dot_icon(colors))
        for label in (self.verdict,) + tuple(badge for _, _, badge in self.tiles):
            polish(label, label.property("kind") or "none")
        if self.ready:
            self.recalc()                          # цвета кривых зависят от темы

    def toggle_theme(self):
        THEME.set("light" if THEME.dark else "dark")
        self.apply_theme()

    def toggle_fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def show_help(self):
        QtWidgets.QMessageBox.information(self, "Справка", (
            f"{APP_TITLE}, версия {__version__}\n\n"
            "Как пользоваться\n"
            "• Слева задайте параметры: ползунок меняет картину сразу, число в поле "
            "(Enter, колёсико, стрелки ↑ ↓) — плавным переходом.\n"
            "• Готовые примеры переключаются плавно — видно, как меняется картина.\n"
            "• Наведите мышь на график — появятся значения под курсором. Колёсико — масштаб, "
            "перетаскивание — сдвиг, двойной щелчок — весь график.\n"
            "• Наведите мышь на кольца — радиус, порядок интерференции m и яркость; "
            "тот же радиус отмечается на разрезе.\n"
            "• Справа — измерения по графикам и значения по формулам; значок показывает расхождение.\n\n"
            "Клавиши\n"
            "Ctrl+S — снимок окна PNG    Ctrl+Shift+S — кольца PNG 2048 × 2048\n"
            "Ctrl+E — таблица CSV    Ctrl+Shift+C — копировать таблицу\n"
            "Пробел — анимация зеркала    Ctrl+T — тема    F11 — во весь экран"))

    # --- сохранение ---
    def save_png(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить снимок окна", "fabry-perot.png",
                                                        "Картинка PNG (*.png)")
        if path:
            self.write_png(path)

    def write_png(self, path):
        """Снимок всего окна: параметры, графики, кольца и таблица."""
        if not path.lower().endswith(".png"):
            path += ".png"
        if self.centralWidget().grab().save(path, "PNG"):
            self.statusBar().showMessage(f"Картинка сохранена: {path}", 6000)
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить файл:\n{path}")

    def save_rings(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить картину колец", "rings.png",
                                                        "Картинка PNG (*.png)")
        if path:
            self.write_rings(path)

    def write_rings(self, path, side=2048):
        """Картина колец крупно, для отчёта: side × side пикселей на тёмном фоне."""
        if not path.lower().endswith(".png"):
            path += ".png"
        image = QImage(side, side, QImage.Format.Format_ARGB32)
        image.fill(QColor(SCREEN_BG))
        p = QPainter(image)
        p.drawImage(0, 0, self.ring_view.make_image(side))
        p.end()
        if image.save(path, "PNG"):
            self.statusBar().showMessage(f"Кольца сохранены: {path}", 6000)
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить файл:\n{path}")

    def save_csv(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Сохранить таблицу", "fabry-perot.csv",
                                                        "Таблица CSV (*.csv)")
        if path:
            self.write_csv(path)

    def write_csv(self, path):
        """Таблица для Excel: параметры, измерения, радиусы колец и точки графика T(λ)."""
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            # utf-8-sig и «;» — чтобы русский Excel сразу открыл файл без «кракозябр»
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                out = csv.writer(file, delimiter=";")
                out.writerow(["Параметр", "Значение", "Единица"])
                for row in self.params.values():
                    out.writerow([row.name, plain(self.shown[row.key]), row.unit])
                out.writerow(["Вторая линия", "включена" if self.second.isChecked() else "выключена"])
                out.writerow([])
                out.writerow(["Величина", "По графику", "По формуле", "Единица"])
                for name, got, expect, unit, _ in self.results:
                    out.writerow([name, plain(got), plain(expect), unit])
                out.writerow([])
                out.writerow(["Кольцо №", "r по картинке, мм", "r по формуле, мм"])
                measured, predicted = self.radii
                for k in range(max(len(measured), len(predicted))):
                    got = measured[k] * 1e3 if k < len(measured) else None
                    expect = predicted[k] * 1e3 if k < len(predicted) else None
                    out.writerow([k + 1, plain(got), plain(expect)])
                out.writerow([])
                out.writerow(["λ, нм", "Пропускание T"])
                x, T = self.curve
                step = max(1, len(x) // 20000)     # не больше примерно 20 000 строк
                for a, b in zip(x[::step], T[::step]):
                    out.writerow([f"{a * 1e9:.6f}".replace(".", ","), plain(b)])
        except OSError as error:
            QtWidgets.QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить файл:\n{error}")
            return
        self.statusBar().showMessage(f"Таблица сохранена: {path}", 6000)

    def copy_table(self):
        """Таблица в буфер обмена через табуляцию — вставляется в Excel и Word как таблица."""
        lines = ["Величина\tПо графику\tПо формуле"]
        for name, got, expect, unit, _ in self.results:
            lines.append(f"{name}\t{with_unit(got, unit)}\t{with_unit(expect, unit)}")
        QtWidgets.QApplication.clipboard().setText("\n".join(lines))
        self.statusBar().showMessage("Таблица скопирована в буфер обмена", 4000)

    # --- настройки между запусками ---
    def restore(self):
        """Вернуть параметры, тему и размер окна с прошлого запуска (или первый пример)."""
        s = self.settings
        THEME.set(s.value("theme", "dark"))
        self.apply_theme()
        self.glow_switch.setChecked(s.value("glow", True, type=bool))
        saved = s.value("params/lam") is not None
        if saved:
            for key, row in self.params.items():
                try:
                    row.set(min(max(float(s.value("params/" + key, row.value())), row.lo), row.hi))
                except (TypeError, ValueError):
                    pass
            self.second.setChecked(s.value("second", False, type=bool))
        else:
            name, values, dlam = PRESETS[0]
            for key, value in values.items():
                self.params[key].set(value)
            self.second.setChecked(dlam is not None)
            self.check_preset(values)
        self.second_toggled(self.second.isChecked())
        for key, row in self.params.items():
            self.shown[key] = row.value()
        geometry = s.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        self.update_scan_button()
        self.recalc()

    def closeEvent(self, event):
        s = self.settings
        s.setValue("theme", THEME.name)
        s.setValue("glow", self.glow_switch.isChecked())
        s.setValue("second", self.second.isChecked())
        for key, row in self.params.items():
            s.setValue("params/" + key, row.value())
        s.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)
