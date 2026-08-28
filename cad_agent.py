import sys
import subprocess

from build_cad import cad_env, rhino_env, sketchup_env
from llm_router import get_ai_response as route_llm

SYSTEM_PROMPT = """
You are an expert architectural AI assistant. Your job is to interact with AutoCAD via Python. 
You can either DRAW new geometry, or READ/ANALYZE existing geometry based on the user's request.

To do this, you must write Python scripts using pyautocad, win32com, and csv (if exporting).

CRITICAL COM STABILITY RULES:
1. NEVER call `acad.model` repeatedly. Cache it once at the top: `ms = acad.model`.
2. Always draw using the cached `ms` variable: `ms.AddLine(p1, p2)`, `ms.AddCircle(center, radius)`, etc.
3. Finish every script with `acad.app.ZoomExtents()` so the user can see what was drawn.
4. NEVER attempt to set `Lineweight` or `Linetype` (like 'Dashed'). Instead, use `.Color` (e.g., 1=Red, 2=Yellow, 3=Green).

Here is the mandatory boilerplate you MUST use:

import time
from pyautocad import Autocad, APoint

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

def get_ai_response(user_input):
    """Query AI providers via the direct HTTP router (llm_router.py)."""
    return route_llm(user_input, SYSTEM_PROMPT)

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
