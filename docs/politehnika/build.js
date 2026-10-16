const pptxgen = require("pptxgenjs");
const path = require("path");
const D = path.dirname(__filename);
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Интерферометр Фабри — Перо";
pres.author = "Сидоренко Е. К., Кузнецов А. В., Кадников И. В.";
const BG = "0B1220", PANEL = "141E33", TEAL = "22C7B0", ORANGE = "FF7A45", INK = "1B2437", MUTED = "5B6678", LIGHT = "FFFFFF", SOFT = "EEF3F8";
const HEAD = "Cambria", BODY = "Calibri";
const t = (s, o) => s.addText;
function title(s, text, color) {
  s.addText(text, { x: 0.5, y: 0.35, w: 9, h: 0.7, fontFace: HEAD, fontSize: 30, bold: true, color: color || INK, margin: 0, isTextBox: true, valign: "top" });
}
function dark(s) { s.background = { color: BG }; }
function light(s) { s.background = { color: LIGHT }; }
function foot(s, n, dk) {
  s.addText("Интерферометр Фабри — Перо · проект СЭЛФ, МГТУ им. Н. Э. Баумана", { x: 0.5, y: 5.25, w: 7, h: 0.25, fontFace: BODY, fontSize: 10, color: dk ? "8FA0B8" : MUTED, margin: 0, isTextBox: true });
  s.addText(String(n), { x: 9.0, y: 5.25, w: 0.5, h: 0.25, fontFace: BODY, fontSize: 10, color: dk ? "8FA0B8" : MUTED, align: "right", margin: 0, isTextBox: true });
}

// 1
let s = pres.addSlide(); dark(s);
s.addImage({ path: path.join(D, "rings_circle.png"), x: 5.9, y: 0.75, w: 3.6, h: 3.6 });
s.addText("Интерферометр\nФабри — Перо", { x: 0.5, y: 0.9, w: 5.2, h: 1.6, fontFace: HEAD, fontSize: 40, bold: true, color: "FFFFFF", margin: 0, isTextBox: true, valign: "top" });
s.addText("Модель многолучевой интерференции света и виртуальная лабораторная работа", { x: 0.5, y: 2.65, w: 5.0, h: 1.25, fontFace: BODY, fontSize: 20, color: TEAL, margin: 0, isTextBox: true, valign: "top" });
s.addText("Проект СЭЛФ · МГТУ им. Н. Э. Баумана", { x: 0.5, y: 4.35, w: 6, h: 0.3, fontFace: BODY, fontSize: 14, color: "C9D4E5", margin: 0, isTextBox: true });
s.addText("Сидоренко Е. К. (ИБМ5-31Б) · Кузнецов А. В. · Кадников И. В. (ИБМ2-32Б)", { x: 0.5, y: 4.7, w: 9, h: 0.3, fontFace: BODY, fontSize: 12, color: "8FA0B8", margin: 0, isTextBox: true });
s.addNotes("Добрый день. Мы сделали интерактивную модель интерферометра Фабри — Перо и на её основе виртуальную лабораторную работу. Мы — Егор, Артём и Илья, группы ИБМ5-31Б и ИБМ2-32Б, проект СЭЛФ. Кольца на слайде — это не фотография, а картинка из нашей программы.");

// 2
s = pres.addSlide(); light(s); title(s, "Зачем это нужно");
const cards2 = [
  ["1", "Свет — волна", "Две световые волны могут погасить друг друга. Так возникают светлые и тёмные кольца: только волны так себя ведут."],
  ["2", "Кольца меряют длину волны", "По расстоянию между кольцами находят длину световой волны с точностью до долей процента."],
  ["3", "Но прибор дорог", "Настоящий интерферометр — сложная установка, в учебной лаборатории её мало. Поэтому мы сделали модель."],
];
cards2.forEach((c, i) => {
  const x = 0.5 + i * 3.05;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.35, w: 2.85, h: 3.5, fill: { color: SOFT }, rectRadius: 0.12, line: { color: SOFT } });
  s.addShape(pres.shapes.OVAL, { x: x + 0.25, y: 1.6, w: 0.6, h: 0.6, fill: { color: TEAL }, line: { color: TEAL } });
  s.addText(c[0], { x: x + 0.25, y: 1.6, w: 0.6, h: 0.6, fontFace: HEAD, fontSize: 22, bold: true, color: BG, align: "center", valign: "middle", margin: 0, isTextBox: true });
  s.addText(c[1], { x: x + 0.25, y: 2.4, w: 2.35, h: 0.7, fontFace: HEAD, fontSize: 20, bold: true, color: INK, margin: 0, isTextBox: true, valign: "top" });
  s.addText(c[2], { x: x + 0.25, y: 3.15, w: 2.35, h: 1.6, fontFace: BODY, fontSize: 14, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
});
foot(s, 2);
s.addNotes("Рассказывать мы будем со стороны природы света. Свет — волна: если сложить две волны так, что гребень попадает на впадину, получится темнота. В интерферометре свет многократно отражается между двумя зеркалами, и на экране видны светлые и тёмные кольца. По расстоянию между кольцами можно найти длину световой волны. Но настоящий прибор дорог, поэтому мы сделали его модель.");

// 3
s = pres.addSlide(); light(s); title(s, "Вывод формулы Эйри");
const steps3 = [["1", "Лучи", "Каждое отражение умножает амплитуду на r = √R, а соседние лучи сдвинуты по фазе на δ = 4πnd·cosθ/λ."], ["2", "Сумма", "Бесконечная геометрическая прогрессия: E = t²·Σ(r²e^{iδ})^k = t² / (1 − R·e^{iδ})."], ["3", "Интенсивность", "T = |E|² даёт формулу Эйри; F = 4R/(1 − R)² — коэффициент резкости."]];
steps3.forEach((c, i) => {
  const y = 1.2 + i * 1.1;
  s.addShape(pres.shapes.OVAL, { x: 0.5, y: y + 0.05, w: 0.5, h: 0.5, fill: { color: TEAL }, line: { color: TEAL } });
  s.addText(c[0], { x: 0.5, y: y + 0.05, w: 0.5, h: 0.5, fontFace: HEAD, fontSize: 18, bold: true, color: BG, align: "center", valign: "middle", margin: 0, isTextBox: true });
  s.addText(c[1], { x: 1.2, y, w: 3.7, h: 0.3, fontFace: HEAD, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  s.addText(c[2], { x: 1.2, y: y + 0.32, w: 3.7, h: 0.7, fontFace: BODY, fontSize: 13, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
});
s.addText("T = Tmax / (1 + F·sin²(δ/2))", { x: 5.2, y: 1.2, w: 4.3, h: 0.5, fontFace: HEAD, fontSize: 22, bold: true, italic: true, color: INK, margin: 0, isTextBox: true });
s.addImage({ path: path.join(D, "graph.png"), x: 5.2, y: 1.9, w: 4.3, h: 1.96 });
s.addText("Максимумы — при δ = 2πm, то есть 2nd·cosθ = mλ. He-Ne лазер 632,8 нм, зазор 5 мм, R = 0,9", { x: 5.2, y: 3.95, w: 4.3, h: 0.6, fontFace: BODY, fontSize: 11, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
foot(s, 3);
s.addNotes("Выведем формулу Эйри. Свет входит между двумя зеркалами и многократно отражается. Каждое отражение умножает амплитуду на корень из R, а соседние лучи отличаются по фазе на дельту: четыре пи n d косинус тэта на лямбда. Складываем бесконечную серию лучей — это геометрическая прогрессия, её сумма равна t квадрат делить на единица минус R на e в степени i дельта. Берём квадрат модуля и получаем формулу Эйри: пропускание T равно T-макс делить на единица плюс F синус квадрат дельта пополам, где F равно четыре R делить на единица минус R в квадрате. Максимум там, где дельта равна два пи m. Справа график: узкие острые пики.");

// 4
s = pres.addSlide(); light(s); title(s, "Что даёт формула");
const st4 = [["λ² / (2nd)", "40,04 пм", "область свободной дисперсии: расстояние между пиками"], ["Δλ / 𝓕", "1,344 пм", "ширина пика, 𝓕 — резкость"], ["π√R / (1 − R)", "29,8", "резкость: во сколько раз пик уже расстояния между пиками"], ["λ / w", "≈ 470 000", "разрешающая способность"]];
st4.forEach((c, i) => {
  const x = 0.5 + (i % 2) * 4.55, y = 1.25 + Math.floor(i / 2) * 1.85;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 4.3, h: 1.65, fill: { color: SOFT }, rectRadius: 0.12, line: { color: SOFT } });
  s.addText(c[0], { x: x + 0.3, y: y + 0.15, w: 3.7, h: 0.35, fontFace: HEAD, fontSize: 16, italic: true, bold: true, color: "0F8F7E", margin: 0, isTextBox: true });
  s.addText(c[1], { x: x + 0.3, y: y + 0.5, w: 3.7, h: 0.6, fontFace: HEAD, fontSize: 32, bold: true, color: INK, margin: 0, isTextBox: true, valign: "middle" });
  s.addText(c[2], { x: x + 0.3, y: y + 1.12, w: 3.7, h: 0.45, fontFace: BODY, fontSize: 12, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
});
s.addText("Для He-Ne лазера: 632,8 нм, зазор d = 5 мм, отражение R = 0,9. Две линии считаются различимыми, если провал между ними не больше 0,81 максимума: δλmin ≈ 1,03·w", { x: 0.5, y: 4.8, w: 9, h: 0.42, fontFace: BODY, fontSize: 11, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
foot(s, 4);
s.addNotes("Из формулы Эйри получаются все характеристики прибора. Расстояние между соседними пиками — область свободной дисперсии — равна лямбда квадрат делить на два n d. Для He-Ne лазера с зазором пять миллиметров это 40 пикометров. Ширина пика — около 1,3 пикометра. Отношение этих величин — резкость — примерно пи корень из R делить на единица минус R, это около 30. И разрешающая способность лямбда делить на ширину пика — около 470 тысяч. Две спектральные линии считаются различимыми, если яркость посередине между ними не больше 0,81 от максимума. Это тот же провал, что у критерия Рэлея для дифракционной решётки, и для пиков Эйри он получается при разности длин волн чуть больше ширины пика, около 1,03 w.");

// 5
s = pres.addSlide(); dark(s); title(s, "Кольца равного наклона", "FFFFFF");
s.addText("r² = (f²nλ/d)·(k − 1 + ε)", { x: 0.5, y: 1.2, w: 5, h: 0.5, fontFace: HEAD, fontSize: 24, bold: true, italic: true, color: TEAL, margin: 0, isTextBox: true });
s.addText("Площади зон между кольцами равны: S = πf²nλ/d", { x: 0.5, y: 1.8, w: 5.2, h: 0.4, fontFace: BODY, fontSize: 16, color: "FFFFFF", margin: 0, isTextBox: true });
s.addText([
  { text: "Радиусы колец растут как √k, кольца сгущаются к краю", options: { bullet: true, breakLine: true } },
  { text: "ε — дробная часть порядка в центре (для He-Ne: 0,78)", options: { bullet: true, breakLine: true } },
  { text: "Наклон прямой r²(k) даёт длину волны λ", options: { bullet: true } },
], { x: 0.5, y: 2.45, w: 5.2, h: 1.6, fontFace: BODY, fontSize: 14, color: "C9D4E5", margin: 0, isTextBox: true, valign: "top", paraSpaceAfter: 8 });
[["rings_R50", "R = 0,5"], ["rings_R90", "R = 0,9"], ["rings_R98", "R = 0,98"]].forEach((c, i) => {
  const x = 5.9 + (i % 2) * 1.85, y = 1.3 + Math.floor(i / 2) * 2.0;
  const w = i === 2 ? 1.8 : 1.8;
  s.addImage({ path: path.join(D, c[0] + ".png"), x: x, y: y, w: 1.65, h: 1.65 });
  s.addText(c[1], { x: x, y: y + 1.68, w: 1.65, h: 0.25, fontFace: BODY, fontSize: 11, color: "8FA0B8", align: "center", margin: 0, isTextBox: true });
});
s.addText("Чем ближе R к 1, тем тоньше кольца и темнее промежутки", { x: 7.75, y: 3.5, w: 1.75, h: 1.2, fontFace: BODY, fontSize: 11, color: "8FA0B8", margin: 0, isTextBox: true, valign: "top" });
foot(s, 5, true);
s.addNotes("Свет идёт под разными углами, и линза собирает его в кольца. Условие светлого кольца — два n d косинус тэта равно m лямбда. Отсюда радиусы колец: r квадрат равно f квадрат n лямбда делить на d, умноженное на k минус единица плюс эпсилон, где эпсилон — дробная часть порядка в центре. Поэтому квадрат радиуса растёт линейно с номером кольца, а площади между соседними кольцами одинаковы — каждая равна пи f квадрат n лямбда делить на d. Наклон прямой зависимости r квадрат от k даёт длину волны. На картинках справа видно, как меняются кольца при отражении зеркал 0,5, 0,9 и 0,98: чем ближе R к единице, тем тоньше светлые кольца.");

// 6
s = pres.addSlide(); light(s); title(s, "Допущения модели и пятно в центре");
s.addText("Допущения", { x: 0.5, y: 1.2, w: 4.3, h: 0.4, fontFace: HEAD, fontSize: 20, bold: true, color: INK, margin: 0, isTextBox: true });
s.addText([
  { text: "Свет монохроматический, зеркала плоские и параллельные", options: { bullet: true, breakLine: true } },
  { text: "Малые углы: ошибка закона r² ∝ k на краю экрана 0,2 %", options: { bullet: true, breakLine: true } },
  { text: "Поглощение A одинаково у обоих зеркал: Tmax = (1 − R − A)²/(1 − R)²", options: { bullet: true, breakLine: true } },
  { text: "Экран вне фокуса размывает кольца: кружок радиусом 25 мкм при сдвиге 1 мм", options: { bullet: true } },
], { x: 0.5, y: 1.7, w: 4.4, h: 3.0, fontFace: BODY, fontSize: 14, color: INK, margin: 0, isTextBox: true, valign: "top", paraSpaceAfter: 8 });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.3, y: 1.2, w: 4.2, h: 3.4, fill: { color: SOFT }, rectRadius: 0.12, line: { color: SOFT } });
s.addText("Пятно в центре: интерференция", { x: 5.55, y: 1.35, w: 3.7, h: 0.7, fontFace: HEAD, fontSize: 18, bold: true, color: INK, margin: 0, isTextBox: true });
s.addText([
  { text: "Это место, где разность хода близка к целому числу длин волн", options: { bullet: true, breakLine: true } },
  { text: "Пятно Пуассона — дифракция на диске; у нас — сложение лучей между зеркалами", options: { bullet: true, breakLine: true } },
  { text: "Общее: складываются когерентные волны с учётом фаз", options: { bullet: true } },
], { x: 5.55, y: 2.15, w: 3.7, h: 2.35, fontFace: BODY, fontSize: 13, color: INK, margin: 0, isTextBox: true, valign: "top", paraSpaceAfter: 8 });
foot(s, 6);
s.addNotes("Мы разобрали допущения модели. Свет считаем монохроматическим, зеркала плоскими и параллельными. Малые углы: на краю экрана закон «квадрат радиуса пропорционален номеру кольца» нарушается всего на 0,2 процента. Поглощение зеркал снижает высоту пиков. Если экран стоит не в фокусе линзы, кольца размываются: при сдвиге на миллиметр кружок размытия 25 микрометров. Отдельный вопрос — что такое светлое пятно в центре: интерференция или дифракция. Это интерференция: разность хода между лучами близка к целому числу длин волн. Пятно Пуассона — дифракция на диске. Общее у них — сложение когерентных волн с учётом фаз.");

// 7
s = pres.addSlide(); light(s); title(s, "Три способа измерить длину волны");
const rows7 = [["По расстоянию между пиками", "Δλ = λ²/(2nd): по прямой Δλ(1/d) наклон b = λ²/(2n)"], ["По радиусам колец", "r² = (f²nλ/d)·k: по наклону прямой находится λ"], ["По сдвигу зеркала", "каждые λ/2 в центре появляется новое кольцо: наклон b = λ/(2n)"]];
rows7.forEach((r, i) => {
  const y = 1.25 + i * 0.95;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 5.6, h: 0.82, fill: { color: SOFT }, rectRadius: 0.1, line: { color: SOFT } });
  s.addText(r[0], { x: 0.7, y: y + 0.08, w: 5.2, h: 0.3, fontFace: HEAD, fontSize: 15, bold: true, color: INK, margin: 0, isTextBox: true });
  s.addText(r[1], { x: 0.7, y: y + 0.4, w: 5.2, h: 0.36, fontFace: BODY, fontSize: 12, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
});
s.addText("Прямая проводится методом наименьших квадратов, погрешность — по коэффициенту Стьюдента. Пример: скрытая λ = 454,6 нм, найдено (456,7 ± 2,3) нм — ошибка около 0,5 %", { x: 0.5, y: 4.15, w: 5.6, h: 0.8, fontFace: BODY, fontSize: 13, color: INK, margin: 0, isTextBox: true, valign: "top" });
s.addImage({ path: path.join(D, "lab.png"), x: 6.35, y: 1.25, w: 3.15, h: 1.89 });
s.addText("Виртуальная лабораторная: 7 заданий, 30 вариантов со скрытыми λ и A", { x: 6.35, y: 3.25, w: 3.15, h: 0.7, fontFace: BODY, fontSize: 11, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
foot(s, 7);
s.addNotes("На этой физике мы построили лабораторную работу: длину волны можно найти тремя независимыми способами. Первый — по расстоянию между пиками: Дельта лямбда равно лямбда квадрат делить на два n d, поэтому график зависимости от единицы на d — прямая, наклон которой даёт лямбду. Второй — по радиусам колец: квадрат радиуса пропорционален номеру кольца. Третий — по сдвигу зеркала: каждые полдлины волны в центре появляется новое кольцо. Прямую проводим методом наименьших квадратов, погрешность оцениваем по коэффициенту Стьюдента. Пример: скрытая длина волны 454,6 нанометра, студент получил 456,7 плюс-минус 2,3, то есть ошибка около полупроцента. Справа — окно виртуальной лабораторной, в ней 7 заданий и 30 вариантов со скрытыми величинами.");

// 8
s = pres.addSlide(); dark(s); title(s, "Проверка, программа, команда", "FFFFFF");
const c8 = [["800 лучей", "прямое сложение совпадает с формулой Эйри"], ["< 0,1 %", "расхождение модели и точных формул"], ["30 тестов", "проверяют расчёты автоматически"]];
c8.forEach((c, i) => {
  const x = 0.5 + i * 3.05;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.25, w: 2.85, h: 1.55, fill: { color: PANEL }, rectRadius: 0.12, line: { color: PANEL } });
  s.addText(c[0], { x: x + 0.25, y: 1.4, w: 2.35, h: 0.6, fontFace: HEAD, fontSize: 28, bold: true, color: TEAL, margin: 0, isTextBox: true, valign: "middle" });
  s.addText(c[1], { x: x + 0.25, y: 2.05, w: 2.35, h: 0.65, fontFace: BODY, fontSize: 13, color: "C9D4E5", margin: 0, isTextBox: true, valign: "top" });
});
s.addText("Модель реализована на Python и работает на Windows, macOS и Linux", { x: 0.5, y: 3.05, w: 9, h: 0.35, fontFace: BODY, fontSize: 14, color: "FFFFFF", margin: 0, isTextBox: true });
s.addText("Артём Кузнецов · Егор Сидоренко · Илья Кадников", { x: 0.5, y: 3.6, w: 9, h: 0.4, fontFace: HEAD, fontSize: 20, bold: true, color: "FFFFFF", margin: 0, isTextBox: true });
s.addText("Дальше: проверить работу на группе студентов; добавить интерферометры Майкельсона и Юнга", { x: 0.5, y: 4.1, w: 9, h: 0.5, fontFace: BODY, fontSize: 14, color: TEAL, margin: 0, isTextBox: true, valign: "top" });
foot(s, 8, true);
s.addNotes("Как мы проверяли модель. Прямое сложение 800 отражённых лучей совпадает с формулой Эйри. Расчёты программы расходятся с точными формулами меньше чем на 0,1 процента, это проверяют 30 автоматических тестов. Модель реализована на Python и работает на Windows, macOS и Linux. Над проектом работали Артём, Егор и Илья. Дальше мы хотим проверить лабораторную на группе студентов и добавить интерферометры Майкельсона и Юнга. Спасибо за внимание.");

pres.writeFile({ fileName: path.join(D, "deck.pptx") }).then(() => console.log("ok"));
