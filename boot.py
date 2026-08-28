import subprocess
import sys
import os

# Update if your SketchUp is on a different drive
SKETCHUP_EXE = r"C:\Program Files\SketchUp\SketchUp 2025\SketchUp.exe"

def boot_software(target):
    if target == "cad":
        if os.path.exists("cad.py"):
            print("🚀 Launching AutoCAD via cad.py...")
            subprocess.run([sys.executable, "cad.py"])
        else:
            print("[!] cad.py not found. Run build_cad.py first.")
            
    elif target == "sketchup":
        if os.path.exists("sketchup.rb"):
            print("🚀 Launching SketchUp via sketchup.rb...")
            subprocess.run([SKETCHUP_EXE, "-RubyStartup", "sketchup.rb"])
        else:
            print("[!] sketchup.rb not found.")
            
    elif target == "rhino":
        if os.path.exists("rhino.py"):
            print("🚀 Launching Rhino via rhino.py...")
            subprocess.run([sys.executable, "rhino.py"])
        else:
            print("[!] rhino.py not found.")
            
    elif target == "all":
        print("🚀 Executing Full AEC Pipeline...")
        boot_software("cad")
        boot_software("sketchup")
        boot_software("rhino")

if __name__ == "__main__":
    print("==================================================")
    print(" 🎛️ REAL-TIME AEC SWITCHBOARD ACTIVE")
    print("==================================================")
    print("Commands: 'cad', 'sketchup', 'rhino', 'all', or 'exit'")
    
    while True:
        cmd = input("\nBoot> ").strip().lower()
        if cmd in ['exit', 'quit']:
            break
        elif cmd in ['cad', 'sketchup', 'rhino', 'all']:
            boot_software(cmd)
        else:
            print("[!] Unknown command. Try 'cad', 'sketchup', or 'rhino'.")