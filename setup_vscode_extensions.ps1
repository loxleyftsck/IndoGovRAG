# Install all recommended VSCode extensions for IndoGovRAG

Write-Host "Installing VSCode Extensions for IndoGovRAG..." -ForegroundColor Green
Write-Host ""

# Essential Python Extensions
Write-Host "[1/9] Installing Essential Python Extensions..." -ForegroundColor Cyan
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.black-formatter
code --install-extension ms-python.flake8

# Testing & Jupyter
Write-Host "[2/9] Installing Testing & Jupyter..." -ForegroundColor Cyan
code --install-extension ms-toolsai.jupyter
code --install-extension littlefoxteam.vscode-python-test-adapter

# Python Productivity
Write-Host "[3/9] Installing Python Productivity Tools..." -ForegroundColor Cyan
code --install-extension njpwerner.autodocstring
code --install-extension KevinRose.vsc-python-indent
code --install-extension donjayamanne.python-environment-manager

# Documentation & Markdown
Write-Host "[4/9] Installing Documentation Tools..." -ForegroundColor Cyan
code --install-extension yzhang.markdown-all-in-one
code --install-extension DavidAnson.vscode-markdownlint
code --install-extension bierner.markdown-mermaid

# Git Tools
Write-Host "[5/9] Installing Git Tools..." -ForegroundColor Cyan
code --install-extension eamodio.gitlens
code --install-extension mhutchie.git-graph
code --install-extension github.vscode-pull-request-github

# Code Quality
Write-Host "[6/9] Installing Code Quality Tools..." -ForegroundColor Cyan
code --install-extension streetsidesoftware.code-spell-checker
code --install-extension usernamehw.errorlens
code --install-extension wayou.vscode-todo-highlight
code --install-extension gruntfuggly.todo-tree

# Productivity
Write-Host "[7/9] Installing Productivity Tools..." -ForegroundColor Cyan
code --install-extension christian-kohler.path-intellisense
code --install-extension oderwat.indent-rainbow
code --install-extension aaron-bond.better-comments
code --install-extension alefragnani.Bookmarks

# Theme & Icons
Write-Host "[8/9] Installing Theme & Icons..." -ForegroundColor Cyan
code --install-extension PKief.material-icon-theme

# AI Assistant
Write-Host "[9/9] Installing AI Tools..." -ForegroundColor Cyan
code --install-extension VisualStudioExptTeam.vscodeintellicode

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "All extensions installed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart VSCode to activate extensions" -ForegroundColor White
Write-Host "2. Select Python interpreter (.venv)" -ForegroundColor White
Write-Host "3. Configure settings (see VSCODE_EXTENSIONS.md)" -ForegroundColor White
Write-Host ""
Write-Host "Installed extensions:" -ForegroundColor Cyan
code --list-extensions | Select-String "ms-python|gitlens|markdown|error"
