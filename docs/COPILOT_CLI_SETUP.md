# GitHub Copilot CLI Configuration Guide

**Last Updated:** 2025-11-02  
**Purpose:** Minimize confirmation prompts while maintaining security for unpdf development

---

## Overview

GitHub Copilot CLI can request your approval before executing potentially dangerous commands. This guide configures it to automatically execute safe, common development commands while still protecting against destructive operations.

---

## Configuration Strategy

### ✅ Auto-Approve (Safe Commands)
- Reading files and directories
- Running tests
- Linting and formatting
- Installing dependencies (in virtual environments)
- Git status and diff (read-only)
- Building packages
- Running the application in development mode

### ⚠️ Require Confirmation (Potentially Dangerous)
- Deleting files or directories
- Force-pushing to git
- Installing system-wide packages
- Modifying system configurations
- Running as administrator/sudo
- Publishing to PyPI
- Database operations

---

## Environment Setup

### 1. Create Virtual Environment Configuration

GitHub Copilot CLI respects shell environment variables. Configure your shell to mark virtual environments as safe:

**For PowerShell** (add to `$PROFILE`):

```powershell
# Copilot CLI Configuration for unpdf development
$env:COPILOT_CLI_AUTO_APPROVE = "read,test,lint,build,install_venv"

# Mark this project as a safe development environment
if ($PWD.Path -like "*\unpdf*") {
    $env:UNPDF_DEV_MODE = "true"
}

# Function to activate and configure venv
function Enter-UnpdfDev {
    Set-Location "C:\Projects\blog\20251102-pdf-to-markdown\unpdf"
    if (Test-Path ".\venv\Scripts\Activate.ps1") {
        .\venv\Scripts\Activate.ps1
        Write-Host "unpdf dev environment activated (Copilot CLI configured)" -ForegroundColor Green
    }
}

# Alias for convenience
Set-Alias unpdf-dev Enter-UnpdfDev
```

**For Bash/Zsh** (add to `~/.bashrc` or `~/.zshrc`):

```bash
# Copilot CLI Configuration for unpdf development
export COPILOT_CLI_AUTO_APPROVE="read,test,lint,build,install_venv"

# Mark this project as a safe development environment
if [[ "$PWD" == *"/unpdf"* ]]; then
    export UNPDF_DEV_MODE="true"
fi

# Function to activate and configure venv
unpdf-dev() {
    cd ~/projects/unpdf || return
    if [ -f "./venv/bin/activate" ]; then
        source ./venv/bin/activate
        echo "unpdf dev environment activated (Copilot CLI configured)"
    fi
}
```

### 2. Project-Specific Configuration

Create a `.copilot-cli.json` in the project root:

```json
{
  "version": "1.0",
  "project": "unpdf",
  "auto_approve": {
    "enabled": true,
    "commands": {
      "read": {
        "allowed": [
          "cat", "less", "more", "head", "tail",
          "Get-Content", "Select-String",
          "grep", "find", "ls", "dir", "tree",
          "git status", "git diff", "git log"
        ],
        "description": "Read-only file operations"
      },
      "test": {
        "allowed": [
          "pytest", "python -m pytest",
          "python -m unittest",
          "coverage run", "coverage report"
        ],
        "description": "Running tests"
      },
      "lint": {
        "allowed": [
          "ruff check", "ruff format",
          "black", "flake8", "mypy",
          "pylint", "isort"
        ],
        "description": "Code quality checks"
      },
      "build": {
        "allowed": [
          "python -m build",
          "pip install -e .",
          "python setup.py develop"
        ],
        "description": "Building the package"
      },
      "install_venv": {
        "allowed": [
          "pip install",
          "poetry install",
          "pip install -r requirements.txt"
        ],
        "conditions": [
          "VIRTUAL_ENV is set",
          "Inside project directory"
        ],
        "description": "Installing packages in virtual environment only"
      },
      "run_dev": {
        "allowed": [
          "unpdf",
          "python -m unpdf",
          "python unpdf/cli.py"
        ],
        "description": "Running the application"
      }
    },
    "deny": {
      "patterns": [
        "rm -rf /",
        "Remove-Item -Recurse -Force",
        "git push --force",
        "sudo",
        "Format-Volume",
        "DROP DATABASE",
        "twine upload"
      ],
      "description": "Always require confirmation for these"
    }
  },
  "security": {
    "require_venv": true,
    "allowed_directories": [
      "C:\\Projects\\blog\\20251102-pdf-to-markdown\\unpdf",
      "~/projects/unpdf"
    ],
    "deny_system_modifications": true
  }
}
```

---

## Copilot CLI Command Categories

### Category 1: Always Safe (Auto-Approve)

These commands never modify system state:

```bash
# File reading
cat file.py
Get-Content file.py
less README.md
head -n 20 file.py

# Directory listing
ls -la
Get-ChildItem -Recurse
tree
find . -name "*.py"

# Git read operations
git status
git diff
git log --oneline
git show HEAD

# Search operations
grep -r "pattern" .
Select-String -Pattern "pattern" -Path *.py

# Environment inspection
python --version
pip list
which python
$env:PATH
```

**Copilot CLI Config:** Set `COPILOT_READ_AUTO_APPROVE=true`

### Category 2: Development Operations (Auto-Approve in venv)

Safe when inside activated virtual environment:

```bash
# Installing dependencies
pip install pytest
pip install -r requirements.txt
pip install -e .

# Running tests
pytest
pytest tests/test_extractors.py -v
python -m unittest discover

# Code quality
ruff check .
ruff format .
mypy unpdf/
black unpdf/

# Building
python -m build
pip install -e ".[dev]"
```

**Copilot CLI Config:** Set `COPILOT_VENV_AUTO_APPROVE=true` (only when `VIRTUAL_ENV` is set)

### Category 3: Application Execution (Auto-Approve)

Running the application with test data:

```bash
# CLI execution
unpdf sample.pdf
unpdf --help
python -m unpdf input.pdf -o output.md

# Testing CLI
unpdf tests/fixtures/sample.pdf --verbose
```

**Copilot CLI Config:** Set `COPILOT_APP_RUN_AUTO_APPROVE=true`

### Category 4: Git Operations (Mixed)

**Auto-Approve:**
```bash
git add .
git commit -m "message"
git pull
git checkout -b feature-branch
git push origin branch-name
```

**Require Confirmation:**
```bash
git push --force
git reset --hard
git clean -fd
git rebase -i
```

**Copilot CLI Config:** Set `COPILOT_GIT_SAFE_AUTO_APPROVE=true`

### Category 5: Always Require Confirmation

Never auto-approve these:

```bash
# Destructive file operations
rm -rf /
Remove-Item -Recurse -Force C:\
Format-Volume

# System modifications
sudo anything
chown
chmod 777

# Force operations
git push --force
git push --force-with-lease

# Publishing
twine upload
npm publish
pip upload

# Database operations
DROP DATABASE
DELETE FROM table WHERE 1=1
```

---

## Implementation for GitHub Copilot CLI

### Option 1: Shell Aliases (Recommended)

Create safe command wrappers in your shell profile:

**PowerShell (`$PROFILE`):**

```powershell
# Safe command wrappers for unpdf development
function Invoke-UnpdfTest {
    param([string]$TestPath = "")
    if ($env:VIRTUAL_ENV) {
        if ($TestPath) {
            pytest $TestPath -v
        } else {
            pytest
        }
    } else {
        Write-Warning "Virtual environment not activated. Run 'unpdf-dev' first."
    }
}

function Invoke-UnpdfLint {
    if ($env:VIRTUAL_ENV) {
        ruff check .
        ruff format --check .
        mypy unpdf/
    } else {
        Write-Warning "Virtual environment not activated."
    }
}

function Invoke-UnpdfBuild {
    if ($env:VIRTUAL_ENV) {
        python -m build
    } else {
        Write-Warning "Virtual environment not activated."
    }
}

# Aliases
Set-Alias ut Invoke-UnpdfTest
Set-Alias ul Invoke-UnpdfLint
Set-Alias ub Invoke-UnpdfBuild
```

**Bash/Zsh:**

```bash
# Safe command wrappers for unpdf development
function unpdf-test() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        pytest "${1:-.}" -v
    else
        echo "⚠️  Virtual environment not activated"
        return 1
    fi
}

function unpdf-lint() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        ruff check .
        ruff format --check .
        mypy unpdf/
    else
        echo "⚠️  Virtual environment not activated"
        return 1
    fi
}

function unpdf-build() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        python -m build
    else
        echo "⚠️  Virtual environment not activated"
        return 1
    fi
}

# Aliases
alias ut='unpdf-test'
alias ul='unpdf-lint'
alias ub='unpdf-build'
```

### Option 2: GitHub Copilot Workspace Settings

If using VS Code with Copilot, create `.vscode/settings.json`:

```json
{
  "github.copilot.cli.autoApprove": {
    "enabled": true,
    "rules": [
      {
        "pattern": "^(cat|less|more|head|tail|grep|find|ls|tree)",
        "action": "approve",
        "reason": "Read-only operations"
      },
      {
        "pattern": "^(pytest|python -m pytest|python -m unittest)",
        "action": "approve",
        "reason": "Running tests",
        "conditions": ["virtualenv_active"]
      },
      {
        "pattern": "^(ruff|black|flake8|mypy|pylint)",
        "action": "approve",
        "reason": "Code quality tools"
      },
      {
        "pattern": "^pip install",
        "action": "approve",
        "reason": "Installing in venv",
        "conditions": ["virtualenv_active", "not_sudo"]
      },
      {
        "pattern": "^git (status|diff|log|show)",
        "action": "approve",
        "reason": "Read-only git operations"
      },
      {
        "pattern": "^git (add|commit|pull|push(?! --force))",
        "action": "approve",
        "reason": "Safe git operations"
      },
      {
        "pattern": "^(unpdf|python -m unpdf)",
        "action": "approve",
        "reason": "Running the application"
      },
      {
        "pattern": ".*(rm -rf|Remove-Item.*-Force|sudo|DROP|DELETE FROM).*",
        "action": "deny_auto",
        "reason": "Potentially destructive"
      }
    ]
  }
}
```

### Option 3: Pre-Command Hook Script

Create a `copilot-pre-exec.sh` script:

```bash
#!/bin/bash
# Pre-execution hook for Copilot CLI
# Returns 0 for auto-approve, 1 for confirmation required

COMMAND="$1"

# Check if virtual environment is active
if [[ -z "$VIRTUAL_ENV" ]]; then
    # Outside venv, be more cautious
    case "$COMMAND" in
        cat*|less*|more*|head*|tail*|grep*|find*|ls*|tree*|git\ status*|git\ diff*|git\ log*)
            exit 0  # Auto-approve read operations
            ;;
        *)
            exit 1  # Require confirmation
            ;;
    esac
fi

# Inside venv, auto-approve more commands
case "$COMMAND" in
    # Destructive operations - always confirm
    rm\ -rf*|sudo*|DROP*|DELETE\ FROM*|git\ push\ --force*)
        exit 1
        ;;
    
    # Development operations - auto-approve
    pytest*|python\ -m\ pytest*|ruff*|black*|mypy*|pip\ install*|python\ -m\ build*|unpdf*)
        exit 0
        ;;
    
    # Git safe operations - auto-approve
    git\ add*|git\ commit*|git\ pull*|git\ status*|git\ diff*)
        exit 0
        ;;
    
    # Default - require confirmation
    *)
        exit 1
        ;;
esac
```

Make it executable and configure Copilot:

```bash
chmod +x copilot-pre-exec.sh
export COPILOT_PRE_EXEC_HOOK="$(pwd)/copilot-pre-exec.sh"
```

---

## Security Best Practices

### 1. Never Auto-Approve System-Wide Operations
```bash
# ❌ NEVER auto-approve
sudo pip install package
pip install package  # When outside venv
rm -rf /important/system/path
chown -R user:group /
```

### 2. Always Use Virtual Environments
```bash
# ✅ GOOD - Safe in venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows
pip install unpdf[dev]
```

### 3. Scope Auto-Approval to Project Directory
```bash
# ✅ Only auto-approve when in project directory
if [[ "$PWD" == */unpdf* ]]; then
    COPILOT_AUTO_APPROVE=true
fi
```

### 4. Review Git Operations
```bash
# ✅ Auto-approve
git add .
git commit -m "feat: add feature"
git push origin feature-branch

# ⚠️ Always review
git push --force
git reset --hard HEAD~5
git clean -fd
```

### 5. Never Auto-Approve Publishing
```bash
# ⚠️ ALWAYS require confirmation
twine upload dist/*
python -m build && twine upload dist/*
npm publish
```

---

## Quick Reference: Command Safety Matrix

| Command | Auto-Approve? | Condition |
|---------|---------------|-----------|
| `cat`, `ls`, `grep` | ✅ Yes | Always |
| `git status`, `git diff` | ✅ Yes | Always |
| `pytest`, `ruff` | ✅ Yes | Always |
| `pip install` | ✅ Yes | In venv only |
| `python -m build` | ✅ Yes | In venv only |
| `git add`, `git commit` | ✅ Yes | Always |
| `git push` | ✅ Yes | Not --force |
| `unpdf input.pdf` | ✅ Yes | Always |
| `rm -rf` | ❌ No | Always confirm |
| `sudo` | ❌ No | Always confirm |
| `git push --force` | ❌ No | Always confirm |
| `twine upload` | ❌ No | Always confirm |
| System modifications | ❌ No | Always confirm |

---

## Testing Your Configuration

### 1. Test Read Operations
```bash
# Should auto-approve
cat README.md
ls -la
git status
```

### 2. Test Development Operations (in venv)
```bash
# Activate venv first
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1

# Should auto-approve in venv
pytest
ruff check .
pip install pytest-cov
```

### 3. Test Safety Guards
```bash
# Should ALWAYS require confirmation
rm -rf *
sudo anything
git push --force
```

---

## Troubleshooting

### Issue: Commands Still Prompting Despite Configuration

**Solution:** Check environment variables:
```bash
# PowerShell
$env:COPILOT_AUTO_APPROVE
$env:VIRTUAL_ENV

# Bash/Zsh
echo $COPILOT_AUTO_APPROVE
echo $VIRTUAL_ENV
```

### Issue: Virtual Environment Not Detected

**Solution:** Verify venv activation:
```bash
# PowerShell
Get-Command python | Select-Object Source

# Bash/Zsh
which python
```

Should point to venv directory.

### Issue: Git Operations Require Confirmation

**Solution:** Configure git operations explicitly:
```bash
export COPILOT_GIT_SAFE_AUTO_APPROVE=true
```

---

## Recommended Workflow

### Daily Development Session

```bash
# 1. Navigate to project
cd C:\Projects\blog\20251102-pdf-to-markdown\unpdf

# 2. Activate development environment
unpdf-dev  # Custom function from profile

# 3. Verify configuration
echo "VIRTUAL_ENV: $env:VIRTUAL_ENV"
echo "Auto-approve: $env:COPILOT_AUTO_APPROVE"

# 4. Start development
# All test, lint, and build commands now auto-approved

# 5. When done
deactivate
```

### For New Contributors

```bash
# 1. Clone repository
git clone https://github.com/username/unpdf.git
cd unpdf

# 2. Setup virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Run tests to verify
pytest

# All above commands can be auto-approved safely
```

---

## Summary

**Auto-Approve Safely:**
1. ✅ Read operations (always)
2. ✅ Tests and linting (always)
3. ✅ Package installation (in venv only)
4. ✅ Application execution (always)
5. ✅ Safe git operations (not force-push)

**Always Confirm:**
1. ⚠️ Destructive file operations
2. ⚠️ System-wide installations
3. ⚠️ Force git operations
4. ⚠️ Publishing to PyPI
5. ⚠️ Sudo/admin commands

**Key Principle:** When in doubt, require confirmation. It's better to have one extra prompt than accidentally execute a destructive command.

---

**Last Updated:** 2025-11-02  
**Next Review:** When GitHub Copilot CLI releases new auto-approval features
