import os, sys, tempfile, subprocess, math
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, "/home/user/fabry-pertotq")
from fabry_perot.qt import QtCore, QtWidgets, QtGui, QColor, QFont, QPainter, QImage, Qt
QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat, QtCore.QSettings.Scope.UserScope, tempfile.mkdtemp())
from fabry_perot.app import create_app
from fabry_perot.window import MainWindow
from fabry_perot.lab import Variant
from fabry_perot.params import PRESETS
from fabry_perot.physics import ring_radii
import imageio_ffmpeg

W, H, FPS = 1600, 960, 25
BAR = 80
HO = H + BAR
app = QtWidgets.QApplication.instance() or create_app(["v"])
w = MainWindow(); w.resize(W, H); w.show(); app.processEvents()
out = sys.argv[1]
ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{W}x{HO}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                       "-crf", "22", "-preset", "medium", "-movflags", "+faststart", out], stdin=subprocess.PIPE)

def ease(t): return 0.5 - 0.5 * math.cos(math.pi * min(max(t, 0), 1))
def setp(**kv):
    for k, v in kv.items():
        w.params[k].set(v); w.shown[k] = w.params[k].value()
def frame(caption):
    w.recalc(); app.processEvents()
    img = w.grab().toImage().convertToFormat(QImage.Format.Format_RGB888)
    if img.width() != W or img.height() != H:
        img = img.scaled(W, H, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
    full = QImage(W, HO, QImage.Format.Format_RGB888); full.fill(QColor(8, 14, 26))
    p = QPainter(full); p.drawImage(0, 0, img)
    if caption:
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        f = QFont("DejaVu Sans"); f.setPixelSize(30); f.setBold(True); p.setFont(f)
        p.setPen(QColor(34, 199, 176)); p.drawLine(0, H, W, H)
        p.setPen(QColor(255, 255, 255)); p.drawText(QtCore.QRect(0, H, W, BAR), Qt.AlignmentFlag.AlignCenter, caption)
    p.end(); img = full
    bpl = img.bytesPerLine(); ptr = img.constBits(); ptr.setsize(bpl * HO) if hasattr(ptr, "setsize") else None
    raw = bytes(ptr) if not hasattr(ptr, "asstring") else ptr.asstring(bpl * HO)
    if bpl != W * 3:
        raw = b"".join(raw[r * bpl:r * bpl + W * 3] for r in range(HO))
    ff.stdin.write(raw)
def scene(sec, caption, step=None):
    n = int(sec * FPS)
    for i in range(n):
        if step: step(i / max(n - 1, 1))
        frame(caption)

name, base, dlam = PRESETS[0]
w.apply_preset(base, dlam); w.tweens.clear()
setp(**base); w.second.setChecked(False)
scene(7, "Формула Эйри: T = Tmax / (1 + F·sin²(δ/2)) — узкие пики и кольца")
scene(13, "Отражение зеркал R → 1: F = 4R/(1 − R)² растёт, пики и кольца тоньше",
      lambda t: setp(R=0.5 + (0.98 - 0.5) * ease(t / 0.8) if t < 0.8 else 0.98 + (0.9 - 0.98) * ease((t - 0.8) / 0.2)))
scene(12, "Зазор d: Δλ = λ²/(2nd) — чем больше d, тем ближе пики и больше колец",
      lambda t: setp(d=5 + 3 * math.sin(2 * math.pi * ease(t))))
scene(12, "Длина волны λ: меняются цвет и радиусы колец r² = f²nλ(k − 1 + ε)/d",
      lambda t: setp(lam=632.8 + (450 - 632.8) * ease(t / 0.35) if t < 0.35 else (450 + (690 - 450) * ease((t - 0.35) / 0.4) if t < 0.75 else 690 + (632.8 - 690) * ease((t - 0.75) / 0.25))))
scene(12, "Сдвиг зеркала на λ/2 — в центре рождается новое кольцо", lambda t: setp(dd=t * 3 * 316.4))
setp(dd=0)
name, base, dlam = PRESETS[1]
setp(**base); w.second.setChecked(True); setp(dlam=dlam)
scene(6, "Натриевый дублет 589,0 / 589,6 нм: две линии — двойные кольца")
scene(9, "Линии сливаются, когда провал больше 0,81 максимума: δλmin ≈ 1,03·w",
      lambda t: setp(dlam=600 * (20 / 600) ** ease(t)))
w.second.setChecked(False)
v = Variant(5); w.student = ("Студент", ""); w.set_lab(v)
setp(d=v.d_rings, f=v.f_rings, L=v.f_rings, R=0.9, dd=0, n=1.0, screen=10.0)
w.journal.select("rings")
rr = ring_radii(v.lam * 1e-9, v.d_rings * 1e-3, 1.0, v.f_rings * 1e-3, 0.010)[:7]
picked = [0]
def pick(t):
    k = min(int(t * 9), 7)
    while picked[0] < k:
        w.ring_view.picked.emit(float(rr[picked[0]]) * 1e3, 0.9); picked[0] += 1
scene(12, "Лабораторная: λ по радиусам колец — прямая МНК и погрешность", pick)
scene(3, "Интерферометр Фабри — Перо · проект СЭЛФ, МГТУ им. Н. Э. Баумана")
ff.stdin.close(); ff.wait()
print("ok", out)
