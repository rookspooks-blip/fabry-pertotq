"""Журнал измерений: серии точек по заданиям, прямая по методу наименьших квадратов, итог с погрешностью.

Точки записываются правым щелчком по графику T(λ), по картине колец или разрезу,
а для серий «по параметру» — кнопкой «Записать». Журнал сохраняется между запусками.
"""

import json
import math

import numpy as np

from .fmt import num
from .lab import BY_KEY, SERIES, derived, fit_line, mean_with_error
from .qt import Qt, QtWidgets, Signal
from .theme import THEME
from .widgets import Curve, Plot, card_title


def pm(value, error, unit, digits=4):
    """Запись «значение ± погрешность единица» по-русски."""
    if error is None or not math.isfinite(error) or error == 0:
        return f"{num(value, digits)} {unit}".strip()
    return f"({num(value, digits)} ± {num(error, 2)}) {unit}".strip()


class Journal(QtWidgets.QWidget):
    """Журнал: выбор серии, таблица точек, график с прямой, результат."""

    changed = Signal()                             # данные изменились — окно сохранит журнал

    def __init__(self, context, notify):
        super().__init__()
        self.context = context                     # функция: текущие параметры окна (скрытые — None)
        self.notify = notify                       # функция: сообщение в строке состояния
        self.data = {s.key: [] for s in SERIES}
        self.extra = {}                            # подсказки варианта к сериям (d, f и т. п.)
        self.pending = None                        # первая точка пары (для Δλ и w)

        column = QtWidgets.QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(8)
        column.addWidget(card_title("Журнал измерений"))
        self.owner = QtWidgets.QLabel()            # кто выполняет лабораторную (видно и на снимке)
        self.owner.setObjectName("owner")
        self.owner.setWordWrap(True)
        column.addWidget(self.owner)
        self.combo = QtWidgets.QComboBox()
        # ширина списка не зависит от длины названий серий — окно помещается на экране 1366 точек
        self.combo.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.combo.setMinimumContentsLength(18)
        for s in SERIES:
            self.combo.addItem(s.title, s.key)
        self.combo.currentIndexChanged.connect(self.series_changed)
        column.addWidget(self.combo)
        self.hint = QtWidgets.QLabel()
        self.hint.setObjectName("hint")
        self.hint.setWordWrap(True)
        column.addWidget(self.hint)

        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        column.addWidget(self.table, 2)

        buttons = QtWidgets.QHBoxLayout()
        buttons.setSpacing(6)
        self.record_button = QtWidgets.QPushButton("Записать")
        self.record_button.setObjectName("primary")
        self.record_button.setToolTip("Записать текущее значение параметра (для серий «по параметру»)")
        self.record_button.clicked.connect(self.record_param)
        undo = QtWidgets.QPushButton("Удалить выбранную")
        undo.clicked.connect(self.delete_selected)
        clear = QtWidgets.QPushButton("Очистить")
        clear.clicked.connect(self.clear_series)
        for b in (self.record_button, undo, clear):
            buttons.addWidget(b)
        column.addLayout(buttons)

        self.plot = Plot("Точки серии и прямая МНК", "x", "y")
        self.plot.setMinimumSize(200, 190)
        column.addWidget(self.plot, 2)
        self.result = QtWidgets.QLabel()
        self.result.setObjectName("journalResult")
        self.result.setWordWrap(True)
        self.result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        column.addWidget(self.result)
        self.series_changed()

    # --- серии ---
    def series(self):
        return BY_KEY[self.combo.currentData()]

    def set_extra(self, extra):
        """Подсказки варианта: {ключ серии: текст}."""
        self.extra = dict(extra)
        self.series_changed()

    def select(self, key):
        index = self.combo.findData(key)
        if index >= 0:
            self.combo.setCurrentIndex(index)

    def series_changed(self, *args):
        self.pending = None
        s = self.series()
        text = s.hint + (" " + self.extra[s.key] if s.key in self.extra else "")
        self.hint.setText(text)
        self.record_button.setEnabled(s.kind == "param")
        self.refresh()

    # --- запись точек ---
    def add(self, x, y, note=""):
        ctx = self.context()
        self.data[self.series().key].append(
            {"x": float(x), "y": float(y), "note": note,
             "ctx": {k: ctx.get(k) for k in ("n", "d", "f", "R")}})
        self.refresh()
        self.changed.emit()
        self.notify(f"Записано в журнал: {self.series().ylabel.split(',')[0]} = {num(float(y), 5)}")

    def plot_pick(self, x, unit, y):
        """Правый щелчок по графику T(λ): x — отступ от λ₁ в единицах оси (нм или пм), y — показание T."""
        s = self.series()
        x_pm = x * 1000.0 if unit == "нм" else x
        if s.kind == "pair":
            if self.pending is None:
                self.pending = x_pm
                self.notify(f"Первая точка: {num(x_pm, 5)} пм. Щёлкните правой кнопкой по второй точке.")
                self.hint.setText(f"Первая точка: x₁ = {num(x_pm, 5)} пм — щёлкните вторую.")
                return
            first, self.pending = self.pending, None
            ctx = self.context()
            self.add(s.xfunc(ctx[s.xkey]), abs(x_pm - first),
                     f"x₁ = {num(first, 5)}, x₂ = {num(x_pm, 5)} пм")
            self.series_changed()
        elif s.key == "tmax":
            self.add(self.context()["R"], y, f"λ − λ₁ = {num(x_pm, 5)} пм")
        elif s.key == "free":
            self.add(x_pm, y, "график T(λ): x — отступ, пм")
        else:
            self.notify("Эта серия записывается " + ("щелчком по кольцам." if s.kind == "ring"
                                                     else "кнопкой «Записать»."))

    def ring_pick(self, r_mm, bright):
        """Правый щелчок по кольцам или разрезу: радиус, мм, и яркость."""
        s = self.series()
        if s.kind == "ring":
            k = len(self.data[s.key]) + 1
            self.add(k, r_mm ** 2, f"r = {num(r_mm, 5)} мм")
        elif s.key == "free":
            self.add(r_mm, bright, "кольца: x — радиус, мм")
        else:
            self.notify("Эта серия записывается " + ("щелчком по графику T(λ)." if s.kind in ("pair", "point")
                                                     else "кнопкой «Записать»."))

    def record_param(self):
        s = self.series()
        ctx = self.context()
        value = ctx.get(s.source)
        if value is None:
            self.notify("Эта величина скрыта — её нельзя записать.")
            return
        x = s.xfunc(ctx[s.xkey]) if s.xfunc else (ctx[s.xkey] if s.xkey else len(self.data[s.key]) + 1)
        self.add(x, value)

    def delete_selected(self):
        rows = self.data[self.series().key]
        selected = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        if not selected and rows:
            selected = [len(rows) - 1]
        for i in selected:
            if 0 <= i < len(rows):
                rows.pop(i)
        self.refresh()
        self.changed.emit()

    def clear_series(self):
        if not self.data[self.series().key]:
            return
        answer = QtWidgets.QMessageBox.question(self, "Очистить серию",
                                                f"Удалить все точки серии «{self.series().title}»?")
        if answer == QtWidgets.QMessageBox.StandardButton.Yes:
            self.data[self.series().key] = []
            self.refresh()
            self.changed.emit()

    # --- обработка ---
    def fit(self, key):
        s = BY_KEY[key]
        rows = self.data[key]
        if not s.fit or len(rows) < 2:
            return None
        return fit_line([r["x"] for r in rows], [r["y"] for r in rows], s.through_origin)

    def known_lambda(self):
        """Длина волны для расчётов: лучший результат серий (кольца, сдвиг, Δλ) или видимое λ."""
        best = None
        for key in ("rings", "shift", "fsr"):
            rows = self.data[key]
            fit = self.fit(key)
            if fit is None:
                continue
            res = derived(key, fit, rows[-1]["ctx"], None)
            if res and math.isfinite(res[1]):
                rel = (res[2] or 0) / res[1] if res[2] is not None and math.isfinite(res[2]) else 1.0
                if best is None or rel < best[2]:
                    best = (res[1], res[2], rel, key)
        if best:
            return best[0], best[1]
        lam = self.context().get("lam")
        return (lam, None) if lam else (None, None)

    def result_text(self, key):
        s = BY_KEY[key]
        rows = self.data[key]
        if not rows:
            return "Серия пуста."
        lines = []
        if s.fit:
            fit = self.fit(key)
            if fit is None:
                return "Нужно не меньше двух точек."
            if s.through_origin:
                lines.append("Прямая через начало координат y = b·x")
            else:
                lines.append("Прямая y = a + b·x")
                lines.append(f"a = {pm(fit['a'], fit['da'], '')}")
            lines.append(f"b = {pm(fit['b'], fit['db'], '')}  (n = {fit['n']}, t = {num(fit['t'], 3)})")
            res = derived(key, fit, rows[-1]["ctx"], None)
            if res:
                name, value, err, unit = res
                lines.append(f"<b>{name} = {pm(value, err, unit)}</b>")
            return "<br>".join(lines)
        lam, dlam_err = self.known_lambda()
        if key == "doublet":
            m, e = mean_with_error([r["y"] for r in rows])
            lines.append(f"d* = {pm(m, e, 'мм', 5)}  (n = {len(rows)})")
            if lam:
                n = rows[-1]["ctx"]["n"] or 1.0
                dl = (lam * 1e-9) ** 2 / (2 * n * m * 1e-3) * 1e12
                rel = math.hypot(2 * (dlam_err or 0) / lam, (e or 0) / m)
                lines.append(f"<b>δλ = λ²/(2nd*) = {pm(dl, dl * rel if rel else None, 'пм')}</b>  (λ = {num(lam, 5)} нм)")
            else:
                lines.append("Чтобы найти δλ, сначала определите λ (задания 2, 4 или 5).")
        elif key == "resolve":
            if lam:
                for r in rows:
                    lines.append(f"R = {num(r['x'], 3)}: δλmin = {num(r['y'], 4)} пм, "
                                 f"<b>A = λ/δλ = {num(lam * 1e3 / r['y'], 3)}</b>")
            else:
                lines.append("Чтобы найти A = λ/δλ, нужна λ (задания 2, 4 или 5).")
        elif key == "tmax":
            values = []
            for r in rows:
                if 0 < r["y"] <= 1 and r["x"] < 1:
                    a = (1 - r["x"]) * (1 - math.sqrt(r["y"]))
                    values.append(a)
                    lines.append(f"R = {num(r['x'], 3)}: Tmax = {num(r['y'], 3)} → A = {num(a, 3)}")
            if values:
                m, e = mean_with_error(values)
                lines.append(f"<b>A = (1 − R)(1 − √Tmax) = {pm(m, e, '')}</b>")
        else:
            lines.append(f"Точек: {len(rows)}")
        return "<br>".join(lines)

    def refresh(self):
        s = self.series()
        rows = self.data[s.key]
        self.table.setHorizontalHeaderLabels(["№", s.xlabel, s.ylabel, "примечание"])
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            x = r["x"]
            xs_text = str(int(x)) if float(x).is_integer() and abs(x) < 1e6 else num(x, 5)
            for j, text in enumerate((str(i + 1), xs_text, num(r["y"], 5), r.get("note", ""))):
                item = self.table.item(i, j)
                if item is None:
                    item = QtWidgets.QTableWidgetItem()
                    self.table.setItem(i, j, item)
                item.setText(text)
        self.result.setText(self.result_text(s.key))
        # график серии: точки и прямая МНК
        xs = [r["x"] for r in rows]
        ys = [r["y"] for r in rows]
        if xs:
            x0 = min(xs + ([0.0] if s.through_origin else []))
            x1 = max(xs)
            pad = (x1 - x0) * 0.1 or abs(x1) * 0.1 or 1.0
            y0 = min(ys + [0.0])
            y1 = max(ys) * 1.12 if max(ys) > 0 else 1.0
            xlim, ylim = (x0 - (0 if s.through_origin else pad), x1 + pad), (y0, y1 if y1 > y0 else y0 + 1)
        else:
            xlim, ylim = (0.0, 1.0), (0.0, 1.0)
        curves = []
        fit = self.fit(s.key)
        if fit is not None:
            a, b = fit["a"], fit["b"]

            def value(x, a=a, b=b):
                return a + b * np.asarray(x, dtype=float)

            def span(edges, a=a, b=b):
                v = a + b * edges
                return np.minimum(v[:-1], v[1:]), np.maximum(v[:-1], v[1:])
            curves.append(Curve(value, span, THEME["accent"], "МНК"))
        self.plot.xname = s.xlabel.split(",")[0]
        self.plot.ylabel = s.ylabel
        self.plot.show_data(s.xlabel, "", xlim, ylim, curves, points=list(zip(xs, ys)))

    # --- сохранение ---
    def to_json(self):
        return json.dumps(self.data, ensure_ascii=False)

    def load_json(self, text):
        try:
            data = json.loads(text)
        except (TypeError, ValueError):
            return
        for key in self.data:
            if isinstance(data.get(key), list):
                self.data[key] = [r for r in data[key] if isinstance(r, dict) and "x" in r and "y" in r]
        self.refresh()

    def clear_all(self):
        self.data = {s.key: [] for s in SERIES}
        self.refresh()
        self.changed.emit()

    def csv_rows(self):
        """Строки для CSV: все непустые серии с результатами (без HTML)."""
        out = []
        for s in SERIES:
            rows = self.data[s.key]
            if not rows:
                continue
            out.append([s.title])
            out.append(["№", s.xlabel, s.ylabel, "Примечание"])
            for i, r in enumerate(rows):
                out.append([i + 1, f"{r['x']:.6g}".replace(".", ","), f"{r['y']:.6g}".replace(".", ","),
                            r.get("note", "")])
            text = self.result_text(s.key).replace("<b>", "").replace("</b>", "")
            for line in text.split("<br>"):
                out.append(["", line])
            out.append([])
        return out
