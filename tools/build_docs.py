"""Сборка методичек: docs/src/*.html → docs/*.pdf.

Запуск:  python tools/build_docs.py            (всё)
         python tools/build_docs.py lab        (только файлы, в имени которых есть «lab»)
         python tools/build_docs.py --no-shots (не переснимать окно программы)

Что делает:
  1. Снимает окно программы (tools/docs_shots.py) → docs/img/*.png.
  2. В шаблонах docs/src/*.html заменяет особые метки:
       <eq n="1">LaTeX</eq>        — выключная формула с номером (1);
       <eq>LaTeX</eq>              — выключная формула без номера;
       $LaTeX$                     — формула в строке;
       <code ref="physics.airy"/>  — настоящий текст функции из программы
                                     (атрибут nodoc — без строки документации,
                                     lines="3-10" — только эти строки);
       <fig name="scheme"/>        — рисунок SVG из tools/docs_figures.py.
     Формулы переводятся в MathML — его Chromium рисует сам, без интернета.
     Код берётся прямо из fabry_perot/*.py, поэтому методичка не расходится с программой.
  3. Печатает страницы в PDF через Chromium (Playwright).

Нужно: pip install playwright latex2mathml pygments; шрифты Liberation и Latin Modern Math.
"""

import ast
import glob
import html
import os
import re
import subprocess
import sys
import textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "src")
OUT = os.path.join(ROOT, "docs")
BUILD = os.path.join(ROOT, "docs", "build")
sys.path.insert(0, os.path.join(ROOT, "tools"))

from latex2mathml.converter import convert  # noqa: E402
from pygments import highlight  # noqa: E402
from pygments.formatters import HtmlFormatter  # noqa: E402
from pygments.lexers import PythonLexer  # noqa: E402

import docs_figures  # noqa: E402


# ---------------------------------------------------------------------------
#  Фрагменты кода из программы
# ---------------------------------------------------------------------------

def find_node(tree, names):
    """Найти функцию или класс по пути «Класс.метод» в дереве модуля."""
    body = tree.body
    node = None
    for name in names:
        node = next((n for n in body if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.Assign))
                     and (getattr(n, "name", None) == name
                          or (isinstance(n, ast.Assign) and any(getattr(t, "id", None) == name
                                                               for t in n.targets)))), None)
        if node is None:
            raise KeyError(".".join(names))
        body = getattr(node, "body", [])
    return node


def source_of(ref, nodoc=False, lines=None):
    module, *names = ref.split(".")
    path = os.path.join(ROOT, "fabry_perot", module + ".py")
    text = open(path, encoding="utf-8").read()
    if not names:
        code = text
        start = 1
    else:
        node = find_node(ast.parse(text), names)
        first = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
        src = text.splitlines()[first - 1:node.end_lineno]
        start = first
        if nodoc and isinstance(node, (ast.FunctionDef, ast.ClassDef)) and ast.get_docstring(node):
            doc = node.body[0]
            cut_from, cut_to = doc.lineno - first, doc.end_lineno - first + 1
            src = src[:cut_from] + src[cut_to:]
        code = textwrap.dedent("\n".join(src))
    if lines:
        a, b = (int(v) for v in lines.split("-"))
        code = "\n".join(code.splitlines()[a - 1:b])
    return code, start, os.path.relpath(path, ROOT)


def code_block(match):
    attrs = dict(re.findall(r'(\w+)="([^"]*)"', match.group(0)))
    nodoc = " nodoc" in match.group(0)
    code, start, path = source_of(attrs["ref"], nodoc, attrs.get("lines"))
    body = highlight(code, PythonLexer(), HtmlFormatter(nowrap=True))
    caption = attrs.get("caption") or f"{path} — {attrs['ref'].split('.', 1)[-1]}"
    return (f'<figure class="code"><figcaption>{html.escape(caption)}</figcaption>'
            f'<pre>{body}</pre></figure>')


# ---------------------------------------------------------------------------
#  Формулы
# ---------------------------------------------------------------------------

def mathml(latex, display=False):
    latex = latex.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    return convert(latex.strip(), display="block" if display else "inline")


def equation(match):
    number = re.search(r'n="([^"]*)"', match.group(1) or "")
    body = mathml(match.group(2), display=True)
    label = f'<span class="eqn">({number.group(1)})</span>' if number else ""
    return f'<div class="equation">{body}{label}</div>'


def inline_math(text):
    return re.sub(r"(?<!\\)\$(.+?)(?<!\\)\$", lambda m: mathml(m.group(1)), text, flags=re.S)


# ---------------------------------------------------------------------------
#  Сборка
# ---------------------------------------------------------------------------

def figure(match):
    name = re.search(r'name="([^"]+)"', match.group(0)).group(1)
    return f'<div class="svgfig">{docs_figures.FIGURES[name]()}</div>'


def render_template(path):
    text = open(path, encoding="utf-8").read()
    protected = []

    def protect(fragment):
        protected.append(fragment)
        return f"\x00{len(protected) - 1}\x00"

    text = re.sub(r"<code\s[^>]*/>", lambda m: protect(code_block(m)), text)
    text = re.sub(r"<pre>.*?</pre>", lambda m: protect(m.group(0)), text, flags=re.S)
    text = re.sub(r"<fig\s[^>]*/>", lambda m: protect(figure(m)), text)
    text = re.sub(r"<eq(\s[^>]*)?>(.*?)</eq>", lambda m: protect(equation(m)), text, flags=re.S)
    text = inline_math(text)
    text = re.sub(r"\x00(\d+)\x00", lambda m: protected[int(m.group(1))], text)
    style = open(os.path.join(SRC, "style.css"), encoding="utf-8").read()
    style += HtmlFormatter(style="friendly").get_style_defs("figure.code pre")
    return text.replace("</head>", f"<style>{style}</style></head>", 1)


def chromium_path():
    if os.environ.get("CHROMIUM"):
        return os.environ["CHROMIUM"]
    found = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))
    return found[-1] if found else None


def to_pdf(pages):
    from playwright.sync_api import sync_playwright
    footer = ('<div style="width:100%;text-align:center;font-family:\'Liberation Serif\';font-size:10pt;'
              'color:#333"><span class="pageNumber"></span></div>')
    with sync_playwright() as p:
        exe = chromium_path()
        browser = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        page = browser.new_page()
        for html_path, pdf_path in pages:
            page.goto("file://" + html_path)
            page.wait_for_load_state("networkidle")
            page.pdf(path=pdf_path, format="A4", print_background=True, display_header_footer=True,
                     header_template="<div></div>", footer_template=footer,
                     margin={"top": "18mm", "bottom": "18mm", "left": "20mm", "right": "16mm"})
            print("  →", os.path.relpath(pdf_path, ROOT))
        browser.close()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--no-shots" not in sys.argv:
        print("Снимки окна программы…")
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "docs_shots.py")], check=True)
    os.makedirs(BUILD, exist_ok=True)
    pages = []
    for path in sorted(glob.glob(os.path.join(SRC, "*.html"))):
        name = os.path.splitext(os.path.basename(path))[0]
        if args and not any(a in name for a in args):
            continue
        out_html = os.path.join(BUILD, name + ".html")
        with open(out_html, "w", encoding="utf-8") as f:
            f.write(render_template(path).replace('src="img/', 'src="../img/'))
        pages.append((out_html, os.path.join(OUT, name + ".pdf")))
    print("PDF…")
    to_pdf(pages)


if __name__ == "__main__":
    main()
