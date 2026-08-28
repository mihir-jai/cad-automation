# AEC DRAFTING STANDARDS
# Based on Neufert Architects' Data (4th ed.) and the National Building Code of India (NBC 2016).
# This document is the permanent architectural education of the CAD agent.
# It is appended to the system prompt for EVERY generation. Follow it without exception.

## 1. WALL THICKNESS (NBC + standard practice)

| Wall Type              | Thickness (inches) | Thickness (feet) | Usage                                  |
|------------------------|--------------------|------------------|----------------------------------------|
| Exterior (main) wall   | 9 inch (230 mm)    | 0.75 ft          | Plot boundary walls, load-bearing outer|
| Interior partition     | 4.5 inch (115 mm)  | 0.375 ft         | Room-to-room internal walls            |
| Bathroom/kitchen wall  | 4.5 inch (115 mm)  | 0.375 ft         | Wet-area partitions (tile-ready)       |

- ALWAYS draw walls as DOUBLE LINES (outer line + inner line offset by the thickness).
- Exterior walls: offset 0.75 ft. Interior walls: offset 0.375 ft.
- The outer face of the exterior wall sits ON the plot boundary line.

## 2. DOOR & WINDOW OPENINGS

| Element        | Width   | Height  | Rule                                              |
|----------------|---------|---------|---------------------------------------------------|
| Main door      | 3.5 ft  | 7 ft    | Gap in exterior wall facing entry side            |
| Room doors     | 3.0 ft  | 7 ft    | 3-foot gap in the shared interior wall            |
| Bathroom door  | 2.5 ft  | 7 ft    | Smaller leaf for wet areas                        |
| Windows        | 4 ft    | 4 ft    | Sill at 3 ft above floor; place on exterior walls |

- NEVER draw a continuous closed wall loop around internal rooms — every habitable room
  MUST have at least one 3-ft door gap connecting it to a circulation space.
- Draw the door swing as a 90-degree arc (radius = door width) plus a straight door leaf.
- Draw windows as double parallel lines within the exterior wall thickness.

## 3. MINIMUM ROOM SIZES (NBC 2016 + Neufert residential standards)

### 1 BHK (approx. 450–650 sq ft built-up)
| Room              | Min Area (sq ft) | Min Dimension (ft) | Typical Size (ft)  |
|-------------------|------------------|--------------------|--------------------|
| Living/Lounge     | 100              | 10 x 10            | 12 x 16            |
| Bedroom           | 100              | 10 x 10            | 11 x 12            |
| Kitchen           | 50               | 8 x 7              | 8 x 10             |
| Bathroom (W+C)    | 30               | 5 x 7              | 5 x 8              |
| Passage/lobby     | —                | 3.5 ft wide        | 3.5 x 8            |

### 2 BHK (approx. 750–1000 sq ft built-up)
| Room              | Min Area (sq ft) | Min Dimension (ft) | Typical Size (ft)  |
|-------------------|------------------|--------------------|--------------------|
| Living/Dining     | 120              | 11 x 11            | 14 x 16            |
| Master Bedroom    | 110              | 10 x 11            | 12 x 14            |
| Second Bedroom    | 100              | 10 x 10            | 11 x 12            |
| Kitchen           | 50               | 8 x 7              | 8 x 10             |
| Bath + WC (attached) | 40            | 5 x 7              | 5 x 8              |
| Common Bath       | 30               | 5 x 7              | 5 x 7              |

### Larger units (3+ BHK): add 100–120 sq ft per extra bedroom; add a 20 sq ft
### attached bath per master bedroom; balconies min 3 ft depth.

## 4. PROPORTIONAL RATIOS (enforced)

- Bathroom area ≈ 20–30% of bedroom area. NEVER larger than the room it serves.
- Kitchen ≈ 40–50% of a bedroom.
- Circulation (passage + lobby) ≤ 15% of total built-up area.
- Living room is the largest habitable room on its floor.
- Every habitable room must have a window ≥ 1/7 of its floor area (NBC daylighting).

## 5. CIRCULATION & CLEARANCES (Neufert)

- Corridor width: min 3.5 ft (residential).
- Door swing must not hit furniture zones or swing into corridors.
- Keep 3 ft clear in front of every door.
- Bed side clearance: 2 ft minimum.
- Kitchen platform depth: 2 ft; keep 3 ft working aisle in front.
- Staircase (if present): tread 10 in, riser 6–7 in, width min 3 ft.

## 6. MATHEMATICAL LOGIC FOR DOUBLE-LINE WALLS IN AUTOCAD

A wall from point A(x1,y1) to point B(x2,y2) with thickness t is drawn as TWO parallel
lines plus two end caps, forming a closed rectangle:

- Direction vector: d = (dx, dy) = (x2-x1, y2-y1), normalized: |d| = sqrt(dx^2 + dy^2)
- Perpendicular (normal) vector: n = (-dy/|d|, dx/|d|) * t
- Line 1 (base): A -> B
- Line 2 (offset): A+n -> B+n
- End cap 1: A -> A+n
- End cap 2: B -> B+n

For AXIS-ALIGNED walls (all our walls are 90-degree):
- Horizontal wall (y1 == y2): offset in +Y by t. Lines: (x1,y1)-(x2,y2) and (x1,y1+t)-(x2,y2+t).
- Vertical wall (x1 == x2): offset in +X by t. Lines: (x1,y1)-(x2,y2) and (x1+t,y1)-(x2+t,y2).

To leave a DOOR GAP of width g in a wall segment, split the wall into two segments:
- Segment 1: start -> (door_start)
- Segment 2: (door_start + g) -> end
Then draw the swing arc centered at door_start with radius g, from the wall angle
sweeping 90 degrees, plus the door leaf line from the hinge perpendicular to the wall.

## 7. DRAFTING CONVENTIONS

- Plot boundary: red, closed polyline on the true plot dimensions.
- Exterior walls: thicker visual weight (color 7 white/black), interior walls same layer.
- Room labels: centered in the room, height = room_width * 0.15, ALL-CAPS names.
- Dimension text (if drawn): height = room_width * 0.08, placed outside the plan.
- North arrow (optional): small triangle at top-right of the plan.
- Always end with ZoomExtents.