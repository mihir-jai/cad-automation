import time
import math
from pyautocad import Autocad, APoint, aDouble


class ArchitecturalDrafter:
    """All AutoCAD geometry math wrapped so the AI never calls ms.* directly."""

    def __init__(self, acad, ms):
        self.acad = acad
        self.ms = ms
        self._labeled = set()       # room-name dedup -> one label per room
        self._drawn_walls = set()   # shared-wall dedup (rounded coord key)

    # --- coordinate helpers ---
    def pt(self, x, y, z=0):
        return APoint(x, y, z)

    @staticmethod
    def _key(p1, p2):
        return (round(min(p1[0], p2[0]), 1), round(min(p1[1], p2[1]), 1),
                round(max(p1[0], p2[0]), 1), round(max(p1[1], p2[1]), 1))

    # --- core: double-line wall with physical thickness ---
    def draw_wall(self, x1, y1, x2, y2, thickness=4.5):
        """Draw a closed double-line wall between two (x, y) points."""
        k = self._key((x1, y1), (x2, y2))
        if k in self._drawn_walls:
            return
        self._drawn_walls.add(k)

        if x1 == x2:                       # vertical wall -> offset in +X
            off = thickness
            coords = aDouble(x1, y1, 0, x2, y2, 0, x2 + off, y2, 0,
                             x1 + off, y1, 0, x1, y1, 0)
        elif y1 == y2:                     # horizontal wall -> offset in +Y
            off = thickness
            coords = aDouble(x1, y1, 0, x2, y1, 0, x2, y1 + off, 0,
                             x1, y1 + off, 0, x1, y1, 0)
        else:                              # diagonal -> normal offset
            dx, dy = x2 - x1, y2 - y1
            length = math.hypot(dx, dy)
            nx = -dy / length * thickness
            ny = dx / length * thickness
            coords = aDouble(x1, y1, 0, x2, y2, 0, x2 + nx, y2 + ny, 0,
                             x1 + nx, y1 + ny, 0, x1, y1, 0)
        self.ms.AddPolyline(coords).Closed = True

    # --- room: 4 double-line walls + centered, deduplicated label ---
    def draw_room(self, x_min, y_min, x_max, y_max, name=None, thickness=4.5):
        self.draw_wall(x_min, y_min, x_max, y_min, thickness)   # bottom
        self.draw_wall(x_max, y_min, x_max, y_max, thickness)   # right
        self.draw_wall(x_max, y_max, x_min, y_max, thickness)   # top
        self.draw_wall(x_min, y_max, x_min, y_min, thickness)   # left
        if name:
            self.draw_room_text(name, x_min, y_min, x_max, y_max)

    # --- text: center math + safe height + MiddleCenter alignment ---
    def draw_room_text(self, name, x_min, y_min, x_max, y_max):
        if name in self._labeled:
            return                          # one label per room, guaranteed
        self._labeled.add(name)
        cx = x_min + (x_max - x_min) / 2.0
        cy = y_min + (y_max - y_min) / 2.0
        height = (x_max - x_min) * 0.12
        height = min(height, 18)            # inches cap so it never bleeds
        t = self.ms.AddText(name, self.pt(cx, cy), height)
        t.Alignment = 10                      # acAlignmentMiddleCenter
        t.TextAlignmentPoint = self.pt(cx, cy)

    # --- door: 36-inch gap in the wall + 90-degree swing arc ---
    def draw_door(self, x, y, rotation=0, door_width=36):
        """Create a doorway. rotation: 0=horizontal wall, 90=vertical wall."""
        half = door_width / 2.0
        hinge = self.pt(x - half, y) if rotation == 0 else self.pt(x, y - half)

        # --- break the wall visually: mask a 36" segment with white lines ---
        if rotation == 0:          # gap runs along the wall's length (horizontal)
            for i in (0, 1):
                seg = self.ms.AddLine(self.pt(x - half, y - 4.5 * i),
                                      self.pt(x + half, y - 4.5 * i))
                seg.color = 7       # white over the wall lines
        else:                       # gap on a vertical wall
            for i in (0, 1):
                seg = self.ms.AddLine(self.pt(x - 4.5 * i, y - half),
                                      self.pt(x - 4.5 * i, y + half))
                seg.color = 7

        # --- 90-degree swing arc (correct COM args: center, radius, start, end) ---
        start_angle = math.radians(180) if rotation == 0 else math.radians(270)
        end_angle = start_angle + math.radians(90)
        # AutoCAD COM AddArc: center, radius, start_angle, end_angle (radians)
        self.ms.AddArc(hinge, door_width, start_angle, end_angle)

        # --- door leaf: thin line perpendicular to wall ---
        if rotation == 0:
            leaf_end = self.pt(x - half, y + door_width)
        else:
            leaf_end = self.pt(x + door_width, y - half)
        self.ms.AddLine(hinge, leaf_end)

    # --- exterior boundary ---
    def draw_plot_boundary(self, width, depth, thickness=9):
        self.draw_room(0, 0, width, depth, name=None, thickness=thickness)


# --- connection boilerplate ---
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
d = ArchitecturalDrafter(acad, ms)

print("[System] AutoCAD bridge active. ArchitecturalDrafter ready.")
# --- Inject generated CAD code below ---

