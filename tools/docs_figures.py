import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fabry_perot import physics as ph

INK = "#1b1f24"
GRAY = "#7a838c"
LIGHT = "#c9d0d6"
ACCENT = "#0f8f7e"
ORANGE = "#d9660b"
FONT = "font-family:'Liberation Serif','Times New Roman',serif"


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=13, anchor="middle", italic=False, color=INK, weight="normal", extra=""):
    style = f"{FONT};font-size:{size}px;font-weight:{weight}" + (";font-style:italic" if italic else "")
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" fill="{color}" style="{style}" {extra}>'
            f"{s}</text>")


def line(x1, y1, x2, y2, color=INK, width=1.2, dash=None, extra=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
            f'stroke-width="{width}"{d} {extra}/>')


def arrow_defs():
    return ('<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1b1f24"/></marker>'
            '<marker id="arg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#0f8f7e"/></marker></defs>')


def svg(width, height, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" '
            f'height="{height}">{arrow_defs()}{body}</svg>')


def polyline(xs, ys, color=INK, width=1.6, dash=None, fill="none"):
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in zip(xs, ys))
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<polyline points="{pts}" fill="{fill}" stroke="{color}" stroke-width="{width}"{d} stroke-linejoin="round"/>'


class Axes:
    def __init__(self, x, y, w, h, xlim, ylim):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.xlim, self.ylim = xlim, ylim

    def X(self, v):
        return self.x + (np.asarray(v) - self.xlim[0]) / (self.xlim[1] - self.xlim[0]) * self.w

    def Y(self, v):
        return self.y + self.h - (np.asarray(v) - self.ylim[0]) / (self.ylim[1] - self.ylim[0]) * self.h

    def frame(self, xticks=(), yticks=(), xlabel="", ylabel="", grid=True):
        out = []
        for v, label in xticks:
            X = float(self.X(v))
            if grid:
                out.append(line(X, self.y, X, self.y + self.h, LIGHT, 0.6))
            out.append(line(X, self.y + self.h, X, self.y + self.h + 4, INK, 1))
            out.append(text(X, self.y + self.h + 18, label, 12))
        for v, label in yticks:
            Y = float(self.Y(v))
            if grid:
                out.append(line(self.x, Y, self.x + self.w, Y, LIGHT, 0.6))
            out.append(line(self.x - 4, Y, self.x, Y, INK, 1))
            out.append(text(self.x - 8, Y + 4, label, 12, "end"))
        out.append(line(self.x, self.y + self.h, self.x + self.w + 8, self.y + self.h, INK, 1.2,
                        extra='marker-end="url(#ar)"'))
        out.append(line(self.x, self.y + self.h, self.x, self.y - 8, INK, 1.2, extra='marker-end="url(#ar)"'))
        if xlabel:
            out.append(text(self.x + self.w + 4, self.y + self.h + 34, xlabel, 14, "end", italic=True))
        if ylabel:
            out.append(text(self.x + 6, self.y - 12, ylabel, 14, "start", italic=True))
        return "".join(out)

    def curve(self, xs, ys, **kw):
        return polyline(self.X(xs), self.Y(ys), **kw)


def num(v, digits=2):
    s = f"{v:.{digits}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",").replace("-", "−")


def scheme():
    W, H = 760, 330
    b = []
    b.append('<rect x="30" y="80" width="18" height="170" rx="4" fill="#fde7c7" stroke="#b86b12"/>')
    b.append(text(39, 272, "S", 15, italic=True))
    b.append('<rect x="90" y="80" width="6" height="170" fill="#e8ecef" stroke="#7a838c"/>')
    b.append(text(93, 272, "Р", 13))
    px1, px2 = 250, 330
    for px, side in ((px1, 1), (px2, -1)):
        b.append(f'<rect x="{px - (22 if side == 1 else 0)}" y="60" width="22" height="210" fill="#e3f1ef" '
                 f'stroke="#5b8f88"/>')
        b.append(line(px, 60, px, 270, ACCENT, 3))
    b.append(line(px1, 290, px2, 290, INK, 1, extra='marker-start="url(#ar)" marker-end="url(#ar)"'))
    b.append(text((px1 + px2) / 2, 308, "d", 15, italic=True))
    b.append(text((px1 + px2) / 2, 48, "ИФП", 13))
    ang = math.radians(9)
    rays = []
    for k in range(4):
        y0 = 118 + 26 * k
        x_start = 96
        y_start = y0 - (px1 - 22 - x_start) * math.tan(ang)
        rays.append((x_start, y_start))
    lens_x, screen_x = 560, 720
    focus_y = 165 + (screen_x - lens_x) * math.tan(ang)
    for k, (xs, ys) in enumerate(rays):
        y_lens = ys + (lens_x - xs) * math.tan(ang)
        b.append(line(xs, ys, lens_x, y_lens, "#d9660b" if k == 1 else "#e3a15c", 1.3))
        b.append(line(lens_x, y_lens, screen_x, focus_y, "#d9660b" if k == 1 else "#e3a15c", 1.3))
    b.append(line(20, 165, 745, 165, GRAY, 0.8, dash="6 4"))
    b.append(f'<ellipse cx="{lens_x}" cy="165" rx="11" ry="110" fill="#eef4fb" stroke="#5a7896"/>')
    b.append(text(lens_x, 298, "Л", 14))
    b.append(line(lens_x, 312, screen_x, 312, INK, 1, extra='marker-start="url(#ar)" marker-end="url(#ar)"'))
    b.append(text((lens_x + screen_x) / 2, 326, "f", 15, italic=True))
    b.append(line(screen_x, 50, screen_x, 280, INK, 3))
    b.append(text(screen_x + 4, 42, "Э", 14))
    b.append(f'<circle cx="{screen_x}" cy="{focus_y:.1f}" r="3.5" fill="{ORANGE}"/>')
    b.append(text(screen_x + 10, focus_y + 5, "P", 14, "start", italic=True))
    b.append(line(screen_x + 18, 165, screen_x + 18, focus_y, INK, 1,
                  extra='marker-start="url(#ar)" marker-end="url(#ar)"'))
    b.append(text(screen_x + 24, (165 + focus_y) / 2 + 5, "r", 15, "start", italic=True))
    b.append(f'<path d="M {lens_x - 90} 165 A 90 90 0 0 1 {lens_x - 90 * math.cos(ang) + 0.5:.1f} '
             f'{165 - 90 * math.sin(ang) + 14.2:.1f}" fill="none" stroke="{INK}" stroke-width="1"/>')
    b.append(text(lens_x - 105, 158, "θ", 15, italic=True))
    return svg(W, H, "".join(b))


def beams():
    W, H = 640, 300
    b = []
    x1, x2 = 250, 370
    b.append(f'<rect x="{x1 - 26}" y="30" width="26" height="250" fill="#e3f1ef" stroke="#5b8f88"/>')
    b.append(f'<rect x="{x2}" y="30" width="26" height="250" fill="#e3f1ef" stroke="#5b8f88"/>')
    b.append(line(x1, 30, x1, 280, ACCENT, 3))
    b.append(line(x2, 30, x2, 280, ACCENT, 3))
    ang = math.radians(13)
    dy = (x2 - x1) * math.tan(ang)
    y = 50.0
    b.append(line(60, y - (x1 - 60) * math.tan(ang), x1, y, INK, 1.6, extra='marker-end="url(#ar)"'))
    b.append(text(70, 34, "E₀", 15, "start", italic=True))
    xs, ys = [x1], [y]
    right = True
    labels = ["t²E₀", "t²r²E₀e<tspan dy='-6' font-size='10'>iδ</tspan>",
              "t²r⁴E₀e<tspan dy='-6' font-size='10'>2iδ</tspan>", "…"]
    k = 0
    for step in range(7):
        nx = x2 if right else x1
        ny = ys[-1] + dy
        b.append(line(xs[-1], ys[-1], nx, ny, INK, 1.3))
        xs.append(nx)
        ys.append(ny)
        if right:
            b.append(line(nx, ny, nx + 170, ny + 170 * math.tan(ang), ORANGE, 1.4 if k < 3 else 1,
                          extra='marker-end="url(#ar)"' if k < 3 else ""))
            if k < 4:
                b.append(text(nx + 178, ny + 170 * math.tan(ang) + 5, labels[k], 14, "start", italic=True))
            k += 1
        right = not right
        if ny > 262:
            break
    b.append(line(x1, 292, x2, 292, INK, 1, extra='marker-start="url(#ar)" marker-end="url(#ar)"'))
    b.append(text((x1 + x2) / 2, 290 - 4, "d", 15, italic=True))
    b.append(text(x1 - 13, 20, "1", 13))
    b.append(text(x2 + 13, 20, "2", 13))
    b.append(line(x1, 50, x1 + 60, 50, GRAY, 0.8, dash="4 3"))
    b.append(text(x1 + 50, 66, "θ′", 14, italic=True))
    return svg(W, H, "".join(b))


def airy_family():
    W, H = 710, 300
    ax = Axes(70, 30, 500, 210, (-3 * math.pi, 3 * math.pi), (0, 1.1))
    b = [ax.frame([(v * math.pi, lab) for v, lab in
                   ((-2, "2π(m−1)"), (0, "2πm"), (2, "2π(m+1)"))],
                  [(0, "0"), (0.5, "0,5"), (1, "1")], "δ", "T")]
    d = np.linspace(-3 * math.pi, 3 * math.pi, 3000)
    for i, (R, dash, lab) in enumerate(((0.3, "7 4", "R = 0,3"), (0.7, "2 3", "R = 0,7"),
                                        (0.9, None, "R = 0,9"))):
        T = ph.airy(d, ph.coefficient_f(R))
        b.append(ax.curve(d, T, dash=dash, width=1.7))
        ly = 22 + 18 * i
        b.append(line(598, ly, 628, ly, INK, 1.7, dash))
        b.append(text(634, ly + 4, lab, 13, "start"))
    return svg(W, H, "".join(b))


def peak_measures():
    W, H = 640, 290
    R = 0.8
    F = ph.coefficient_f(R)
    ax = Axes(60, 36, 540, 200, (-0.35, 1.35), (0, 1.18))
    x = np.linspace(-0.35, 1.35, 4000)
    T = ph.airy(2 * math.pi * x, F)
    b = [ax.frame([(0, "λₘ"), (1, "λₘ₋₁")], [(0, "0"), (0.5, "0,5"), (1, "1")], "λ", "T")]
    b.append(ax.curve(x, T, width=1.8))
    half = 2 * math.asin(1 / math.sqrt(F)) / (2 * math.pi)
    y5 = float(ax.Y(0.5))
    b.append(line(float(ax.X(-half)), y5, float(ax.X(half)), y5, ORANGE, 1.5,
                  extra='marker-start="url(#ar)" marker-end="url(#ar)"'))
    b.append(line(float(ax.X(-0.3)), y5, float(ax.X(-half)), y5, GRAY, 0.8, dash="3 3"))
    b.append(text(float(ax.X(half)) + 8, y5 + 5, "w", 15, "start", italic=True, color=ORANGE))
    y11 = float(ax.Y(1.08))
    b.append(line(float(ax.X(0)), y11, float(ax.X(1)), y11, INK, 1.2,
                  extra='marker-start="url(#ar)" marker-end="url(#ar)"'))
    b.append(text(float(ax.X(0.5)), y11 - 6, "Δλ", 15, italic=True))
    for v in (0, 1):
        b.append(line(float(ax.X(v)), float(ax.Y(0)), float(ax.X(v)), y11, GRAY, 0.8, dash="3 3"))
    b.append(text(float(ax.X(0.5)), float(ax.Y(0.16)), "T<tspan dy='4' font-size='10'>min</tspan>"
                  "<tspan dy='-4'> = 1/(1 + F)</tspan>", 13))
    return svg(W, H, "".join(b))


def rings_linear():
    lam, d, n, f = 632.8e-9, 5e-3, 1.0, 0.2
    r = ph.ring_radii(lam, d, n, f, 0.01)[:6] * 1e3
    k = np.arange(1, len(r) + 1)
    r2 = r ** 2
    W, H = 520, 280
    ax = Axes(70, 30, 400, 200, (0, 7), (0, math.ceil(r2.max() / 5) * 5 + 5))
    yt = [(v, num(v, 0)) for v in range(0, int(ax.ylim[1]) + 1, 10)]
    b = [ax.frame([(v, str(v)) for v in range(1, 7)], yt, "k", "r², мм²")]
    slope, icpt = np.polyfit(k, r2, 1)
    kk = np.array([0, 6.8])
    b.append(ax.curve(kk, icpt + slope * kk, width=1.2, color=GRAY))
    for a, c in zip(k, r2):
        b.append(f'<circle cx="{float(ax.X(a)):.1f}" cy="{float(ax.Y(c)):.1f}" r="4" fill="{INK}"/>')
    k1, k2 = 2, 5
    y1, y2 = icpt + slope * k1, icpt + slope * k2
    b.append(line(float(ax.X(k1)), float(ax.Y(y1)), float(ax.X(k2)), float(ax.Y(y1)), ACCENT, 1.2, dash="4 3"))
    b.append(line(float(ax.X(k2)), float(ax.Y(y1)), float(ax.X(k2)), float(ax.Y(y2)), ACCENT, 1.2, dash="4 3"))
    b.append(text(float(ax.X(3.5)), float(ax.Y(y1)) + 17, "Δk", 13, italic=True, color=ACCENT))
    b.append(text(float(ax.X(k2)) + 6, float(ax.Y((y1 + y2) / 2)) + 4, "Δ(r²)", 13, "start", italic=True,
                  color=ACCENT))
    return svg(W, H, "".join(b))


def resolution():
    R = 0.9
    F = ph.coefficient_f(R)
    halfw = 2 * math.asin(1 / math.sqrt(F))
    W, H = 720, 200
    b = []
    for i, (mult, lab) in enumerate(((2.0, "δλ = 2w"), (1.0, "δλ = w"), (0.5, "δλ = w/2"))):
        ax = Axes(30 + i * 235, 20, 200, 130, (-4, 4), (0, 1.15))
        sep = mult * 2 * halfw
        x = np.linspace(-4, 4, 1500)
        scale = 4 * halfw
        T1 = ph.airy((x * scale / 4 + sep / 2), F)
        T2 = ph.airy((x * scale / 4 - sep / 2), F)
        b.append(ax.frame([], [], "", "", grid=False))
        b.append(ax.curve(x, T1, color=LIGHT, width=1.1, dash="4 3"))
        b.append(ax.curve(x, T2, color=LIGHT, width=1.1, dash="4 3"))
        b.append(ax.curve(x, (T1 + T2) / 2 * 1.0, width=1.8))
        b.append(text(float(ax.X(0)), 180, lab, 14, italic=False))
    return svg(W, H, "".join(b))


def shift_linear():
    lam = 632.8
    N = np.arange(1, 4)
    d0 = 60.0
    dd = d0 + N * lam / 2
    W, H = 460, 260
    ax = Axes(70, 30, 330, 180, (0, 3.6), (0, 1100))
    b = [ax.frame([(v, str(v)) for v in (1, 2, 3)], [(v, str(v)) for v in (0, 250, 500, 750, 1000)],
                  "N", "Δd, нм")]
    b.append(ax.curve(np.array([0, 3.4]), d0 + np.array([0, 3.4]) * lam / 2, color=GRAY, width=1.2))
    for a, c in zip(N, dd):
        b.append(f'<circle cx="{float(ax.X(a)):.1f}" cy="{float(ax.Y(c)):.1f}" r="4" fill="{INK}"/>')
    b.append(text(float(ax.X(0.05)), float(ax.Y(d0)) - 10, "Δd₀", 13, "start", italic=True))
    return svg(W, H, "".join(b))


def box(x, y, w, h, title, sub="", fill="#f3f6f8", stroke="#5b6b78"):
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}"/>'
    out += text(x + w / 2, y + (h / 2 + 5 if not sub else 22), title, 14, weight="bold")
    if sub:
        for i, s in enumerate(sub.split("\n")):
            out += text(x + w / 2, y + 40 + 15 * i, s, 11.5, color="#3d4852")
    return out


def arrow(x1, y1, x2, y2, color=INK, dash=None):
    return line(x1, y1, x2, y2, color, 1.3, dash, extra='marker-end="url(#ar)"')


def modules():
    W, H = 760, 380
    b = []
    b.append(box(300, 10, 160, 50, "run.py", "", "#ffffff"))
    b.append(box(300, 90, 160, 64, "app.py", "приложение Qt,\nшрифт, значок"))
    b.append(box(270, 184, 220, 80, "window.py", "главное окно, пересчёт,\nплавные переходы,\nсохранение",
                 "#e6f4f1", ACCENT))
    b.append(box(20, 184, 200, 80, "params.py", "параметры, примеры,\nползунок + поле"))
    b.append(box(540, 184, 200, 80, "widgets.py", "график, кольца,\nпереключатель, карточки"))
    b.append(box(20, 300, 200, 70, "theme.py", "темы, стили,\nцвет света, значок"))
    b.append(box(280, 300, 200, 70, "physics.py", "формулы и измерения\n(только numpy)", "#fff4e8", ORANGE))
    b.append(box(540, 300, 200, 70, "fmt.py", "числа по-русски,\nделения осей"))
    b.append(box(560, 90, 180, 64, "qt.py", "PyQt6 или PyQt5"))
    b.append(box(20, 90, 200, 64, "journal.py + lab.py", "журнал, варианты,\nметод наим. квадратов", "#fff8e1", "#b8860b"))
    b.append(arrow(270, 200, 180, 156))
    b.append(arrow(380, 60, 380, 88))
    b.append(arrow(380, 154, 380, 182))
    b.append(arrow(270, 224, 222, 224))
    b.append(arrow(490, 224, 538, 224))
    b.append(arrow(380, 264, 380, 298))
    b.append(arrow(320, 264, 200, 298))
    b.append(arrow(440, 264, 580, 298))
    b.append(arrow(640, 264, 640, 298))
    b.append(arrow(600, 264, 470, 312, dash="4 3"))
    b.append(arrow(120, 264, 120, 298))
    b.append(arrow(460, 122, 558, 122, GRAY, "4 3"))
    b.append(text(648, 175, "все, кто рисует, берут Qt отсюда", 11, color=GRAY))
    return svg(W, H, "".join(b))


def pipeline():
    W, H = 760, 250
    b = []
    xs = [10, 160, 310, 460, 610]
    names = [("Ползунок\nили поле", "ParamRow"), ("param_changed", "сразу / плавно"),
             ("shown", "значения\nна картинке"), ("recalc", "физика\nи измерения"),
             ("Экран", "графики, кольца,\nтаблица")]
    for x, (a, s) in zip(xs, names):
        b.append(box(x, 40, 140, 90, a.split("\n")[0], s if "\n" not in a else a.split("\n")[1] + "\n" + s))
    for i in range(4):
        b.append(arrow(xs[i] + 140, 85, xs[i + 1] - 2, 85))
    b.append(box(235, 170, 150, 60, "tween_step", "кадр перехода,\n60 раз в секунду", "#e6f4f1", ACCENT))
    b.append(arrow(260, 130, 290, 168, ACCENT))
    b.append(arrow(360, 168, 380, 132, ACCENT))
    b.append(box(430, 170, 150, 60, "timer 15 мс", "склейка частых\nсигналов ползунка"))
    b.append(arrow(505, 168, 520, 132))
    return svg(W, H, "".join(b))


def parabola():
    W, H = 520, 250
    ax = Axes(50, 20, 420, 190, (-1.6, 2.4), (0.3, 1.1))
    b = [ax.frame([(-1, "i−1"), (0, "i"), (1, "i+1")], [], "x", "y", grid=False)]
    x = np.linspace(-1.6, 2.4, 400)
    true = 1 / (1 + 3 * (x - 0.3) ** 2)
    b.append(ax.curve(x, true, color=LIGHT, width=2))
    pts = [(-1, 1 / (1 + 3 * 1.69)), (0, 1 / (1 + 3 * 0.09)), (1, 1 / (1 + 3 * 0.49))]
    (x0, y0), (x1, y1), (x2, y2) = pts
    A = (y0 - 2 * y1 + y2) / 2
    Bc = (y2 - y0) / 2
    xp = np.linspace(-1.3, 1.6, 200)
    b.append(ax.curve(xp, y1 + Bc * xp + A * xp ** 2, color=ACCENT, width=1.6, dash="5 3"))
    for a, c in pts:
        b.append(f'<circle cx="{float(ax.X(a)):.1f}" cy="{float(ax.Y(c)):.1f}" r="4.5" fill="{INK}"/>')
    shift = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)
    top = y1 - 0.25 * (y0 - y2) * shift
    b.append(f'<circle cx="{float(ax.X(shift)):.1f}" cy="{float(ax.Y(top)):.1f}" r="5" fill="none" '
             f'stroke="{ORANGE}" stroke-width="2"/>')
    b.append(line(float(ax.X(shift)), float(ax.Y(top)) + 6, float(ax.X(shift)), float(ax.Y(0.3)), ORANGE, 1,
                  dash="3 3"))
    b.append(text(float(ax.X(shift)) + 6, float(ax.Y(0.36)), "вершина", 12, "start", color=ORANGE))
    b.append(text(float(ax.X(1.7)), float(ax.Y(0.78)), "парабола", 12, "start", color=ACCENT))
    b.append(text(float(ax.X(1.3)), float(ax.Y(0.52)), "настоящая кривая", 12, "start", color=GRAY))
    return svg(W, H, "".join(b))


def columns():
    W, H = 700, 270
    R = 0.95
    F = ph.coefficient_f(R)
    ax = Axes(40, 20, 620, 200, (0, 1), (0, 1.1))
    b = [ax.frame([], [], "x", "T", grid=False)]
    ncol = 14
    edges = np.linspace(0, 1, ncol + 1)
    phase_of = (lambda x: 2 * math.pi * (x * 2.3 - 0.35))
    lo, hi = ph.airy_range(phase_of(edges), F)
    for i in range(ncol):
        X0, X1 = float(ax.X(edges[i])), float(ax.X(edges[i + 1]))
        b.append(f'<rect x="{X0:.1f}" y="{float(ax.Y(hi[i])):.1f}" width="{X1 - X0:.1f}" '
                 f'height="{float(ax.Y(lo[i])) - float(ax.Y(hi[i])):.1f}" fill="#d7efe9" stroke="{ACCENT}" '
                 f'stroke-width="0.8"/>')
        b.append(line(X0, float(ax.Y(0)), X0, float(ax.Y(1.1)), LIGHT, 0.6, dash="2 3"))
    x = np.linspace(0, 1, 3000)
    b.append(ax.curve(x, ph.airy(phase_of(x), F), width=1.3))
    b.append(text(float(ax.X(0.5)), 250, "столбцы пикселей: в каждом закрашено от наименьшего до наибольшего значения",
                  12, color=GRAY))
    return svg(W, H, "".join(b))


def antiderivative():
    W, H = 620, 320
    F = ph.coefficient_f(0.8)
    q = math.sqrt(1 + F)
    d = np.linspace(-math.pi * 0.999, 5 * math.pi * 0.999, 3000)
    k = np.floor(d / (2 * math.pi) + 0.5)
    G = (2 / q) * (np.pi * k + np.arctan(q * np.tan((d - 2 * np.pi * k) / 2)))
    ax = Axes(60, 20, 500, 120, (-math.pi, 5 * math.pi), (0, 1.1))
    b = [ax.frame([(0, "0"), (2 * math.pi, "2π"), (4 * math.pi, "4π")], [(1, "1")], "", "T(δ)", grid=False)]
    b.append(ax.curve(d, ph.airy(d, F), width=1.6))
    ax2 = Axes(60, 170, 500, 100, (-math.pi, 5 * math.pi), (G.min(), G.max()))
    b.append(ax2.frame([(0, "0"), (2 * math.pi, "2π"), (4 * math.pi, "4π")], [], "δ", "G(δ)", grid=False))
    b.append(ax2.curve(d, G, color=ACCENT, width=1.8))
    return svg(W, H, "".join(b))


def ease_curve():
    W, H = 420, 260
    ax = Axes(60, 20, 320, 190, (0, 1), (0, 1))
    b = [ax.frame([(0, "0"), (0.5, "0,5"), (1, "1")], [(0, "0"), (0.5, "0,5"), (1, "1")], "t", "e(t)")]
    t = np.linspace(0, 1, 300)
    e = np.where(t < 0.5, 4 * t ** 3, 1 - (2 - 2 * t) ** 3 / 2)
    b.append(ax.curve(t, t, color=LIGHT, width=1.2, dash="4 3"))
    b.append(ax.curve(t, e, color=ACCENT, width=2))
    b.append(text(float(ax.X(0.72)), float(ax.Y(0.55)), "равномерно", 12, "start", color=GRAY))
    b.append(text(float(ax.X(0.1)), float(ax.Y(0.2)) - 8, "разгон", 12, "start", color=ACCENT))
    b.append(text(float(ax.X(0.55)), float(ax.Y(0.86)), "торможение", 12, "end", color=ACCENT))
    return svg(W, H, "".join(b))


def layout():
    W, H = 720, 360
    b = ['<rect x="5" y="5" width="710" height="350" rx="10" fill="#f7f9fa" stroke="#5b6b78"/>']
    b.append(box(15, 15, 690, 40, "Шапка: значок, название, кнопки сохранения, тема, справка", "", "#ffffff"))
    b.append(box(15, 65, 170, 280, "Слева", "готовые примеры\nпараметры\nанимация\nвторая линия\n\n(прокрутка)"))
    b.append(box(195, 65, 330, 120, "График T(λ)", "Plot"))
    b.append(box(195, 195, 160, 150, "Кольца", "RingView"))
    b.append(box(365, 195, 160, 150, "Разрез", "Plot"))
    b.append(box(535, 65, 170, 280, "Справа", "4 плитки\nтаблица\n«график / формула»\nвывод о второй\nлинии"))
    b.append(text(360, 352, "", 11))
    return svg(W, H, "".join(b))


def raster():
    W, H = 720, 250
    b = []
    x0, y0, cell = 30, 20, 30
    rows, cols = 7, 12
    tops = [5.2, 4.8, 3.9, 1.3, 0.6, 0.4, 0.4, 0.7, 1.6, 3.6, 4.6, 5.0]
    bots = [5.3, 5.2, 4.8, 3.9, 1.3, 0.6, 0.7, 1.6, 3.6, 4.6, 5.0, 5.3]
    half = 0.45
    for c in range(cols):
        a, z = tops[c] - half, bots[c] + half
        for r in range(rows):
            cover = max(0.0, min(r + 1, z) - max(r, a))
            cover = min(cover, 1.0)
            shade = int(255 - cover * (255 - 60))
            color = f"rgb({shade},{min(255, shade + 30)},{min(255, shade + 20)})"
            b.append(f'<rect x="{x0 + c * cell}" y="{y0 + r * cell}" width="{cell}" height="{cell}" '
                     f'fill="{color}" stroke="#c9d0d6" stroke-width="0.6"/>')
        b.append(line(x0 + c * cell + cell / 2, y0 + tops[c] * cell, x0 + c * cell + cell / 2, y0 + bots[c] * cell,
                      ORANGE, 2))
    b.append(text(x0 + cols * cell + 12, y0 + 20, "оранжевое — от наименьшего", 12, "start", color=ORANGE))
    b.append(text(x0 + cols * cell + 12, y0 + 36, "до наибольшего значения", 12, "start", color=ORANGE))
    b.append(text(x0 + cols * cell + 12, y0 + 36 + 16, "в столбце", 12, "start", color=ORANGE))
    b.append(text(x0 + cols * cell + 12, y0 + 90, "цвет пикселя — какая его", 12, "start"))
    b.append(text(x0 + cols * cell + 12, y0 + 106, "доля попала в полоску", 12, "start"))
    b.append(text(x0 + cols * cell + 12, y0 + 122, "(плюс толщина линии)", 12, "start"))
    return svg(W, H, "".join(b))


def mmgrid():
    W, H = 170, 105
    b = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="white" stroke="#d98c5f" stroke-width="0.35"/>']
    for i in range(W + 1):
        width = 0.3 if i % 10 == 0 else (0.18 if i % 5 == 0 else 0.07)
        b.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{H}" stroke="#e0a07a" stroke-width="{width}"/>')
    for j in range(H + 1):
        width = 0.3 if j % 10 == 0 else (0.18 if j % 5 == 0 else 0.07)
        b.append(f'<line x1="0" y1="{j}" x2="{W}" y2="{j}" stroke="#e0a07a" stroke-width="{width}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}mm" height="{H}mm">'
            + "".join(b) + "</svg>")


FIGURES = {
    "scheme": scheme, "beams": beams, "airy_family": airy_family, "peak_measures": peak_measures,
    "rings_linear": rings_linear, "resolution": resolution, "shift_linear": shift_linear,
    "modules": modules, "pipeline": pipeline, "parabola": parabola, "columns": columns,
    "antiderivative": antiderivative, "ease": ease_curve, "layout": layout, "raster": raster, "mmgrid": mmgrid,
}
