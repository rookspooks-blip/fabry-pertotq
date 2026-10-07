(function () {
  "use strict";
  const stack = [];                                  // откуда пришли: id ссылок по порядку
  const floatBack = document.getElementById("floatback");
  const KEY = "fp-defense-known";
  let known = new Set();
  try { known = new Set(JSON.parse(localStorage.getItem(KEY) || "[]")); } catch (e) { known = new Set(); }

  const WHO = "fp-defense-who";
  let who = "";
  try { who = localStorage.getItem(WHO) || ""; } catch (e) { who = ""; }

  function save() { try { localStorage.setItem(KEY, JSON.stringify([...known])); } catch (e) { /* без памяти */ } }

  function flash(el) {
    if (!el) return;
    el.classList.remove("flash");
    void el.offsetWidth;
    el.classList.add("flash");
  }

  function reveal(el) {                              // показать ответ, если он спрятан режимом проверки
    const card = el && el.closest(".card");
    if (card) card.classList.add("shown");
    let sec = el && el.closest("[data-hide]");          // чужой вопрос из словаря: открыть его и раздел
    while (sec) { sec.removeAttribute("data-hide"); sec = sec.closest("[data-hide]"); }
  }

  function go(el, block) {
    if (!el) return;
    reveal(el);
    el.scrollIntoView({ behavior: "smooth", block: block || "start" });
    flash(el.closest(".card, .entry") || el);
  }

  function updateBack() { floatBack.hidden = stack.length === 0; }

  // переход по ссылке в словарь или к вопросу: запоминаем, откуда ушли
  document.addEventListener("click", function (ev) {
    const a = ev.target.closest("a.g, a.jump");
    if (!a) return;
    const id = a.getAttribute("href").slice(1);
    const target = document.getElementById(id);
    if (!target) return;
    ev.preventDefault();
    if (!a.id) a.id = "j" + Math.random().toString(36).slice(2, 9);
    stack.push(a.id);
    updateBack();
    go(target);
    try { history.replaceState(null, "", "#" + id); } catch (e) { /* не важно */ }
  });

  function back() {
    const id = stack.pop();
    updateBack();
    if (!id) { document.querySelector(".toc").scrollIntoView({ behavior: "smooth" }); return; }
    const el = document.getElementById(id);
    go(el, "center");
    if (el) { el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash"); }
  }
  document.querySelectorAll("button.back").forEach(b => b.addEventListener("click", back));

  // «Знаю»
  const cards = [...document.querySelectorAll(".card")];
  const prog = document.getElementById("prog");
  function paint() {
    let n = 0, total = 0;
    cards.forEach(c => {
      const k = known.has(c.dataset.q);
      if (mine(c)) { total++; if (k) n++; }
      c.classList.toggle("is-known", k);
      c.querySelector(".known").setAttribute("aria-pressed", k ? "true" : "false");
    });
    prog.textContent = (who ? who + ": знаю " : "Знаю ") + n + " из " + total;
  }
  document.querySelectorAll(".known").forEach(b => b.addEventListener("click", function () {
    const q = b.dataset.q;
    known.has(q) ? known.delete(q) : known.add(q);
    save(); paint(); filter();
  }));
  document.querySelectorAll(".reveal").forEach(b => b.addEventListener("click", function () {
    b.closest(".card").classList.add("shown");
  }));

  // режим проверки
  const quiz = document.getElementById("quiz");
  quiz.addEventListener("change", function () {
    document.body.classList.toggle("quiz", quiz.checked);
    cards.forEach(c => c.classList.remove("shown"));
  });

  // поиск и «только невыученные»
  const find = document.getElementById("find");
  const unknownOnly = document.getElementById("unknown");
  function mine(c) { return !who || c.dataset.owner === who || c.dataset.owner === "Общие"; }
  function filter() {
    const q = find.value.trim().toLowerCase();
    cards.forEach(c => {
      const hit = !q || c.textContent.toLowerCase().includes(q);
      const ok = !unknownOnly.checked || !known.has(c.dataset.q);
      if (hit && ok && mine(c)) c.removeAttribute("data-hide"); else c.setAttribute("data-hide", "");
    });
    // разделы без видимых вопросов прячем, в оглавлении — сколько осталось
    document.querySelectorAll("section[data-sec]").forEach(s => {
      const n = s.querySelectorAll(".card:not([data-hide])").length;
      const li = document.querySelector('.toc li[data-sec="' + s.dataset.sec + '"]');
      if (n) s.removeAttribute("data-hide"); else s.setAttribute("data-hide", "");
      if (li) {
        li.querySelector(".cnt").textContent = n;
        if (n) li.removeAttribute("data-hide"); else li.setAttribute("data-hide", "");
      }
    });
    document.querySelectorAll(".entry").forEach(e => {
      const hit = !q || e.textContent.toLowerCase().includes(q);
      if (hit) e.removeAttribute("data-hide"); else e.setAttribute("data-hide", "");
    });
  }
  find.addEventListener("input", filter);
  unknownOnly.addEventListener("change", filter);

  // кто ты: Артём / Егор / Илья / все
  function choose(name) {
    who = name || "";
    try { localStorage.setItem(WHO, who); } catch (e) { /* без памяти */ }
    document.querySelectorAll(".pick").forEach(b => b.setAttribute("aria-pressed", b.dataset.pick === who ? "true" : "false"));
    document.querySelectorAll(".plan").forEach(p => { p.hidden = p.dataset.plan !== who; });
    document.body.dataset.who = who;
    paint(); filter();
  }
  document.querySelectorAll(".pick").forEach(b => b.addEventListener("click", () => choose(b.dataset.pick)));
  choose(who);
})();
