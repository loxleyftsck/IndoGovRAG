# 🛠️ Recommended VSCode Extensions for IndoGovRAG

**Project:** IndoGovRAG - Indonesian Government RAG System  
**Tech Stack:** Python, RAG, Machine Learning, NLP  
**Date:** 2024-12-17

---

## 🚀 Quick Install (Copy-Paste)

```bash
# Essential Python Extensions (Must-Have)
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.black-formatter
code --install-extension ms-python.flake8

# Testing & Jupyter
code --install-extension ms-toolsai.jupyter
code --install-extension littlefoxteam.vscode-python-test-adapter

# Python Productivity
code --install-extension njpwerner.autodocstring
code --install-extension KevinRose.vsc-python-indent
code --install-extension donjayamanne.python-environment-manager

# Documentation & Markdown
code --install-extension yzhang.markdown-all-in-one
code --install-extension DavidAnson.vscode-markdownlint
code --install-extension bierner.markdown-mermaid

# Git Tools
code --install-extension eamodio.gitlens
code --install-extension mhutchie.git-graph
code --install-extension github.vscode-pull-request-github

# Code Quality
code --install-extension streetsidesoftware.code-spell-checker
code --install-extension usernamehw.errorlens
code --install-extension wayou.vscode-todo-highlight
code --install-extension gruntfuggly.todo-tree

# Productivity
code --install-extension christian-kohler.path-intellisense
code --install-extension oderwat.indent-rainbow
code --install-extension aaron-bond.better-comments
code --install-extension alefragnani.Bookmarks

# Theme & Icons
code --install-extension PKief.material-icon-theme

# AI Assistant
code --install-extension VisualStudioExptTeam.vscodeintellicode
```

---

## 📦 Extensions by Category

### 1. **Python Development** (Essential) ⭐

#### **Python** (`ms-python.python`)
- **Why:** Core Python support
- **Features:** IntelliSense, debugging, linting, testing
- **Priority:** CRITICAL ⚠️

#### **Pylance** (`ms-python.vscode-pylance`)
- **Why:** Fast, feature-rich language server
- **Features:** Type checking, auto-imports, better IntelliSense
- **Priority:** CRITICAL ⚠️

#### **Black Formatter** (`ms-python.black-formatter`)
- **Why:** Code formatting (PEP 8)
- **Features:** Auto-format on save
- **Priority:** HIGH

#### **Flake8** (`ms-python.flake8`)
- **Why:** Linting for code quality
- **Features:** Detect errors, style issues
- **Priority:** HIGH

---

### 2. **Testing & Jupyter** 🧪

#### **Jupyter** (`ms-toolsai.jupyter`)
- **Why:** Notebook support for experiments
- **Features:** Run cells, visualizations
- **Priority:** MEDIUM
- **Use Case:** RAGAS evaluation, data analysis

#### **Python Test Adapter** (`littlefoxteam.vscode-python-test-adapter`)
- **Why:** Visual test runner
- **Features:** Run tests from sidebar
- **Priority:** MEDIUM

---

### 3. **Python Productivity** ⚡

#### **autoDocstring** (`njpwerner.autodocstring`)
- **Why:** Auto-generate docstrings
- **Features:** Google, NumPy, Sphinx styles
- **Priority:** HIGH
- **Shortcut:** `Ctrl+Shift+2` or `Cmd+Shift+2`

#### **Python Indent** (`KevinRose.vsc-python-indent`)
- **Why:** Better indentation behavior
- **Features:** Smart indent after colons
- **Priority:** MEDIUM

#### **Python Environment Manager** (`donjayamanne.python-environment-manager`)
- **Why:** Manage virtual environments
- **Features:** Switch envs easily
- **Priority:** MEDIUM

---

### 4. **Documentation & Markdown** 📚

#### **Markdown All in One** (`yzhang.markdown-all-in-one`)
- **Why:** Complete Markdown tooling
- **Features:** TOC, shortcuts, preview
- **Priority:** HIGH
- **Use Case:** README, docs, reports

#### **Markdown Lint** (`DavidAnson.vscode-markdownlint`)
- **Why:** Markdown style checking
- **Features:** Enforce consistency
- **Priority:** MEDIUM

#### **Mermaid** (`bierner.markdown-mermaid`)
- **Why:** Diagram support
- **Features:** Preview mermaid diagrams
- **Priority:** MEDIUM
- **Use Case:** Architecture diagrams in docs

---

### 5. **Git & Version Control** 🌿

#### **GitLens** (`eamodio.gitlens`)
- **Why:** Supercharge Git
- **Features:** Blame, history, compare
- **Priority:** HIGH ⭐

#### **Git Graph** (`mhutchie.git-graph`)
- **Why:** Visual Git history
- **Features:** Branch visualization
- **Priority:** MEDIUM

#### **GitHub Pull Requests** (`github.vscode-pull-request-github`)
- **Why:** Manage PRs in VSCode
- **Features:** Review, comment, merge
- **Priority:** HIGH

---

### 6. **Code Quality & Debugging** 🐛

#### **Code Spell Checker** (`streetsidesoftware.code-spell-checker`)
- **Why:** Catch typos
- **Features:** Spelling for code/docs
- **Priority:** HIGH
- **Languages:** English, Indonesian (install extension)

#### **Error Lens** (`usernamehw.errorlens`)
- **Why:** Inline error display
- **Features:** See errors without hovering
- **Priority:** HIGH ⭐

#### **TODO Highlight** (`wayou.vscode-todo-highlight`)
- **Why:** Highlight TODO, FIXME
- **Features:** Never miss TODOs
- **Priority:** MEDIUM

#### **TODO Tree** (`gruntfuggly.todo-tree`)
- **Why:** Collect all TODOs
- **Features:** Sidebar view of all TODOs
- **Priority:** MEDIUM

---

### 7. **Productivity & Navigation** 🎯

#### **Path Intellisense** (`christian-kohler.path-intellisense`)
- **Why:** Auto-complete file paths
- **Features:** Fast imports
- **Priority:** HIGH

#### **Indent Rainbow** (`oderwat.indent-rainbow`)
- **Why:** Colorize indentation
- **Features:** Easier to read nested code
- **Priority:** LOW (nice to have)

#### **Better Comments** (`aaron-bond.better-comments`)
- **Why:** Colorful comments
- **Features:** ! for alerts, ? for questions
- **Priority:** MEDIUM

#### **Bookmarks** (`alefragnani.Bookmarks`)
- **Why:** Mark important lines
- **Features:** Quick navigation
- **Priority:** MEDIUM

---

### 8. **Visual & Theme** 🎨

#### **Material Icon Theme** (`PKief.material-icon-theme`)
- **Why:** Beautiful file icons
- **Features:** Recognizable file types
- **Priority:** LOW (aesthetic)

---

### 9. **AI & Intelligence** 🤖

#### **IntelliCode** (`VisualStudioExptTeam.vscodeintellicode`)
- **Why:** AI-assisted coding
- **Features:** Smart suggestions
- **Priority:** MEDIUM

---

## 🎯 Recommended Installation Order

### Phase 1: Essential (Install First) ⚠️
1. Python
2. Pylance
3. Black Formatter
4. Flake8
5. GitLens

### Phase 2: Productivity (Install Second) ⚡
6. autoDocstring
7. Error Lens
8. Path Intellisense
9. Markdown All in One
10. Code Spell Checker

### Phase 3: Nice-to-Have (Install Later) ✨
11. Jupyter
12. Git Graph
13. TODO Tree
14. Better Comments
15. Material Icon Theme

---

## ⚙️ Recommended Settings (settings.json)

```json
{
  // Python
  "python.defaultInterpreterPath": ".venv/Scripts/python.exe",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "88"],
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  
  // Editor
  "editor.rulers": [88],
  "editor.tabSize": 4,
  "editor.insertSpaces": true,
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  
  // Git
  "git.autofetch": true,
  "git.confirmSync": false,
  "gitlens.hovers.currentLine.over": "line",
  
  // Markdown
  "markdown.preview.breaks": true,
  "markdownlint.config": {
    "MD013": false,
    "MD033": false
  },
  
  // Error Lens
  "errorLens.enabledDiagnosticLevels": [
    "error",
    "warning"
  ],
  
  // TODO Highlight
  "todohighlight.keywords": [
    {
      "text": "TODO:",
      "color": "#fff",
      "backgroundColor": "#ffbd2e"
    },
    {
      "text": "FIXME:",
      "color": "#fff",
      "backgroundColor": "#f06292"
    },
    {
      "text": "NOTE:",
      "color": "#fff",
      "backgroundColor": "#64b5f6"
    }
  ]
}
```

---

## 🚀 Quick Setup Script

Create `setup_vscode.ps1`:

```powershell
# Install all recommended extensions at once

Write-Host "Installing VSCode Extensions for IndoGovRAG..." -ForegroundColor Green

# Essential
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.black-formatter
code --install-extension ms-python.flake8

# Testing
code --install-extension ms-toolsai.jupyter
code --install-extension littlefoxteam.vscode-python-test-adapter

# Productivity
code --install-extension njpwerner.autodocstring
code --install-extension KevinRose.vsc-python-indent
code --install-extension donjayamanne.python-environment-manager

# Documentation
code --install-extension yzhang.markdown-all-in-one
code --install-extension DavidAnson.vscode-markdownlint
code --install-extension bierner.markdown-mermaid

# Git
code --install-extension eamodio.gitlens
code --install-extension mhutchie.git-graph
code --install-extension github.vscode-pull-request-github

# Code Quality
code --install-extension streetsidesoftware.code-spell-checker
code --install-extension usernamehw.errorlens
code --install-extension wayou.vscode-todo-highlight
code --install-extension gruntfuggly.todo-tree

# Extras
code --install-extension christian-kohler.path-intellisense
code --install-extension oderwat.indent-rainbow
code --install-extension aaron-bond.better-comments
code --install-extension alefragnani.Bookmarks
code --install-extension PKief.material-icon-theme
code --install-extension VisualStudioExptTeam.vscodeintellicode

Write-Host "Done! Restart VSCode to activate extensions." -ForegroundColor Green
```

Run with:
```bash
powershell -ExecutionPolicy Bypass -File setup_vscode.ps1
```

---

## 🎯 Project-Specific Tips

### For RAG Development
- Use **Jupyter** for RAGAS experiments
- Use **GitLens** to track evaluation changes
- Use **TODO Tree** to track Week 3+ tasks

### For Documentation
- Use **Markdown All in One** for README
- Use **Mermaid** for architecture diagrams
- Use **autoDocstring** for Python docstrings

### For Code Quality
- Enable **Black** format on save
- Use **Error Lens** to catch bugs early
- Run **Flake8** before commits

---

## 📝 Extension Shortcuts

| Extension | Shortcut | Action |
|-----------|----------|--------|
| autoDocstring | `Ctrl+Shift+2` | Generate docstring |
| Markdown Preview | `Ctrl+Shift+V` | Preview markdown |
| Git Graph | `Ctrl+Shift+G` then click icon | Open graph |
| TODO Tree | `Ctrl+Shift+P` → "TODO Tree" | View all TODOs |
| Bookmarks | `Ctrl+Alt+K` | Toggle bookmark |
| Error Lens | Automatic | Inline errors |

---

## ✅ Verification

After installation, verify:

```bash
# Check Python extension
code --list-extensions | Select-String "ms-python.python"

# Check all installed
code --list-extensions
```

---

**Setup Complete!** 🎉  
**Recommended Extensions:** 30+  
**Essential:** 5 (Python, Pylance, Black, Flake8, GitLens)  
**Total Install Time:** ~5 minutes

Restart VSCode to activate all extensions!
