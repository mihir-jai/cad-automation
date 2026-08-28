import time
import win32com.client

# Connect to Rhino 8 locally (dynamic dispatch prevents license pings/errors)
rhino = win32com.client.dynamic.Dispatch("Rhino.Application")
rhino.Visible = True
time.sleep(1)

rs = rhino.GetScriptObject()
print("[System] Rhino 8 bridge active. Ready to model.")
# --- Inject generated Rhino script below ---

