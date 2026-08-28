import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QRadioButton, QButtonGroup, QFrame, QSplitter,
    QFileDialog, QMessageBox
)
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QProcess

from cad_agent import get_ai_response, fix_code_with_error
from build_cad import cad_env, rhino_env, sketchup_env

SKETCHUP_EXE = r"C:\Program Files\SketchUp\SketchUp 2025\SketchUp.exe"

# --- Color Palette ---
BG_COLOR = "#0a0e14"
PANEL_COLOR = "#11161d"
BORDER_COLOR = "#1f2937"
ACCENT_COLOR = "#00d4ff"
TEXT_COLOR = "#e5e7eb"
MUTED_TEXT = "#6b7280"

class AEC_Orchestrator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AEC Orchestrator — Generative CAD Bridge")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet(f"background-color: {BG_COLOR}; color: {TEXT_COLOR};")

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # --- HEADER ---
        header = QLabel("◈ AEC ORCHESTRATOR")
        header.setFont(QFont("Courier New", 12, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {ACCENT_COLOR}; padding-bottom: 5px;")
        main_layout.addWidget(header)

        # --- SPLITTER (Left: Input/Controls, Right: Code/Output) ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # ==========================================
        # LEFT PANEL (Controls & Prompt)
        # ==========================================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)

        # 1. Target Software Selector
        target_label = QLabel("TARGET SOFTWARE:")
        target_label.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        left_layout.addWidget(target_label)

        self.btn_group = QButtonGroup(self)
        targets = [("AutoCAD (2D)", "cad"), ("SketchUp (Ruby)", "sketchup"), ("Rhino 8 (3D)", "rhino")]

        radio_layout = QHBoxLayout()
        for text, value in targets:
            rb = QRadioButton(text)
            rb.setFont(QFont("Courier New", 9))
            rb.setObjectName(value)
            if value == "cad":
                rb.setChecked(True)
            self.btn_group.addButton(rb)
            radio_layout.addWidget(rb)
        left_layout.addLayout(radio_layout)

        # 2. Natural Language Prompt
        left_layout.addSpacing(15)
        prompt_label = QLabel("GENERATIVE PROMPT:")
        prompt_label.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        left_layout.addWidget(prompt_label)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("e.g., Draw a 5000x5000 floor plan with a 1000x1000 square inside it...")
        self.prompt_input.setFont(QFont("Courier New", 10))
        self.prompt_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {PANEL_COLOR};
                border: 1px solid {BORDER_COLOR};
                border-radius: 5px;
                padding: 10px;
            }}
            QTextEdit:focus {{ border: 1px solid {ACCENT_COLOR}; }}
        """)
        left_layout.addWidget(self.prompt_input)

        # 3. Generate Button
        self.btn_generate = QPushButton("▸ GENERATE SCRIPT")
        self.btn_generate.setFixedHeight(40)
        self.btn_generate.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        self.btn_generate.setStyleSheet(f"""
            QPushButton {{
                background-color: {PANEL_COLOR}; color: {ACCENT_COLOR};
                border: 1px solid {ACCENT_COLOR}; border-radius: 5px;
            }}
            QPushButton:hover {{ background-color: #001f2e; }}
        """)
        self.btn_generate.clicked.connect(self.simulate_ai_generation)
        left_layout.addWidget(self.btn_generate)

        # 4. Script File Actions (Save / Load)
        file_btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("💾 SAVE SCRIPT")
        self.btn_load = QPushButton("📂 LOAD SCRIPT")
        for b in (self.btn_save, self.btn_load):
            b.setFixedHeight(32)
            b.setFont(QFont("Courier New", 9))
            b.setStyleSheet(f"""
                QPushButton {{
                    background-color: {PANEL_COLOR}; color: {TEXT_COLOR};
                    border: 1px solid {BORDER_COLOR}; border-radius: 5px;
                }}
                QPushButton:hover {{ border: 1px solid {ACCENT_COLOR}; }}
            """)
        self.btn_save.clicked.connect(self.save_script)
        self.btn_load.clicked.connect(self.load_script)
        file_btn_layout.addWidget(self.btn_save)
        file_btn_layout.addWidget(self.btn_load)
        left_layout.addLayout(file_btn_layout)

        splitter.addWidget(left_panel)

        # ==========================================
        # RIGHT PANEL (Code Editor & Execution)
        # ==========================================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)

        # 1. Code Editor
        code_label = QLabel("GENERATED SCRIPT (Editable):")
        code_label.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        right_layout.addWidget(code_label)

        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Courier New", 9))
        self.code_editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {PANEL_COLOR}; color: #a6accd;
                border: 1px solid {BORDER_COLOR}; border-radius: 5px;
                padding: 10px;
            }}
        """)
        right_layout.addWidget(self.code_editor)

        # 2. Execute Button
        self.btn_execute = QPushButton("⚡ BUILD IN SOFTWARE")
        self.btn_execute.setFixedHeight(40)
        self.btn_execute.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        self.btn_execute.setStyleSheet(f"""
            QPushButton {{
                background-color: #00aa55; color: #ffffff;
                border: none; border-radius: 5px;
            }}
            QPushButton:hover {{ background-color: #00c860; }}
        """)
        self.btn_execute.clicked.connect(self.execute_script)
        right_layout.addWidget(self.btn_execute)

        # 2b. Abort Button (kill a frozen CAD execution)
        self.btn_stop = QPushButton("■ ABORT EXECUTION")
        self.btn_stop.setFixedHeight(32)
        self.btn_stop.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        self.btn_stop.setStyleSheet(f"""
            QPushButton {{
                background-color: {PANEL_COLOR}; color: #ff5555;
                border: 1px solid #ff5555; border-radius: 5px;
            }}
            QPushButton:hover {{ background-color: #2a0a0a; }}
        """)
        self.btn_stop.clicked.connect(self.abort_execution)
        self.btn_stop.setEnabled(False)
        right_layout.addWidget(self.btn_stop)

        # 2c. Auto-Fix & Retry Button (appears useful after a failed build)
        self.btn_autofix = QPushButton("🔧 AUTO-FIX & RETRY")
        self.btn_autofix.setFixedHeight(32)
        self.btn_autofix.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        self.btn_autofix.setStyleSheet(f"""
            QPushButton {{
                background-color: {PANEL_COLOR}; color: #ffaa00;
                border: 1px solid #ffaa00; border-radius: 5px;
            }}
            QPushButton:hover {{ background-color: #2a1f00; }}
        """)
        self.btn_autofix.clicked.connect(self.autofix_and_retry)
        self.btn_autofix.setEnabled(False)
        right_layout.addWidget(self.btn_autofix)

        # 3. Execution Output Console
        output_label = QLabel("EXECUTION OUTPUT:")
        output_label.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        right_layout.addWidget(output_label)

        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setFont(QFont("Courier New", 9))
        self.output_console.setStyleSheet(f"""
            QTextEdit {{
                background-color: #05080c; color: #9ca3af;
                border: 1px solid {BORDER_COLOR}; border-radius: 5px;
                padding: 10px;
            }}
        """)
        right_layout.addWidget(self.output_console)

        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])

    # --- Logic ---
    def simulate_ai_generation(self):
        """Query the real LLM fallback chain (cad_agent) in a background thread."""
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            self.code_editor.setPlainText("# [!] Enter a prompt first.")
            return

        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("◌ GENERATING...")
        self.code_editor.setPlainText("[*] Asking AI models (fallback chain active)...")

        target = self.btn_group.checkedButton().objectName()
        self.worker = AIWorker(prompt, target)
        self.worker.finished_signal.connect(self.on_ai_finished)
        self.worker.error_signal.connect(self.on_ai_error)
        self.worker.start()

    def on_ai_finished(self, response):
        """Extract the code block from the AI response and show it in the editor."""
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("▸ GENERATE SCRIPT")

        code = None
        if "```python" in response:
            code = response.split("```python")[1].split("```")[0].strip()
        elif "```ruby" in response:
            code = response.split("```ruby")[1].split("```")[0].strip()
        elif "```" in response:
            code = response.split("```")[1].split("```")[0].strip()

        if code:
            self.code_editor.setPlainText(code)
        else:
            self.code_editor.setPlainText(f"# [!] Could not extract code from AI response:\n# {response[:300]}")

    def on_ai_error(self, error):
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("▸ GENERATE SCRIPT")
        self.code_editor.setPlainText(f"# [!] AI generation failed:\n# {error}")

    def execute_script(self):
        """Save the code and run it, streaming output into the console."""
        target = self.btn_group.checkedButton().objectName()
        code = self.code_editor.toPlainText().strip()

        if not code:
            return

        # Guard: refuse to run raw prompt text (no code structure) as a script
        if not any(token in code for token in ("import", "def ", "print", "puts", "entities", "model", "rs.", "d.")):
            self.output_console.setPlainText(
                "[!] That doesn't look like generated code.\n"
                "    Click 'GENERATE SCRIPT' first, then 'BUILD IN SOFTWARE'."
            )
            return

        self.btn_execute.setEnabled(False)
        self.btn_execute.setText("◌ RUNNING...")
        self.output_console.setPlainText(f"[*] Building in {target.upper()}...\n")

        script_file = {"cad": "run_cad.py", "rhino": "run_rhino.py", "sketchup": "run_sketchup.rb"}[target]

        # Prepend the fresh execution template (connection boilerplate +
        # ArchitecturalDrafter class) so `d`, `ms`, and `acad` always exist —
        # unless the editor code is already a complete standalone script.
        templates = {"cad": cad_env, "rhino": rhino_env, "sketchup": sketchup_env}
        standalone_markers = {
            "cad": ("class ArchitecturalDrafter", "Autocad("),
            "rhino": ("win32com", "Rhino.Application"),
            "sketchup": ("Sketchup.active_model",),
        }
        if not any(marker in code for marker in standalone_markers[target]):
            code = templates[target].strip() + "\n\n" + code + "\n"

        with open(script_file, "w", encoding="utf-8") as f:
            f.write(code)

        if target == "sketchup":
            # SketchUp must be launched as an app with the Ruby startup file
            try:
                subprocess.Popen([SKETCHUP_EXE, "-RubyStartup", script_file])
                self.output_console.append("[+] SketchUp launched with script. Check the SketchUp window.")
            except Exception as e:
                self.output_console.append(f"[!] Failed to launch SketchUp: {e}\n(Update SKETCHUP_EXE path if needed)")
            self._reset_execute_button()
            return

        # Python targets (cad / rhino): run via QProcess, stream output live
        self.runner = QProcess(self)
        self.runner.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.runner.readyReadStandardOutput.connect(self._on_runner_output)
        self.runner.finished.connect(self._on_runner_finished)
        self.runner.start(sys.executable, [script_file])
        self.btn_stop.setEnabled(True)
        self._last_code = code
        self._last_target = target
        self._last_output = ""

    def abort_execution(self):
        """Kill a frozen CAD subprocess."""
        if getattr(self, "runner", None) and self.runner.state() != QProcess.ProcessState.NotRunning:
            self.runner.kill()
            self.output_console.append("\n[!] Execution aborted by user.")
        self.btn_stop.setEnabled(False)

    def save_script(self):
        """Save the generated script to a user-chosen file."""
        target = self.btn_group.checkedButton().objectName()
        default_ext = {"cad": ".py", "rhino": ".py", "sketchup": ".rb"}[target]
        path, _ = QFileDialog.getSaveFileName(self, "Save Script", f"script{default_ext}")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.code_editor.toPlainText())
            self.output_console.append(f"[+] Script saved to {path}")

    def load_script(self):
        """Load a previously saved script into the editor."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Script", "", "CAD Scripts (*.py *.rb);;All Files (*)"
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.code_editor.setPlainText(f.read())
            self.output_console.append(f"[+] Script loaded from {path}")

    def _on_runner_output(self):
        text = bytes(self.runner.readAllStandardOutput()).decode(errors="replace")
        self.output_console.append(text)
        self._last_output += text

    def _on_runner_finished(self, exit_code, _status):
        if exit_code == 0:
            self.output_console.append("\n[+] Build finished successfully.")
            self.btn_autofix.setEnabled(False)
        else:
            self.output_console.append(
                f"\n[!] Build failed with exit code {exit_code}. "
                "Click 'AUTO-FIX & RETRY' to let the AI repair the script."
            )
            self.btn_autofix.setEnabled(True)
        self._reset_execute_button()

    def autofix_and_retry(self):
        """Send the failing code + traceback to the AI, then re-run the fix."""
        if not getattr(self, "_last_code", None):
            return

        self.btn_autofix.setEnabled(False)
        self.btn_autofix.setText("◌ FIXING...")
        self.output_console.append("\n[*] Sending error to AI for repair...")

        self.fixer = FixWorker(self._last_code, self._last_output[-3000:], self._last_target)
        self.fixer.finished_signal.connect(self._on_fix_finished)
        self.fixer.error_signal.connect(self._on_fix_error)
        self.fixer.start()

    def _on_fix_finished(self, fixed_code):
        self.btn_autofix.setText("🔧 AUTO-FIX & RETRY")
        self.code_editor.setPlainText(fixed_code)
        self.output_console.append("[+] AI produced a corrected script. Re-running...\n")
        self.execute_script()

    def _on_fix_error(self, error):
        self.btn_autofix.setText("🔧 AUTO-FIX & RETRY")
        self.btn_autofix.setEnabled(True)
        self.output_console.append(f"[!] Auto-fix failed: {error}")

    def _reset_execute_button(self):
        self.btn_execute.setEnabled(True)
        self.btn_execute.setText("⚡ BUILD IN SOFTWARE")
        self.btn_stop.setEnabled(False)

class FixWorker(QThread):
    """Runs the AI auto-repair off the UI thread."""
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, code, traceback_text, target):
        super().__init__()
        self.code = code
        self.traceback_text = traceback_text
        self.target = target

    def run(self):
        try:
            response = fix_code_with_error(self.code, self.traceback_text, self.target)
            if response is None:
                self.error_signal.emit("All AI providers failed.")
                return
            code = None
            if "```python" in response:
                code = response.split("```python")[1].split("```")[0].strip()
            elif "```ruby" in response:
                code = response.split("```ruby")[1].split("```")[0].strip()
            elif "```" in response:
                code = response.split("```")[1].split("```")[0].strip()
            if code:
                self.finished_signal.emit(code)
            else:
                self.error_signal.emit("Could not extract code from AI response.")
        except Exception as e:
            self.error_signal.emit(str(e))


class AIWorker(QThread):
    """Runs the LLM fallback chain off the UI thread."""
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, prompt, target="cad"):
        super().__init__()
        self.prompt = prompt
        self.target = target

    def run(self):
        try:
            response = get_ai_response(self.prompt, self.target)
            if response is None:
                self.error_signal.emit("All AI providers failed.")
            else:
                self.finished_signal.emit(response)
        except Exception as e:
            self.error_signal.emit(str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AEC_Orchestrator()
    window.show()
    sys.exit(app.exec())