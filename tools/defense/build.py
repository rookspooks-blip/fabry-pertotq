"""Собирает docs/defense.html — подготовка к защите со словарём и переходами туда-обратно.

Запуск:  python tools/defense/build.py
"""

import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import glossary  # noqa: E402
import q1  # noqa: E402,F401
import q2  # noqa: E402,F401
import q3  # noqa: E402,F401
from qbase import SECTIONS  # noqa: E402

GL = {e["key"]: e for e in glossary.ENTRIES}
for i, e in enumerate(glossary.ENTRIES, 1):
    e["id"] = f"g{i}"
    e["uses"] = []                                   # (id блока, подпись) — где встречается

LINK = re.compile(r"\{([^{}|]+)(?:\|([^{}]*))?\}")
counter = [0]
missing = set()


# --- автоматические ссылки на буквы ---------------------------------------
# сочетания с подстрочными индексами (через теги) — целиком
TAGGED = [("δλ<sub>min</sub>", "δλmin"), ("T<sub>max</sub>", "Tmax"), ("T<sub>min</sub>", "Tmin"),
          ("σ<sub>b</sub>", "σb"), ("r<sub>k+1</sub>", "rₖ"), ("r<sub>k</sub>", "rₖ")]
# буквы и обозначения без тегов — длинные сначала
TOKENS = ["Δd₀", "Δλ", "Δν", "Δd", "δλ", "δ½", "θ′", "m₀", "m₁", "d*", "λ₁", "λ₂", "x̄", "𝓕", "𝒜", "𝑛", "𝑁",
          "λ", "δ", "θ", "ε", "ρ", "ν"]
LATIN = set("dnRAFfLDrkmSNTIEcw")
NOSPLIT = {"sin", "cos", "tg", "arcsin", "arctg", "max", "min", "sinc"}
SKIP = re.compile(r"(\{[^{}]*\}|<a\b[^>]*>.*?</a>|<code>.*?</code>|<[^>]+>)", re.S)
TOK_RE = re.compile("|".join(re.escape(x) for x in TOKENS) + r"|Δ(?![A-Za-zα-ωΑ-Ω])|[A-Za-z]+")


def autolink(text, own=None):
    """Каждую букву-обозначение превратить в {ключ|буква} (кроме уже размеченных мест и тегов)."""
    for raw, key in TAGGED:
        if key != own:
            text = text.replace(raw, "{" + key + "|" + raw + "}")
    out = []
    for part in SKIP.split(text):
        if not part or SKIP.fullmatch(part):
            out.append(part)
            continue

        def tok(m):
            s = m.group(0)
            if s in TOKENS or s == "Δ":
                return s if s == own else "{" + s + "|" + s + "}"
            if s in NOSPLIT or not all(ch in LATIN for ch in s):
                return s
            return "".join(ch if ch == own else "{" + ch + "|" + ch + "}" for ch in s)
        out.append(TOK_RE.sub(tok, part))
    return "".join(out)


def render(text, where, label, own=None):
    """Разметка: ⟦формула⟧, ⟪формула отдельной строкой⟫, {ключ} и {ключ|текст} — ссылки в словарь."""
    text = autolink(text, own)
    text = text.replace("⟪", '<span class="fb">').replace("⟫", "</span>")
    text = text.replace("⟦", '<span class="f">').replace("⟧", "</span>")

    def link(m):
        key, shown = m.group(1).strip(), m.group(2)
        e = GL.get(key)
        if e is None:
            missing.add(key)
            return shown or key
        counter[0] += 1
        if not e["uses"] or e["uses"][-1][0] != where:
            e["uses"].append((where, label))
        cls = "g sym" if e["kind"] == "sym" else ("g fn" if e["kind"] == "func" else "g")
        return f'<a class="{cls}" id="l{counter[0]}" href="#{e["id"]}">{shown or key}</a>'
    return LINK.sub(link, text)


def para(text, where, label):
    text = render(" ".join(text.split()), where, label)
    return text if text.lstrip().startswith(("<ol", "<table", "<ul")) else f"<p>{text}</p>"


# --- вопросы ---------------------------------------------------------------
num = 0
toc, body = [], []
for s in SECTIONS:
    toc.append(f'<li><a class="jump" href="#s-{s["key"]}">{html.escape(s["title"])}</a>'
               f' <span class="cnt">{len(s["items"])}</span></li>')
    cards = []
    for it in s["items"]:
        num += 1
        qid = f"q{num}"
        label = f"В{num}"
        q = render(it["q"], qid, label)
        parts = [f'<div class="short"><span class="tag">Коротко</span>{para(it["short"], qid, label)}</div>']
        if it["long"]:
            parts.append(f'<div class="long"><span class="tag">Почему и как</span>{para(it["long"], qid, label)}</div>')
        if it["more"]:
            parts.append(f'<div class="more"><span class="tag">Если копнут глубже</span>{para(it["more"], qid, label)}</div>')
        cards.append(
            f'<article class="card" id="{qid}" data-q="{qid}">'
            f'<header><span class="qn">{label}</span><h3>{q}</h3>'
            f'<button class="known" type="button" data-q="{qid}" aria-pressed="false">Знаю</button></header>'
            f'<button class="reveal" type="button">Показать ответ</button>'
            f'<div class="ans">{"".join(parts)}</div></article>')
    body.append(f'<section class="qs" id="s-{s["key"]}"><h2>{html.escape(s["title"])}</h2>'
                f'<p class="lead">{html.escape(s["lead"])}</p>{"".join(cards)}</section>')

# --- словарь ---------------------------------------------------------------
gl_html = []
for kind, title, lead in (("sym", "Буквы и обозначения", "Что значит каждая буква в формулах."),
                          ("term", "Термины", "Физика, оптика, обработка данных, программирование."),
                          ("func", "Функции программы", "Где в коде считается то, о чём спрашивают.")):
    items = []
    for e in glossary.ENTRIES:
        if e["kind"] != kind:
            continue
        b = render(" ".join(e["body"].split()), e["id"], e["title"], own=e["key"])
        items.append((e, b))
    entries = []
    for e, b in items:
        uses = "".join(f'<a class="use jump" href="#{w}">{html.escape(re.sub("<[^>]+>", "", lab))}</a>'
                       for w, lab in e["uses"] if w.startswith("q"))
        uses_html = f'<div class="uses"><span>Встречается:</span>{uses}</div>' if uses else ""
        entries.append(f'<div class="entry {kind}" id="{e["id"]}"><div class="eh"><h4>{e["title"]}</h4>'
                       f'<button class="back" type="button" title="Вернуться туда, откуда пришли">↩ назад</button></div>'
                       f'<p>{b}</p>{uses_html}</div>')
    gl_html.append(f'<section class="gl" id="gl-{kind}"><h2>{title}</h2><p class="lead">{lead}</p>'
                   f'<div class="entries">{"".join(entries)}</div></section>')

if missing:
    raise SystemExit("Нет в словаре: " + ", ".join(sorted(missing)))

NUMBERS = [("λ = 632,8 нм, d = 5 мм, n = 1", "m₀ = 15 802,78; ε = 0,78"),
           ("R = 0,9", "F = 360; контраст 361; 𝓕 = 29,79 (≈ π√R/(1−R) = 29,80)"),
           ("Δλ при d = 5 мм", "40,04 пм; Δν = 29,98 ГГц"),
           ("w при d = 5 мм, R = 0,9", "1,344 пм"),
           ("𝒜 = λ/w", "≈ 470 000"),
           ("f²nλ/d при f = 200 мм", "5,06 мм²; площадь зоны S ≈ 15,9 мм²"),
           ("Радиусы r₁, r₂ (f = 200 мм)", "1,989 и 3,003 мм; 19 колец на экране 10 мм"),
           ("Наибольший угол на экране 10 мм, f = 200 мм", "2,86°"),
           ("Ошибка закона r² ∝ k на краю", "≈ 0,2 % (у первых колец 0,01 %)"),
           ("Расфокусировка 1 мм (D = 10 мм, f = 200 мм)", "кружок радиусом 25 мкм; ширина внешних колец ≈ 8 мкм"),
           ("Критерий провала", "0,81 = 8/π²; δλmin ≈ 1,03·w"),
           ("R, при котором появляется ширина пика", "R > 0,172 (F > 1)"),
           ("t Стьюдента, 6 точек, прямая y = a + bx", "2,78 (4 степени свободы)"),
           ("Точность модели / точность студента", "< 0,1 % / 0,2–1 %")]
numbers = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in NUMBERS)

CSS = open(os.path.join(HERE, "page.css"), encoding="utf-8").read()
JS = open(os.path.join(HERE, "page.js"), encoding="utf-8").read()

page = f"""<title>Защита: интерферометр Фабри — Перо</title>
<meta name="description" content="Вопросы и ответы к защите проекта: модель, допущения, физика, лабораторная, программа.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&family=Spectral:ital,wght@0,500;0,600;1,400;1,500&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header class="top">
  <p class="eyebrow">Проект СЭЛФ · МГТУ им. Н. Э. Баумана</p>
  <h1>Защита проекта «Интерферометр Фабри — Перо»</h1>
  <p class="intro">{num} вопросов по всем сторонам проекта — от модели и её допущений до сборки программы. У каждого
  ответа три слоя: <b>коротко</b> — что сказать вслух, <b>почему и как</b> — чтобы понимать, <b>если копнут глубже</b> — на
  добивающие вопросы. Любая подчёркнутая буква, термин или функция ведёт в словарь; кнопка <b>↩ назад</b> там возвращает
  ровно туда, откуда пришёл.</p>
  <p class="intro">Как учить: прочитай раздел целиком, потом включи «Проверь себя» — ответы спрячутся, отвечай вслух и
  открывай для проверки. Отмечай «Знаю» — счётчик покажет, что осталось.</p>
</header>
<div class="bar" role="toolbar" aria-label="Инструменты">
  <input id="find" type="search" placeholder="Найти вопрос или слово…" aria-label="Поиск">
  <label class="sw"><input id="quiz" type="checkbox"> Проверь себя</label>
  <label class="sw"><input id="unknown" type="checkbox"> Только невыученные</label>
  <span class="prog" id="prog"></span>
</div>
<nav class="toc" aria-label="Разделы"><h2>Разделы</h2><ol>{"".join(toc)}</ol>
<p class="tocg"><a class="jump" href="#numbers">Числа, которые надо помнить</a> ·
<a class="jump" href="#gl-sym">Буквы</a> · <a class="jump" href="#gl-term">Термины</a> ·
<a class="jump" href="#gl-func">Функции программы</a></p></nav>
<main>
{"".join(body)}
<section class="qs" id="numbers"><h2>Числа, которые надо помнить</h2>
<p class="lead">Пример He-Ne лазера из программы: λ = 632,8 нм, d = 5 мм, R = 0,9, f = 200 мм.</p>
<div class="tblw"><table class="nums">{numbers}</table></div></section>
<div class="glossary">{"".join(gl_html)}</div>
</main>
<footer class="foot">Собрано из исходников проекта (tools/defense). Все числа посчитаны той же программой.</footer>
</div>
<button class="back float" id="floatback" type="button" hidden>↩ назад</button>
<script>{JS}</script>
"""

out = os.path.join(ROOT, "docs", "defense.html")
with open(out, "w", encoding="utf-8") as fh:
    fh.write(page)
print(out, num, "вопросов,", len(glossary.ENTRIES), "статей словаря,", counter[0], "ссылок")
