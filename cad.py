import time
from pyautocad import Autocad, APoint

# Connect to AutoCAD locally
acad = Autocad(create_if_not_exists=True)
acad.app.Visible = True
ms = acad.model

print("[System] AutoCAD bridge active. Ready to draw.")
# --- Inject generated CAD code below ---

