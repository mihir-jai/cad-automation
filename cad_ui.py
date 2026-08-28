import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QPushButton, QLabel, QRadioButton, QButtonGroup, QFrame, QSplitter
)
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from cad_agent import get_ai_response

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
        self.setMinimumSize(1000, 650)
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

        self.worker = AIWorker(prompt)
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
        """Replaces magic.py logic. Saves the code to a file and launches the subprocess."""
        target = self.btn_group.checkedButton().objectName()
        code = self.code_editor.toPlainText().strip()
        
        if not code:
            return

        # Guard: refuse to run raw prompt text (no code structure) as a script
        if target != "sketchup" and not any(
            token in code for token in ("import", "def ", "print", "=", "(", "puts")
        ):
            self.code_editor.setPlainText(
                "# [!] That doesn't look like generated code.\n"
                "# Click 'GENERATE SCRIPT' first, then 'BUILD IN SOFTWARE'."
            )
            return

        if target == "sketchup":
            with open("run_sketchup.rb", "w") as f: f.write(code)
            # Update path to match your installation
            subprocess.Popen([r"C:\Program Files\SketchUp\SketchUp 2025\SketchUp.exe", "-RubyStartup", "run_sketchup.rb"])
        
        elif target == "rhino":
            with open("run_rhino.py", "w") as f: f.write(code)
            subprocess.Popen([sys.executable, "run_rhino.py"])
            
        elif target == "cad":
            with open("run_cad.py", "w") as f: f.write(code)
            subprocess.Popen([sys.executable, "run_cad.py"])

class AIWorker(QThread):
    """Runs the LLM fallback chain off the UI thread."""
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            response = get_ai_response(self.prompt)
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