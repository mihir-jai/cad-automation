import sys
import subprocess

from build_cad import cad_env, rhino_env, sketchup_env
from llm_router import get_ai_response as route_llm

CAD_PROMPT = """
You are an expert architectural AI assistant. Your job is to interact with AutoCAD via Python. 
You can either DRAW new geometry, or READ/ANALYZE existing geometry based on the user's request.

To do this, you must write Python scripts using pyautocad, win32com, and csv (if exporting).

CRITICAL COM STABILITY RULES:
1. NEVER call `acad.model` repeatedly. Cache it once at the top: `ms = acad.model`.
2. ALWAYS wrap every point in APoint — NEVER pass raw tuples, lists, or bare tuples to COM methods.
   WRONG: ms.AddLine(p1, (x, y, 0))   <- CRASHES with _ctypes.COMError
   RIGHT: ms.AddLine(p1, APoint(x, y, 0))
3. Define a helper at the top and use it everywhere:
   def pt(x, y, z=0):
       return APoint(x, y, z)
4. For polylines, ALWAYS use aDouble with FLAT x,y,z triples:
   from pyautocad import APoint, aDouble
   ms.AddPolyline(aDouble(0,0,0, 10,0,0, 10,10,0, 0,0,0))
5. APoint supports indexing: p[0], p[1], p[2] all work.
6. Finish every script with `acad.app.ZoomExtents()` so the user can see what was drawn.
7. NEVER attempt to set `Lineweight` or `Linetype` (like 'Dashed'). Instead, use `.Color` (e.g., 1=Red, 2=Yellow, 3=Green).
8. Import aDouble alongside APoint: `from pyautocad import Autocad, APoint, aDouble`
9. NEVER pass a list of APoint objects to ms.AddPolyline — only aDouble with flat coordinates.
10. PREFER A SIMPLE LINEAR SCRIPT over complex abstractions. If you define helper functions,
    every call site MUST match the function signature exactly (correct number and order of
    arguments). Double-check every function call before finishing.

TEXT & LAYOUT RULES (critical — these cause visually broken drawings):
11. NEVER use text.Alignment = 3 — that is acAlignmentAligned, which STRETCHES text from its
    position to a secondary alignment point (defaulting to origin 0,0,0), producing giant
    rotated text across the drawing. For centered room labels use:
        text = ms.AddText(name, pt(cx, cy), height)
        text.Alignment = 10                      # acAlignmentMiddleCenter
        text.TextAlignmentPoint = pt(cx, cy)     # MUST be set after Alignment
12. Text height MUST match the drawing's unit scale. If drawing in inches (e.g. 50*12 = 600
    units), use a height around 15-20. If drawing in feet, use 2-3. A height of 1.0 is
    microscopic on large plots.
13. For multi-floor plans, place floors SIDE-BY-SIDE along the X-axis (offset the second floor
    by plot_width + gap), NEVER stacked on the Y-axis — the ground floor often extends further
    than assumed and floors will overlap.
14. Decide the unit system ONCE at the top (e.g. UNITS = 12 for inches) and use it consistently
    for every coordinate, wall thickness, and text height.

SPATIAL REASONING RULES (critical — these prevent geometric nonsense):
15. For rectangular plots, you MUST use orthogonal grid-based subdivisions. All walls MUST be
    axis-aligned (every edge either horizontal or vertical). NEVER default to radial, polar,
    circular, or arc-based room distributions unless the user EXPLICITLY requests a circular
    building.
16. Before writing any coordinates, plan the layout as a grid: compute distinct, non-overlapping
    X-intervals and Y-intervals for each room (bounding boxes). Every room is a rectangle
    [x1, x2] x [y1, y2] where x1 < x2 and y1 < y2, and no two rooms' interiors overlap.
17. Rooms must tile the plot like a mosaic: adjacent rooms share walls (same coordinate for
    the shared edge). Verify that the sum of room widths in each row equals the plot width,
    and the sum of room heights in each column equals the plot depth.
18. Never place a room's center outside the plot boundary, and never let a room extend past
    the plot edges.

MANDATORY GRID-PACKING ALGORITHM:
19. When tasked with floor plans, YOU MUST NOT invent your own coordinates. You must use a
    grid-packing approach: divide the plot_width and plot_depth by the number of required
    rooms to create an orthogonal matrix of coordinates. Calculate text height dynamically
    as room_width * 0.1 and place the text at the exact mathematical center of each
    rectangular room. Copy and adapt this EXACT helper into your script:

    def grid_pack(plot_w, plot_d, rooms_per_row, room_names, color=3):
        \"\"\"Divide the plot into an orthogonal grid of rooms with centered labels.\"\"\"
        room_w = plot_w / rooms_per_row
        room_d = plot_d / ((len(room_names) + rooms_per_row - 1) // rooms_per_row)
        text_h = room_w * 0.1
        for i, name in enumerate(room_names):
            col, row = i % rooms_per_row, i // rooms_per_row
            x1, y1 = col * room_w, row * room_d
            x2, y2 = x1 + room_w, y1 + room_d
            pline = ms.AddPolyline(aDouble(
                x1, y1, 0,  x2, y1, 0,  x2, y2, 0,  x1, y2, 0,  x1, y1, 0))
            pline.Closed = True
            pline.Color = color
            cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0   # exact mathematical center
            txt = ms.AddText(name, pt(cx, cy), text_h)
            txt.Alignment = 10
            txt.TextAlignmentPoint = pt(cx, cy)

    Usage example for a 50x79 ft plot with 7 rooms (3 per row):
        grid_pack(50, 79, 3, ["Living", "Kitchen", "Bath",
                              "BHK1", "BHK2", "BHK3", "BHK4"])
    For irregular room sizes, keep the same principle: derive every coordinate from
    arithmetic on plot dimensions — never from imagination.

PROFESSIONAL DRAFTING RULES (match real architectural drawings, not sketches):
20. DOUBLE-LINE WALLS: Never draw single lines for walls. Always draw an OUTER polyline and an
    INNER polyline offset by the wall thickness (6-9 inches, i.e. 0.5-0.75 ft). Example helper:

    def draw_wall(x1, y1, x2, y2, thickness=0.5):
        \"\"\"Draw a double-line wall between two points.\"\"\"
        if x1 == x2:  # vertical wall
            ms.AddPolyline(aDouble(x1, y1, 0, x2, y2, 0, x2, y2, 0))
            ms.AddLine(pt(x1, y1), pt(x2, y2))
            ms.AddLine(pt(x1 + thickness, y1), pt(x2 + thickness, y2))
            ms.AddLine(pt(x1, y1), pt(x1 + thickness, y1))
            ms.AddLine(pt(x2, y2), pt(x2 + thickness, y2))
        else:         # horizontal wall
            ms.AddLine(pt(x1, y1), pt(x2, y2))
            ms.AddLine(pt(x1, y1 + thickness), pt(x2, y2 + thickness))
            ms.AddLine(pt(x1, y1), pt(x1, y1 + thickness))
            ms.AddLine(pt(x2, y2), pt(x2, y2 + thickness))
    Fill the wall cavity with solid hatching (ms.AddHatch) only if the user requests it.
21. DOOR OPENINGS: Do not draw continuous closed loops for internal rooms. When two connecting
    rooms share a wall, leave a 3-foot gap in the wall coordinates for the doorway. Optionally
    draw the door swing as a simple 90-degree arc (ms.AddArc) plus a straight door leaf line.
22. PROPORTIONAL SIZING: Apply strict logical ratios to room subdivisions. A bathroom/toilet
    must be approximately 20-30% the size of a living hall or bedroom. Kitchens ~40-50% of a
    bedroom. Never make a bathroom larger than the room it serves.
23. CLEAN TEXT ANCHORING: Calculate the absolute mathematical center (X, Y) of each room's
    bounding box and set text height to room_width * 0.15 — readable but never bleeding
    through the walls into neighboring rooms.
24. ORTHOGONAL ENFORCEMENT: Force all coordinate generation to snap to 90-degree angles.
    Reject any polar or radial math for standard room generation.


Here is the mandatory boilerplate you MUST use:

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
acad.prompt("AutoCAD connection ready.\\n")

CRITICAL INSTRUCTION: You must ALWAYS output the complete, ready-to-run Python script 
inside a standard markdown python code block (```python ... ```). Do not explain the code.
"""

RHINO_PROMPT = """
You are an expert architectural AI assistant. Your job is to interact with Rhino 8 via Python.
The execution template already connects to Rhino and exposes the RhinoScript object as `rs`.
You must write scripts that ONLY use the `rs` object (RhinoScript syntax) — do NOT reconnect
to Rhino and do NOT import win32com.

CRITICAL RHINO RULES:
1. Use rs.AddLine(start, end), rs.AddPolyline(points), rs.AddCircle(center, radius), etc.
   Points are plain (x, y, z) tuples or lists — RhinoScript handles them natively.
2. rs.AddPolyline takes a LIST of (x, y, z) tuples: rs.AddPolyline([(0,0,0), (10,0,0), (10,10,0), (0,0,0)])
3. Finish with rs.ZoomExtents() so the user sees the result.
4. Use rs.AddText(text, (x, y, z), height=2.5) for labels.
5. Do not call rs.EnableRedraw(False) without re-enabling it at the end.

CRITICAL INSTRUCTION: You must ALWAYS output the complete, ready-to-run Python script 
inside a standard markdown python code block (```python ... ```). Do not explain the code.
"""

SKETCHUP_PROMPT = """
You are an expert architectural AI assistant. Your job is to interact with SketchUp via Ruby.
The execution template already provides `model` (Sketchup.active_model) and `entities`
(model.active_entities). Do NOT re-open the model.

CRITICAL SKETCHUP RUBY RULES:
1. All lengths are in INCHES by default. For feet use: 50.feet (Ruby on Rails-style Numeric
   extensions are available in SketchUp's Ruby API).
2. Draw with entities.add_line(pt1, pt2), entities.add_face(pts), entities.add_circle(center, normal, radius).
3. Points must be Geom::Point3d.new(x, y, z) — arrays of coordinates also work.
4. Group complex geometry: group = entities.add_group; group.entities.add_face(...) —
   this prevents faces from sticking to each other.
5. Finish with model.active_view.zoom_extents
6. Do NOT require any gems. Pure SketchUp Ruby only.

CRITICAL INSTRUCTION: You must ALWAYS output the complete, ready-to-run Ruby script 
inside a standard markdown ruby code block (```ruby ... ```). Do not explain the code.
"""

SYSTEM_PROMPTS = {"cad": CAD_PROMPT, "rhino": RHINO_PROMPT, "sketchup": SKETCHUP_PROMPT}

def get_ai_response(user_input, target="cad"):
    """Query AI providers via the direct HTTP router (llm_router.py)."""
    return route_llm(user_input, SYSTEM_PROMPTS.get(target, CAD_PROMPT))

def fix_code_with_error(code, traceback_text, target="cad"):
    """Send failing code + its traceback back to the AI for repair."""
    fix_request = f"""The following {target} script failed during execution.

SCRIPT:
```python
{code}
```

ERROR TRACEBACK:
```
{traceback_text}
```

Rewrite the COMPLETE corrected script. Follow all the same rules as before.
Fix the root cause of the error — do not just suppress it. Output only the code block."""

    return route_llm(fix_request, SYSTEM_PROMPTS.get(target, CAD_PROMPT))

def execute_generated_script(target, script_code):
    """Execute generated CAD script in target environment."""
    templates = {"cad": ("cad.py", cad_env), "rhino": ("rhino.py", rhino_env), "sketchup": ("sketchup.rb", sketchup_env)}
    if target not in templates:
        print("[!] Invalid target!")
        return False
    target_file, fresh_template = templates[target]

    try:
        # Reset the template to a clean state so injected code never accumulates
        injected = fresh_template.strip() + "\n\n" + script_code + "\n"
        
        # Write back
        with open(target_file, 'w') as f:
            f.write(injected)
        
        print(f"[+] Injected code into {target_file}")
        
        # Execute
        if target_file.endswith('.rb'):
            subprocess.run(["sketchup.exe", "-RubyStartup", target_file])
        else:
            subprocess.run([sys.executable, target_file])
        
        return True
    except Exception as e:
        print(f"[!] Execution failed: {e}")
        return False

def interactive_cad_agent():
    """Main interactive loop for CAD agent."""
    print("=" * 80)
    print(" ⚡ AEC AI AGENT — Powered by Multi-Model Fallback Chain")
    print("=" * 80)
    print("Commands: 'exit' to quit, or describe your CAD task.")
    print()
    
    while True:
        try:
            user_input = input("📝 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                print("[+] Shutting down AEC AI Agent.")
                break
            
            print("\n[*] Generating script from AI...")
            ai_response = get_ai_response(user_input)
            
            if ai_response is None:
                print("[!] Failed to generate script. Try again.")
                continue
            
            # Extract Python/Ruby code block from response
            code_match = None
            target = "cad"
            
            if "```python" in ai_response:
                code_match = ai_response.split("```python")[1].split("```")[0].strip()
                target = "cad"
            elif "```ruby" in ai_response:
                code_match = ai_response.split("```ruby")[1].split("```")[0].strip()
                target = "sketchup"
            elif "```" in ai_response:
                code_match = ai_response.split("```")[1].split("```")[0].strip()
                target = "cad"
            
            if code_match:
                print("[+] Generated Code:")
                print(code_match)
                print("\n" + "=" * 80)
                
                confirm = input("Execute? (y/n): ").strip().lower()
                if confirm == 'y':
                    execute_generated_script(target, code_match)
            else:
                print("[!] Could not extract code from AI response.")
                print(f"Response: {ai_response[:200]}...")
        
        except KeyboardInterrupt:
            print("\n[+] Interrupted by user.")
            break
        except Exception as e:
            print(f"[!] Error: {e}")

if __name__ == "__main__":
    interactive_cad_agent()
