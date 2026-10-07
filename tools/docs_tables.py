import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fabry_perot import lab
from fabry_perot import physics as ph

TASK2_D = (1.0, 2.0, 3.0, 5.0, 8.0, 12.0)
TASK3_R = (0.5, 0.7, 0.8, 0.9, 0.95, 0.98)
TASK6_R = (0.8, 0.9, 0.95)
TASK7_R = (0.9, 0.95)


def f(value, digits=4):
    if value is None or not math.isfinite(value):
        return "—"
    if value == 0:
        return "0"
    power = math.floor(math.log10(abs(value)))
    decimals = max(digits - 1 - power, 0)
    return f"{value:,.{decimals}f}".replace(",", "\u202f").replace(".", ",").replace("-", "−")


def peak_and_width(F, tmax=1.0):
    x = np.linspace(-np.pi, np.pi, 400001)
    T = ph.airy(x, F, tmax)
    top = T.max()
    idx = np.flatnonzero(T >= top / 2)
    return top, x[idx[-1]] - x[idx[0]]


def expected(code):
    v = lab.Variant(code)
    lam = v.lam * 1e-9
    out = {"v": v}
    out["fsr"] = [lam ** 2 / (2 * d * 1e-3) * 1e12 for d in TASK2_D]
    d5 = 5e-3
    fsr5 = lam ** 2 / (2 * d5) * 1e12
    widths = []
    for R in TASK3_R:
        F = ph.coefficient_f(R)
        tmax = ph.peak_transmission(R, v.A)
        top, wphase = peak_and_width(F, tmax)
        widths.append((wphase / (2 * np.pi) * fsr5, fsr5 / (wphase / (2 * np.pi) * fsr5), top))
    out["width"] = widths
    r = ph.ring_radii(lam, v.d_rings * 1e-3, 1.0, v.f_rings * 1e-3, 0.010)[:6] * 1e3
    out["rings"] = r
    out["slope"] = (v.f_rings * 1e-3) ** 2 * lam / (v.d_rings * 1e-3) * 1e6
    m0 = 2 * d5 / lam
    first = (math.ceil(m0) - m0) * lam / 2 * 1e9
    out["shift"] = [first + k * v.lam / 2 for k in range(3) if first + k * v.lam / 2 <= 1000]
    lam2 = lam + v.dlam * 1e-12
    out["dstar"] = lam * lam2 / (2 * (lam2 - lam)) * 1e3
    res = []
    for R in TASK6_R:
        F = ph.coefficient_f(R)
        fsr1 = lam ** 2 / (2 * 1e-3)
        limit = ph.rayleigh_limit(fsr1, F)
        res.append(limit * 1e12 if limit else None)
    out["resolve"] = res
    tm = []
    for R in TASK7_R:
        F = ph.coefficient_f(R)
        tm.append(ph.peak_transmission(R, v.A))
    out["tmax"] = tm
    return out


def table(head, rows, caption=None, cls="answers"):
    h = "".join(f"<th>{c}</th>" for c in head)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    cap = f"<caption>{caption}</caption>" if caption else ""
    return f'<table class="{cls}">{cap}<tr>{h}</tr>{body}</table>'


def answers_hidden():
    rows = []
    for code in lab.CODES:
        v = lab.Variant(code)
        rows.append([code, f(v.lam, 4), f(v.dlam, 3), f(v.A, 1), f(v.d_rings, 1), f(v.f_rings, 3)])
    return table(["Код", "λ, нм", "δλ дублета, пм", "A", "d (зад. 4), мм", "линза f (зад. 4), мм"], rows,
                 "Таблица 1<b>Скрытые величины и параметры вариантов</b>")


def answers_tasks_245():
    rows = []
    for code in lab.CODES:
        e = expected(code)
        v = e["v"]
        rows.append([code, f(v.lam, 4), f(e["fsr"][3], 4), f(e["fsr"][5], 4), f(v.lam ** 2 / 2 * 1e-3, 4),
                     f(e["rings"][0], 4), f(e["rings"][5], 4), f(e["slope"], 4),
                     " / ".join(f(x, 4) for x in e["shift"]), f(v.lam / 2, 4)])
    return table(["Код", "λ, нм", "Δλ (d = 5 мм), пм", "Δλ (d = 12 мм), пм", "наклон $b_1$ зад. 2, пм·мм",
                  "$r_1$, мм", "$r_6$, мм", "наклон $b_2$ зад. 4, мм²", "$\\Delta d_1/\\Delta d_2/\\Delta d_3$, нм",
                  "наклон $b_3$ зад. 5, нм"], rows,
                 "Таблица 2<b>Ожидаемые результаты заданий 2, 4, 5</b>")


def answers_tasks_367():
    rows = []
    for code in lab.CODES:
        e = expected(code)
        v = e["v"]
        w = e["width"]
        rows.append([code, f(w[3][0], 3), f(w[3][1], 3), f(w[5][0], 3), f(w[5][1], 3), f(e["dstar"], 4),
                     f(v.dlam, 3), " / ".join(f(x, 3) for x in e["resolve"]),
                     " / ".join(f(v.lam * 1e3 / x, 3) for x in e["resolve"]),
                     " / ".join(f(t, 3) for t in e["tmax"]), f(v.A, 1)])
    return table(["Код", "$w$ ($R$ = 0,9), пм", "$\\mathcal F$ ($R$ = 0,9)", "$w$ ($R$ = 0,98), пм",
                  "$\\mathcal F$ ($R$ = 0,98)", "$d^*$, мм", "δλ дублета, пм",
                  "$\\delta\\lambda_{\\min}$ ($R$ = 0,8/0,9/0,95), пм", "$\\mathcal A$ = λ/δλ$_{\\min}$",
                  "$T_{\\max}$ ($R$ = 0,9/0,95)", "$A$"], rows,
                 "Таблица 3<b>Ожидаемые результаты заданий 3, 6, 7</b>")


def example_rings():
    v = lab.Variant(0)
    lam = v.lam * 1e-9
    r_true = ph.ring_radii(lam, v.d_rings * 1e-3, 1.0, v.f_rings * 1e-3, 0.010)[:6] * 1e3
    rng = random.Random("example-rings")
    r = [round(x + rng.gauss(0, 0.006), 3) for x in r_true]
    k = list(range(1, 7))
    r2 = [x * x for x in r]
    fit = lab.fit_line(k, r2)
    name, value, err, unit = lab.derived("rings", fit, {"n": 1.0, "d": v.d_rings, "f": v.f_rings}, None)
    mk = sum(k) / 6
    sxx = sum((x - mk) ** 2 for x in k)
    zones = [math.pi * (r2[i + 1] - r2[i]) for i in range(5)] + [None]
    rows = [[kk, f(rr, 4), f(rr2, 4), "—" if s is None else f(s, 3)] for kk, rr, rr2, s in zip(k, r, r2, zones)]
    tbl = table(["$k$", "$r_k$, мм", "$r_k^2$, мм²", "$S_k=\\pi(r_{k+1}^2-r_k^2)$, мм²"], rows,
                "Таблица П1<b>Измеренные радиусы колец и площади зон (пример)</b>", "blank")
    rel = err / value
    exp = math.floor(math.log10(err))
    if err / 10 ** exp < 2:
        exp -= 1
    err_r, val_r = round(err, -exp), round(value, -exp)
    dec = max(-exp, 0)
    err_s, val_s = f"{err_r:.{dec}f}".replace(".", ","), f"{val_r:.{dec}f}".replace(".", ",")
    return f"""
<p>Пример выполнен для варианта, которого нет среди выдаваемых: $d = {f(v.d_rings, 1)}$ мм,
$f = {f(v.f_rings, 3)}$ мм, $n = 1$, экран в фокусе. Радиусы шести колец, измеренные курсором на
разрезе при увеличенном масштабе, — в табл. П1. Пример предназначен для преподавателя: студентам его не выдают,
чтобы они сами проверили равенство площадей зон и вывели закон (10), а не подгоняли результат под образец.</p>
{tbl}
<p><b>1. Метод наименьших квадратов.</b> Для точек $(k_i,\\,y_i=r_i^2)$, $i=1\\ldots n$, $n=6$:
$\\bar k = {f(mk, 3)}$, $\\sum(k_i-\\bar k)^2 = {f(sxx, 3)}$. Наклон и свободный член</p>
<eq>b=\\frac{{\\sum(k_i-\\bar k)(y_i-\\bar y)}}{{\\sum(k_i-\\bar k)^2}} = {f(fit['b'], 5)}\\ \\text{{мм}}^2,\\qquad
a=\\bar y-b\\bar k={f(fit['a'], 4)}\\ \\text{{мм}}^2 .</eq>
<p><b>2. Погрешность наклона.</b> Остаточная дисперсия $s^2=\\sum(y_i-a-bk_i)^2/(n-2)$, стандартное отклонение
наклона $\\sigma_b=s/\\sqrt{{\\sum(k_i-\\bar k)^2}}={f(fit['sb'], 2)}$ мм². Коэффициент Стьюдента для
$n-2=4$ степеней свободы и вероятности 0,95: $t={f(fit['t'], 3)}$. Доверительная граница
$\\Delta b = t\\,\\sigma_b = {f(fit['db'], 2)}$ мм².</p>
<p><b>3. Искомая величина.</b> Из (10) $\\lambda = b\\,d/(f^2 n)$:</p>
<eq>\\lambda=\\frac{{{f(fit['b'], 5)}\\cdot10^{{-6}}\\cdot{f(v.d_rings, 1)}\\cdot10^{{-3}}}}{{({f(v.f_rings, 3)}\\cdot10^{{-3}})^2\\cdot1}}
={f(value, 5)}\\ \\text{{нм}}.</eq>
<p>Параметры $d$ и $f$ заданы точно, поэтому относительная погрешность $\\lambda$ равна относительной погрешности
наклона: $\\Delta\\lambda/\\lambda=\\Delta b/b={f(100 * rel, 2)}\\ \\%$, $\\Delta\\lambda={f(err, 2)}$ нм.</p>
<p><b>4. Результат</b> (погрешность округляется до одной-двух значащих цифр, значение — до того же разряда):</p>
<eq>\\lambda = ({val_s} \\pm {err_s})\\ \\text{{нм}},\\qquad P=0{{,}}95 .</eq>
<p>Скрытая длина волны этого примера — {f(v.lam, 4)} нм: она лежит в пределах найденного интервала. Журнал
программы выполняет те же вычисления автоматически; в отчёте студент приводит их вручную хотя бы для
одного задания.</p>
"""


TABLES = {"answers_hidden": answers_hidden, "answers_tasks_245": answers_tasks_245,
          "answers_tasks_367": answers_tasks_367, "example_rings": example_rings}
