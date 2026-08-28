import time
from pyautocad import Autocad, APoint, aDouble

acad = Autocad(create_if_not_exists=True)
acad.app.Visible = True

for _ in range(10):
    try:
        if acad.app.Documents.Count == 0:
            acad.app.Documents.Add()
        _ = acad.app.ActiveDocument.ModelSpace
        break
    except Exception:
        time.sleep(0.5)

ms = acad.model

# Plot dimensions (in feet)
plot_width = 50
plot_depth = 36
floor_height = 10

# FIX 2: Added 'z' parameter so the AI's 3D coordinates don't crash
def pt(x, y, z=0):
    return APoint(x, y, z)

# FIX 1: Use aDouble() and flat coordinates for AddPolyline
boundary = ms.AddPolyline(aDouble(
    0, 0, 0,
    plot_width, 0, 0,
    plot_width, plot_depth, 0,
    0, plot_depth, 0,
    0, 0, 0
))
boundary.Closed = True
boundary.Color = 1  # Red

wall_thickness = 0.5

outer_walls = [
    [pt(0, 0), pt(0, plot_depth)],
    [pt(plot_width, 0), pt(plot_width, plot_depth)],
    [pt(0, 0), pt(plot_width, 0)],
    [pt(0, plot_depth), pt(plot_width, plot_depth)]
]

inner_walls_gf = [
    [pt(10, 10), pt(40, 10)], [pt(10, 20), pt(40, 20)], [pt(10, 30), pt(40, 30)],
    [pt(10, 10), pt(10, 30)], [pt(20, 10), pt(20, 20)], [pt(30, 10), pt(30, 20)],
    [pt(40, 10), pt(40, 30)], [pt(25, 20), pt(25, 30)], [pt(35, 20), pt(35, 30)]
]

inner_walls_ff = [
    [pt(10, 10), pt(40, 10)], [pt(10, 20), pt(40, 20)], [pt(10, 30), pt(40, 30)],
    [pt(10, 10), pt(10, 30)], [pt(18, 10), pt(18, 20)], [pt(32, 10), pt(32, 20)],
    [pt(40, 10), pt(40, 30)], [pt(25, 20), pt(25, 30)], [pt(35, 20), pt(35, 30)]
]

# Draw ground floor
for wall in outer_walls + inner_walls_gf:
    line = ms.AddLine(wall[0], wall[1])
    line.Color = 2  # Yellow

# Draw first floor
for wall in outer_walls + inner_walls_ff:
    start = pt(wall[0][0], wall[0][1], floor_height)
    end = pt(wall[1][0], wall[1][1], floor_height)
    line = ms.AddLine(start, end)
    line.Color = 3  # Green

# FIX 1: Flat array of doubles for the 3D stairs Polyline
stairs_width = 3
stairs = ms.AddPolyline(aDouble(
    12, 10, 0,
    12 + stairs_width, 10, 0,
    12 + stairs_width, 10, floor_height,
    12, 10, floor_height,
    12, 10, 0
))
stairs.Closed = True
stairs.Color = 5  # Blue

labels_gf = [
    ("Living", pt(25, 5)), ("Bedroom 1", pt(15, 15)), ("Bedroom 2", pt(25, 15)),
    ("Bedroom 3", pt(35, 15)), ("Kitchen", pt(15, 25)), ("Dining", pt(25, 25)),
    ("Common Bath", pt(35, 25))
]

labels_ff = [
    ("Master Bedroom", pt(22, 15)), ("Bedroom 4", pt(13, 15)), ("Bedroom 5", pt(37, 15)),
    ("Study", pt(15, 25)), ("Family Lounge", pt(25, 25)), ("Bath 1", pt(30, 25)),
    ("Bath 2", pt(40, 25))
]

for text, point in labels_gf:
    txt = ms.AddText(text, point, 2.5)
    txt.Color = 2  # Yellow

for text, point in labels_ff:
    txt = ms.AddText(text, pt(point[0], point[1], floor_height), 2.5)
    txt.Color = 3  # Green

ms.AddText("GROUND FLOOR", pt(25, 34), 3.5).Color = 2
ms.AddText("FIRST FLOOR", pt(25, 34, floor_height), 3.5).Color = 3

acad.app.ZoomExtents()