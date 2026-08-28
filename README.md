# 📋 CAD Automation Workspace — File Index

**Status**: ✅ Production Ready | **Last Updated**: 2026-08-28

---

## 🎯 Quick Reference

### Essential Entry Points
- **GUI Mode**: `python cad_ui.py` → PyQt6 orchestrator
- **CLI Mode**: `python cad_agent.py` → Interactive AI agent
- **Menu Mode**: `python boot.py` → Tool launcher menu

### Initialize/Reset
- **Setup Templates**: `python build_cad.py` → Create fresh templates

---

## 📁 File Directory

### 🤖 AI & Agent System
| File | Purpose | Lines | Size | Language |
|------|---------|-------|------|----------|
| **cad_agent.py** | Multi-model LLM fallback chain with code execution | 190+ | 7.4 KB | Python 3 |

**Key Features**:
- 16 LLM provider fallback chain (Gemini, Mistral, Groq, Cerebras, Cohere, NVIDIA)
- Timeout handling (15s per request)
- Code extraction from markdown responses
- Template injection system
- Interactive CLI loop

---

### 💻 User Interfaces
| File | Purpose | Lines | Size | Framework |
|------|---------|-------|------|-----------|
| **cad_ui.py** | Desktop GUI for generative CAD | 200+ | 7.3 KB | PyQt6 |
| **boot.py** | CLI menu for launching tools | 40+ | 1.8 KB | Python subprocess |

**cad_ui.py Features**:
- Target software selector (AutoCAD, SketchUp, Rhino)
- Generative prompt input
- Live code editor
- Syntax highlighting (Courier New font)
- One-click execute button
- Dark theme UI

**boot.py Features**:
- Interactive menu system
- Graceful error handling
- File existence checks

---

### 🏗️ Execution Templates
| File | Purpose | Platform | Size | Notes |
|------|---------|----------|------|-------|
| **cad.py** | AutoCAD Python template | 2D CAD | 0.27 KB | Ready for code injection |
| **rhino.py** | Rhino 3D Python template | 3D CAD | 0.35 KB | Ready for code injection |
| **sketchup.rb** | SketchUp Ruby template | 3D BIM | 0.19 KB | Ready for code injection |

**Template System**:
- Pre-configured boilerplate connections
- Injection points marked with comments
- Platform-specific libraries
- Error handling built-in

---

### 🛠️ Builders & Initialization
| File | Purpose | Lines | Size | Trigger |
|------|---------|-------|------|---------|
| **build_cad.py** | Scaffold builder (regenerate templates) | 48 | 1.5 KB | `python build_cad.py` |

**Functions**:
- `scaffold_environments()` - Create fresh templates
- Supports: cad.py, rhino.py, sketchup.rb
- File I/O with UTF-8 encoding

---

### ⚙️ Configuration
| File | Purpose | Format | Size | Contains |
|------|---------|--------|------|----------|
| **config.yaml** | LLM model configuration | YAML | 0.52 KB | Model names, API key references |
| **.env** | Environment variables | dotenv | 0.99 KB | API keys (KEEP SECRET!) |

**config.yaml Structure**:
```yaml
model_list:
  - model_name: "cad-brain"
    litellm_params:
      model: "groq/llama3-70b-8192"
      api_key: "os.environ/GROQ_KEY_1"
  # ... more providers
```

**Required Environment Variables**:
- GEMINI_KEY_1, GEMINI_KEY_2, GEMINI_KEY_3
- MISTRAL_KEY_1, MISTRAL_KEY_2, MISTRAL_KEY_3
- GROQ_KEY_1, GROQ_KEY_2, GROQ_KEY_3
- CEREBRAS_KEY_1, CEREBRAS_KEY_2, CEREBRAS_KEY_3
- COHERE_KEY_1, COHERE_KEY_2, COHERE_KEY_3
- NVIDIA_KEY_1

---

### 📖 Documentation
| File | Purpose | Format | Size |
|------|---------|--------|------|
| **CLEANUP_REPORT.md** | Detailed cleanup analysis | Markdown | 5.88 KB |
| **FINAL_SUMMARY.md** | Comprehensive project summary | Markdown | 6.5+ KB |
| **README.md** (this file) | File index & quick reference | Markdown | This |

---

## 🔄 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INPUT LAYER                         │
├─────────────────────────────────────────────────────────────┤
│  cad_ui.py (GUI)           boot.py (CLI)     cad_agent.py   │
│  └─ PyQt6 interface        └─ Menu system    └─ Prompt      │
└────────────┬────────────────────┬──────────────────┬─────────┘
             │                    │                  │
             v                    v                  v
┌─────────────────────────────────────────────────────────────┐
│                   AI AGENT LAYER                             │
├─────────────────────────────────────────────────────────────┤
│ cad_agent.py (Multi-Model Fallback Chain)                   │
│ - 16 LLM providers                                           │
│ - Timeout: 15s per request                                  │
│ - Code extraction from markdown                             │
└────────────┬─────────────────────────────────────────────────┘
             │
             v
┌─────────────────────────────────────────────────────────────┐
│                 TEMPLATE INJECTION LAYER                     │
├─────────────────────────────────────────────────────────────┤
│ cad.py (AutoCAD) | rhino.py (Rhino) | sketchup.rb (SketchUp) │
│ └─ AI code injected into templates                          │
└────────────┬─────────────────────────────────────────────────┘
             │
             v
┌─────────────────────────────────────────────────────────────┐
│                  EXECUTION LAYER                             │
├─────────────────────────────────────────────────────────────┤
│ subprocess → Python Interpreter OR Ruby Interpreter         │
│            → AutoCAD/Rhino/SketchUp Live                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎮 Usage Workflows

### Workflow 1: GUI (Recommended for New Users)
```
1. python cad_ui.py
2. Select target software (AutoCAD/SketchUp/Rhino)
3. Enter prompt: "Draw a 5000x5000 floor plan"
4. Click "GENERATE SCRIPT"
5. Review generated code
6. Click "BUILD IN SOFTWARE"
7. Watch geometry appear in CAD software
```

### Workflow 2: CLI Agent (Power Users)
```
1. python cad_agent.py
2. Type: "Create a 3D box with dimensions 1000, 1500, 2000 in Rhino"
3. View generated Python code
4. Press 'y' to execute
5. Script runs in Rhino
```

### Workflow 3: Menu System
```
1. python boot.py
2. Select 'cad', 'sketchup', 'rhino', or 'all'
3. Launches template directly
```

### Workflow 4: Direct Template Execution
```
1. Edit cad.py / rhino.py / sketchup.rb directly
2. python cad.py (or rhino.py)
3. Code executes in target software
```

---

## 🔧 Dependencies

### Python Packages
```
litellm              # Multi-model LLM abstraction
pyautocad            # AutoCAD COM bridge
PyQt6                # GUI framework
python-dotenv        # Environment variable management
win32com             # Windows COM library (for Rhino)
```

### External Software
```
AutoCAD 2020+        # For cad.py execution
Rhino 8+             # For rhino.py execution
SketchUp 2024+       # For sketchup.rb execution
Python 3.8+          # Runtime
Ruby (bundled)       # For sketchup.rb
```

### Required API Keys
- Gemini (Google)
- Mistral AI
- Groq
- Cerebras
- Cohere
- NVIDIA NIM

---

## 🚨 Common Issues & Fixes

### "All AI providers failed"
- **Cause**: All API keys invalid/expired
- **Fix**: Update .env file with valid API keys

### "pyautocad not found"
- **Cause**: Package not installed
- **Fix**: `pip install pyautocad`

### "Rhino connection failed"
- **Cause**: Rhino not running or COM server unavailable
- **Fix**: Launch Rhino first, then run script

### "SketchUp not found"
- **Cause**: SketchUp path incorrect
- **Fix**: Update SKETCHUP_EXE path in boot.py

---

## 📊 File Dependencies Map

```
cad_ui.py
├── → PyQt6 (GUI)
├── → subprocess (execution)
└── → cad.py / rhino.py / sketchup.rb (templates)

cad_agent.py
├── → litellm (LLM)
├── → config.yaml (models)
├── → .env (API keys)
└── → cad.py / rhino.py / sketchup.rb (templates)

boot.py
├── → subprocess
└── → cad.py / rhino.py / sketchup.rb

build_cad.py
└── → (generates) cad.py / rhino.py / sketchup.rb

cad.py / rhino.py / sketchup.rb
└── → (require) pyautocad / win32com / SketchUp Ruby API
```

---

## ✅ Validation Checklist

- [x] All Python files pass syntax validation
- [x] No duplicate code across files
- [x] All incomplete files finished
- [x] All dependencies documented
- [x] All usage workflows explained
- [x] All integration points verified
- [x] Error handling implemented
- [x] Documentation complete

---

## 📞 Support

### For GUI Issues
Check `cad_ui.py` PyQt6 styling and signal connections

### For LLM Issues
Check `cad_agent.py` fallback chain and API keys in `.env`

### For Template Issues
Regenerate with `python build_cad.py`

### For Execution Issues
Check target software is running and COM ports available

---

**Status**: ✅ Production Ready  
**Last Validated**: 2026-08-28  
**Cleanup Version**: 2.0
