const pptxgen = require("pptxgenjs");
const path = require("path");
const D = path.dirname(__filename);
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Интерферометр Фабри - Перо";
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
  s.addText("Интерферометр Фабри - Перо · проект СЭЛФ, МГТУ им. Н. Э. Баумана", { x: 0.5, y: 5.25, w: 7, h: 0.25, fontFace: BODY, fontSize: 10, color: dk ? "8FA0B8" : MUTED, margin: 0, isTextBox: true });
  s.addText(String(n), { x: 9.0, y: 5.25, w: 0.5, h: 0.25, fontFace: BODY, fontSize: 10, color: dk ? "8FA0B8" : MUTED, align: "right", margin: 0, isTextBox: true });
}

// 1
let s = pres.addSlide(); dark(s);
s.addImage({ path: path.join(D, "rings_circle.png"), x: 5.9, y: 0.75, w: 3.6, h: 3.6 });
s.addText("Интерферометр\nФабри - Перо", { x: 0.5, y: 0.9, w: 5.2, h: 1.6, fontFace: HEAD, fontSize: 40, bold: true, color: "FFFFFF", margin: 0, isTextBox: true, valign: "top" });
s.addText("Модель многолучевой интерференции света и виртуальная лабораторная работа", { x: 0.5, y: 2.65, w: 5.0, h: 1.25, fontFace: BODY, fontSize: 20, color: TEAL, margin: 0, isTextBox: true, valign: "top" });
s.addText("Проект СЭЛФ · МГТУ им. Н. Э. Баумана", { x: 0.5, y: 4.35, w: 6, h: 0.3, fontFace: BODY, fontSize: 14, color: "C9D4E5", margin: 0, isTextBox: true });
s.addText("Сидоренко Е. К. (ИБМ5-31Б) · Кузнецов А. В. · Кадников И. В. (ИБМ2-32Б)", { x: 0.5, y: 4.7, w: 9, h: 0.3, fontFace: BODY, fontSize: 12, color: "8FA0B8", margin: 0, isTextBox: true });
s.addNotes("Здравствуйте. Нас зовут Егор Сидоренко, Артём Кузнецов и Илья Кадников, мы студенты МГТУ имени Баумана, группы ИБМ5-31Б и ИБМ2-32Б. Представляем проект, выполненный в рамках СЭЛФ: математическую модель интерферометра Фабри-Перо и виртуальную лабораторную работу, построенную на этой модели. Картина колец на слайде получена расчётом по нашей модели.");

// 2
s = pres.addSlide(); light(s); title(s, "Цель и задачи");
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 1.25, w: 3.9, h: 3.55, fill: { color: SOFT }, rectRadius: 0.12, line: { color: SOFT } });
s.addText("Цель", { x: 0.75, y: 1.4, w: 3.4, h: 0.4, fontFace: HEAD, fontSize: 20, bold: true, color: "0F8F7E", margin: 0, isTextBox: true });
s.addText("Построить математическую модель многолучевой интерференции в интерферометре Фабри - Перо и на её основе разработать методику измерения длины световой волны.", { x: 0.75, y: 1.9, w: 3.4, h: 2.7, fontFace: BODY, fontSize: 15, color: INK, margin: 0, isTextBox: true, valign: "top" });
const tasks2 = [["Вывести формулу Эйри", "и получить характеристики прибора: дисперсию, ширину пика, резкость, разрешение"], ["Получить закон радиусов колец", "равного наклона и доказать равенство площадей зон"], ["Определить границы применимости", "модели: допущения, малые углы, расфокусировка экрана"], ["Разработать три способа измерения", "длины волны с обработкой методом наименьших квадратов"]];
tasks2.forEach((c, i) => {
  const y = 1.25 + i * 0.9;
  s.addShape(pres.shapes.OVAL, { x: 4.75, y: y + 0.05, w: 0.5, h: 0.5, fill: { color: TEAL }, line: { color: TEAL } });
  s.addText(String(i + 1), { x: 4.75, y: y + 0.05, w: 0.5, h: 0.5, fontFace: HEAD, fontSize: 18, bold: true, color: BG, align: "center", valign: "middle", margin: 0, isTextBox: true });
  s.addText(c[0], { x: 5.45, y, w: 4.05, h: 0.32, fontFace: HEAD, fontSize: 15, bold: true, color: INK, margin: 0, isTextBox: true });
  s.addText(c[1], { x: 5.45, y: y + 0.33, w: 4.05, h: 0.5, fontFace: BODY, fontSize: 12, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
});
foot(s, 2);
s.addNotes("Цель работы: построить математическую модель многолучевой интерференции в интерферометре Фабри-Перо и на её основе разработать методику измерения длины световой волны. Для этого поставлены четыре задачи. Первая: вывести формулу Эйри и получить из неё характеристики прибора. Вторая: получить закон радиусов колец равного наклона и доказать равенство площадей зон между соседними кольцами. Третья: определить границы применимости модели. Четвёртая: разработать три независимых способа измерения длины волны с обработкой методом наименьших квадратов. Актуальность определяется тем, что реальный интерферометр является дорогим прибором и редко доступен в учебных лабораториях, а модель позволяет изучить явление количественно.");

// 3
s = pres.addSlide(); light(s); title(s, "Вывод формулы Эйри");
const steps3 = [["1", "Лучи", "Каждое отражение умножает амплитуду на r = √R, а соседние лучи сдвинуты по фазе на δ = 4πnd·cosθ/λ."], ["2", "Сумма", "Бесконечная геометрическая прогрессия: E = t²·Σ(r²e^{iδ})^k = t² / (1 − R·e^{iδ})."], ["3", "Интенсивность", "T = |E|² даёт формулу Эйри; F = 4R/(1 − R)² - коэффициент резкости."]];
steps3.forEach((c, i) => {
  const y = 1.2 + i * 1.1;
  s.addShape(pres.shapes.OVAL, { x: 0.5, y: y + 0.05, w: 0.5, h: 0.5, fill: { color: TEAL }, line: { color: TEAL } });
  s.addText(c[0], { x: 0.5, y: y + 0.05, w: 0.5, h: 0.5, fontFace: HEAD, fontSize: 18, bold: true, color: BG, align: "center", valign: "middle", margin: 0, isTextBox: true });
  s.addText(c[1], { x: 1.2, y, w: 3.7, h: 0.3, fontFace: HEAD, fontSize: 16, bold: true, color: INK, margin: 0, isTextBox: true });
  s.addText(c[2], { x: 1.2, y: y + 0.32, w: 3.7, h: 0.7, fontFace: BODY, fontSize: 13, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
});
s.addText("T = Tmax / (1 + F·sin²(δ/2))", { x: 5.2, y: 1.2, w: 4.3, h: 0.5, fontFace: HEAD, fontSize: 22, bold: true, italic: true, color: INK, margin: 0, isTextBox: true });
s.addImage({ path: path.join(D, "graph.png"), x: 5.2, y: 1.9, w: 4.3, h: 1.96 });
s.addText("Максимумы - при δ = 2πm, то есть 2nd·cosθ = mλ. He-Ne лазер 632,8 нм, зазор 5 мм, R = 0,9", { x: 5.2, y: 3.95, w: 4.3, h: 0.6, fontFace: BODY, fontSize: 11, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
foot(s, 3);
s.addNotes("Выведем формулу Эйри. Свет многократно отражается между двумя зеркалами. При каждом отражении амплитуда умножается на корень из R, а соседние лучи сдвинуты по фазе на величину дельта, равную четыре пи n d косинус тэта, делённому на лямбда. Амплитуда прошедшей волны есть сумма бесконечной геометрической прогрессии и равна t в квадрате, делённому на единицу минус R на е в степени i дельта. Интенсивность определяется квадратом модуля этой величины: T равно T-макс, делённому на единицу плюс F на синус квадрат дельта пополам, где F равно четыре R, делённому на единицу минус R в квадрате. Максимумы пропускания наблюдаются при дельта, равной два пи m. Справа приведён рассчитанный график пропускания.");

// 4
s = pres.addSlide(); light(s); title(s, "Что даёт формула");
const st4 = [["λ² / (2nd)", "40,04 пм", "область свободной дисперсии: расстояние между пиками"], ["Δλ / 𝓕", "1,344 пм", "ширина пика, 𝓕 - резкость"], ["π√R / (1 − R)", "29,8", "резкость: во сколько раз пик уже расстояния между пиками"], ["λ / w", "≈ 470 000", "разрешающая способность"]];
st4.forEach((c, i) => {
  const x = 0.5 + (i % 2) * 4.55, y = 1.25 + Math.floor(i / 2) * 1.85;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 4.3, h: 1.65, fill: { color: SOFT }, rectRadius: 0.12, line: { color: SOFT } });
  s.addText(c[0], { x: x + 0.3, y: y + 0.15, w: 3.7, h: 0.35, fontFace: HEAD, fontSize: 16, italic: true, bold: true, color: "0F8F7E", margin: 0, isTextBox: true });
  s.addText(c[1], { x: x + 0.3, y: y + 0.5, w: 3.7, h: 0.6, fontFace: HEAD, fontSize: 32, bold: true, color: INK, margin: 0, isTextBox: true, valign: "middle" });
  s.addText(c[2], { x: x + 0.3, y: y + 1.12, w: 3.7, h: 0.45, fontFace: BODY, fontSize: 12, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
});
s.addText("Для He-Ne лазера: 632,8 нм, зазор d = 5 мм, отражение R = 0,9. Две линии считаются различимыми, если провал между ними не больше 0,81 максимума: δλmin ≈ 1,03·w", { x: 0.5, y: 4.8, w: 9, h: 0.42, fontFace: BODY, fontSize: 11, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
foot(s, 4);
s.addNotes("Из формулы Эйри следуют все характеристики прибора. Область свободной дисперсии, то есть расстояние между соседними пиками, равна лямбда в квадрате, делённому на два n d. Для He-Ne лазера при зазоре пять миллиметров она составляет около сорока пикометров. Ширина пика равна приблизительно 1,3 пикометра. Их отношение, резкость, приближённо равно пи корень из R, делённому на единицу минус R, и составляет около тридцати. Разрешающая способность, равная отношению лямбда к ширине пика, достигает приблизительно 470 тысяч. Две спектральные линии считаются разрешёнными, если провал между ними не превышает 0,81 максимума. Это значение соответствует критерию Рэлея для дифракционной решётки. Для пиков Эйри оно достигается при разности длин волн, примерно в 1,03 раза превышающей ширину пика.");

// 5
s = pres.addSlide(); dark(s); title(s, "Кольца равного наклона", "FFFFFF");
s.addText("r² = (f²nλ/d)·(k − 1 + ε)", { x: 0.5, y: 1.2, w: 5, h: 0.5, fontFace: HEAD, fontSize: 24, bold: true, italic: true, color: TEAL, margin: 0, isTextBox: true });
s.addText("Площади зон между кольцами равны: S = πf²nλ/d", { x: 0.5, y: 1.8, w: 5.2, h: 0.4, fontFace: BODY, fontSize: 16, color: "FFFFFF", margin: 0, isTextBox: true });
s.addText([
  { text: "Радиусы колец растут как √k, кольца сгущаются к краю", options: { bullet: true, breakLine: true } },
  { text: "ε - дробная часть порядка в центре (для He-Ne: 0,78)", options: { bullet: true, breakLine: true } },
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
s.addNotes("Кольца образуются потому, что линза собирает в одну окружность лучи с одинаковым углом наклона. Условие светлого кольца: два n d косинус тэта равно m лямбда. Для радиусов колец получаем: r в квадрате равно f в квадрате n лямбда, делённому на d, умноженному на k минус единица плюс эпсилон, где эпсилон - дробная часть порядка интерференции в центре. Следовательно, квадрат радиуса линейно зависит от номера кольца, а площади между соседними кольцами одинаковы и равны пи f в квадрате n лямбда, делённому на d. По наклону прямой r в квадрате от k определяется длина волны. Справа показано, как изменяется картина при коэффициенте отражения 0,5, 0,9 и 0,98: чем ближе R к единице, тем уже светлые кольца.");

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
  { text: "Пятно Пуассона - дифракция на диске; у нас - сложение лучей между зеркалами", options: { bullet: true, breakLine: true } },
  { text: "Общее: складываются когерентные волны с учётом фаз", options: { bullet: true } },
], { x: 5.55, y: 2.15, w: 3.7, h: 2.35, fontFace: BODY, fontSize: 13, color: INK, margin: 0, isTextBox: true, valign: "top", paraSpaceAfter: 8 });
foot(s, 6);
s.addNotes("Рассмотрим допущения модели. Излучение считается монохроматическим, зеркала плоскими и параллельными. Используется приближение малых углов: на краю экрана отклонение от закона «квадрат радиуса пропорционален номеру кольца» составляет 0,2 процента. Поглощение зеркал учитывается и снижает высоту пиков. Если экран расположен не в фокальной плоскости линзы, кольца размываются: при смещении на один миллиметр радиус кружка размытия равен 25 микрометрам. Отдельно рассмотрен вопрос о природе светлого пятна в центре картины. Это интерференция: в центре разность хода лучей близка к целому числу длин волн. Пятно Пуассона, напротив, является результатом дифракции на диске. Общее у обоих явлений состоит в том, что складываются когерентные волны с учётом их фаз.");

// 7
s = pres.addSlide(); light(s); title(s, "Три способа измерить длину волны");
const rows7 = [["По расстоянию между пиками", "Δλ = λ²/(2nd): по прямой Δλ(1/d) наклон b = λ²/(2n)"], ["По радиусам колец", "r² = (f²nλ/d)·k: по наклону прямой находится λ"], ["По сдвигу зеркала", "каждые λ/2 в центре появляется новое кольцо: наклон b = λ/(2n)"]];
rows7.forEach((r, i) => {
  const y = 1.25 + i * 0.95;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 5.6, h: 0.82, fill: { color: SOFT }, rectRadius: 0.1, line: { color: SOFT } });
  s.addText(r[0], { x: 0.7, y: y + 0.08, w: 5.2, h: 0.3, fontFace: HEAD, fontSize: 15, bold: true, color: INK, margin: 0, isTextBox: true });
  s.addText(r[1], { x: 0.7, y: y + 0.4, w: 5.2, h: 0.36, fontFace: BODY, fontSize: 12, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
});
s.addText("Прямая проводится методом наименьших квадратов, погрешность - по коэффициенту Стьюдента. Пример: скрытая λ = 454,6 нм, найдено (456,7 ± 2,3) нм - ошибка около 0,5 %", { x: 0.5, y: 4.15, w: 5.6, h: 0.8, fontFace: BODY, fontSize: 13, color: INK, margin: 0, isTextBox: true, valign: "top" });
s.addImage({ path: path.join(D, "lab.png"), x: 6.35, y: 1.25, w: 3.15, h: 1.89 });
s.addText("Виртуальная лабораторная: 7 заданий, 30 вариантов со скрытыми λ и A", { x: 6.35, y: 3.25, w: 3.15, h: 0.7, fontFace: BODY, fontSize: 11, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
foot(s, 7);
s.addNotes("На основе модели разработана лабораторная работа, в которой длина волны определяется тремя независимыми способами. Первый способ: по расстоянию между пиками. Так как дельта лямбда равна лямбда в квадрате, делённому на два n d, график зависимости дельта лямбда от единицы на d является прямой, а её наклон определяет лямбда. Второй способ: по радиусам колец, квадрат радиуса пропорционален номеру кольца. Третий способ: по сдвигу зеркала, так как при смещении на половину длины волны в центре возникает новое кольцо. Прямые проводятся методом наименьших квадратов, погрешность оценивается с помощью коэффициента Стьюдента. В качестве примера: при скрытой длине волны 454,6 нанометра студент получил 456,7 плюс-минус 2,3, то есть относительная ошибка составила около 0,5 процента. Лабораторная работа включает семь заданий и тридцать вариантов со скрытыми величинами.");

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
s.addNotes("Правильность модели проверена несколькими способами. Прямое суммирование 800 отражённых лучей совпадает с формулой Эйри. Расчёты программы расходятся с точными формулами менее чем на 0,1 процента, что подтверждено 30 автоматическими тестами. Модель реализована на языке Python и работает на Windows, macOS и Linux. В работе принимали участие трое: Артём Кузнецов отвечал за физическую часть, Егор Сидоренко за визуализацию и обработку результатов, Илья Кадников за программную реализацию. В дальнейшем планируется апробация лабораторной работы в учебной группе и расширение модели интерферометрами Майкельсона и Юнга. Благодарим за внимание.");

pres.writeFile({ fileName: path.join(D, "deck.pptx") }).then(() => console.log("ok"));
