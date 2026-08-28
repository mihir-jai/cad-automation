import os
import sys
import subprocess

from build_cad import cad_env, rhino_env, sketchup_env
from llm_router import get_ai_response as route_llm

STANDARDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aec_drafting_standards.md")

def load_drafting_standards():
    """Load the permanent architectural education (Neufert + NBC rules)."""
    try:
        with open(STANDARDS_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"[!] Warning: {STANDARDS_FILE} not found — drafting standards disabled.")
        return ""

CAD_PROMPT = """
You are an expert architectural AI assistant. Your job is to interact with AutoCAD via Python.
You can either DRAW new geometry, or READ/ANALYZE existing geometry based on the user's request.

The cad.py execution template provides an `ArchitecturalDrafter` instance named `d` that wraps
ALL AutoCAD geometry math. The AutoCAD connection, model cache (`ms = acad.model`), and the
`ArchitecturalDrafter(acad, ms)` object are already set up for you.

CRITICAL COM STABILITY RULES:
1. NEVER call `acad.model` repeatedly — it is already cached as `ms`. Use the prebuilt `d`.
2. NEVER draw raw geometry. DO NOT call ms.AddLine, ms.AddPolyline, ms.AddArc, ms.AddText,
   or any other ms.Add* method directly. The geometry math is error-prone; you WILL crash.
3. You MUST only use the provided ArchitecturalDrafter methods:
   - d.draw_wall(x1, y1, x2, y2, thickness=4.5)     — closed double-line wall
   - d.draw_room(x_min, y_min, x_max, y_max, name)    — 4 walls + centered label
   - d.draw_room_text(name, x_min, y_min, x_max, y_max)
   - d.draw_door(x, y, rotation=0, door_width=36)    — 36" gap + 90° swing arc + leaf
   - d.draw_plot_boundary(width, depth, thickness=9)
4. For multi-floor plans, place floors SIDE-BY-SIDE along the X-axis. Never stack on Y.
5. Finish EVERY script with `acad.app.ZoomExtents()` so the user can see the result.
6. NEVER attempt to set `Lineweight` or `Linetype`. Use `.Color` (handled by the helpers).
7. PREFER a simple linear script. If you define your own helper functions, every call site
   MUST match the function signature exactly. Double-check before finishing.

MANDATORY DRAFTING BEHAVIOR:
- After drawing room boundaries with d.draw_room(), you MUST call d.draw_door() to create
  connecting passageways between the Living Room, Kitchen, Bedrooms, and Bathrooms.
- One door per habitable room minimum.
- draw_door rotation: 0 = door on a horizontal wall, 90 = vertical wall.


Here is the mandatory boilerplate. The AutoCAD connection and the `d = ArchitecturalDrafter()`
object are ALREADY in the template — do NOT repeat them. Your script should ONLY contain the
room-drawing logic below the injection point:

    # === your generated room layout ===
    # e.g. d.draw_plot_boundary(50, 79)
    #      d.draw_room(0, 0, 25, 20, "Living")
    #      d.draw_door(25, 10, rotation=90)  # door on the shared wall
    #      acad.app.ZoomExtents()

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
    """Query AI providers via the direct HTTP router (llm_router.py).
    The aec_drafting_standards.md knowledge base is appended to every request."""
    standards = load_drafting_standards()
    base_prompt = SYSTEM_PROMPTS.get(target, CAD_PROMPT)
    if standards:
        base_prompt += (
            "\n\n=== MANDATORY ARCHITECTURAL STANDARDS (Neufert + NBC 2016) ===\n"
            "You MUST apply these dimensions and rules to every floor plan you draw:\n\n"
            + standards
        )
    return route_llm(user_input, base_prompt)

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

    standards = load_drafting_standards()
    if standards:
        fix_request += (
            "\n\n=== MANDATORY ARCHITECTURAL STANDARDS (Neufert + NBC 2016) ===\n" + standards
        )
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
