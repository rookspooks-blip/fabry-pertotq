import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PIL import Image

from fabry_perot.qt import QtWidgets
from fabry_perot.theme import app_icon_image

app = QtWidgets.QApplication([])
out = os.path.join(ROOT, "assets")
os.makedirs(out, exist_ok=True)
png = os.path.join(out, "icon.png")
app_icon_image(1024).save(png)
image = Image.open(png)
image.save(os.path.join(out, "icon.ico"), sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
image.save(os.path.join(out, "icon.icns"))
print("assets/icon.png, icon.ico, icon.icns")
