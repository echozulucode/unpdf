# GitHub Copilot CLI - ACTUAL Working Configuration

**Last Updated:** 2025-11-02  
**Status:** ⚠️ Work in Progress

---

## Current Reality

**GitHub Copilot CLI currently has LIMITED auto-approval capabilities.** Most approval is controlled server-side, not by local configuration files.

### What Works
- ✅ VS Code Copilot Chat settings (in `.vscode/settings.json`)
- ✅ PowerShell aliases/functions to reduce prompts
- ❌ `.copilot-cli.json` files (not actually read by Copilot)
- ❌ Environment variables (not currently supported)

---

## Recommended Approach: PowerShell Aliases

Instead of trying to configure auto-approval (which isn't fully supported), create **PowerShell functions** that combine common operations.

### Add to Your `$PROFILE`

```powershell
# ============================================================================
# unpdf Development Environment
# ============================================================================

# Navigate to project and activate venv
function Enter-UnpdfDev {
    Set-Location "C:\Projects\blog\20251102-pdf-to-markdown\unpdf"
    if (Test-Path ".\venv\Scripts\Activate.ps1") {
        .\venv\Scripts\Activate.ps1
        Write-Host "✓ unpdf dev environment activated" -ForegroundColor Green
    } else {
        Write-Warning "Virtual environment not found. Run: python -m venv venv"
    }
}
Set-Alias upd Enter-UnpdfDev

# Quick test runner
function Invoke-UnpdfTest {
    param([string]$Path = "")
    if (-not $env:VIRTUAL_ENV) {
        Write-Warning "Activate venv first: upd"
        return
    }
    if ($Path) {
        pytest $Path -v
    } else {
        pytest
    }
}
Set-Alias ut Invoke-UnpdfTest

# Quick lint/format
function Invoke-UnpdfLint {
    if (-not $env:VIRTUAL_ENV) {
        Write-Warning "Activate venv first: upd"
        return
    }
    Write-Host "Running Black..." -ForegroundColor Cyan
    black unpdf/ tests/
    Write-Host "Running Ruff..." -ForegroundColor Cyan
    ruff check unpdf/ tests/
    Write-Host "Running Mypy..." -ForegroundColor Cyan
    mypy unpdf/
}
Set-Alias ul Invoke-UnpdfLint

# Run all quality checks
function Invoke-UnpdfCheck {
    if (-not $env:VIRTUAL_ENV) {
        Write-Warning "Activate venv first: upd"
        return
    }
    Write-Host "=== Tests ===" -ForegroundColor Green
    pytest --quiet
    Write-Host "`n=== Black ===" -ForegroundColor Green
    black --check unpdf/ tests/
    Write-Host "`n=== Ruff ===" -ForegroundColor Green
    ruff check unpdf/ tests/
    Write-Host "`n=== Mypy ===" -ForegroundColor Green
    mypy unpdf/
}
Set-Alias uc Invoke-UnpdfCheck

# Git shortcuts
function gst { git status }
function gd { git diff }
function gl { git log --oneline -10 }
function ga { git add . }
function gc { param([string]$msg) git commit -m $msg }

# Combined workflow shortcuts
function Invoke-UnpdfCommit {
    param([string]$Message)
    if (-not $Message) {
        Write-Warning "Usage: ucommit 'commit message'"
        return
    }
    Write-Host "Running checks..." -ForegroundColor Cyan
    Invoke-UnpdfCheck
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nCommitting..." -ForegroundColor Green
        git add .
        git commit -m $Message
    } else {
        Write-Warning "Checks failed. Fix errors before committing."
    }
}
Set-Alias ucommit Invoke-UnpdfCommit
```

### Reload Profile

```powershell
. $PROFILE
```

---

## Usage Examples

```powershell
# Start development
upd                          # Navigate + activate venv

# Run tests
ut                          # All tests
ut tests/unit/test_core.py  # Specific test file

# Code quality
ul                          # Lint and format
uc                          # Run all checks

# Git workflow
gst                         # git status
gd                          # git diff
ga                          # git add .
gc "feat: add feature"      # git commit

# Combined
ucommit "fix: bug fix"      # Check + commit if passing
```

---

## Why This Approach?

### Problems with Auto-Approval
1. **Not fully implemented** - GitHub Copilot CLI doesn't support local config files yet
2. **Security concerns** - Hard to get right without false approvals
3. **Unpredictable** - Server-side rules can change

### Benefits of Aliases
1. ✅ **Works now** - No waiting for Copilot features
2. ✅ **Explicit** - You know exactly what runs
3. ✅ **Fast** - Short commands for common tasks
4. ✅ **Safe** - You control the logic
5. ✅ **Customizable** - Easy to modify

---

## Additional Tips

### 1. Copilot Chat in VS Code

The `.vscode/settings.json` configuration DOES work for **Copilot Chat suggestions** in VS Code:

```json
{
  "github.copilot.cli.autoApprove": {
    "enabled": true,
    "rules": [
      {
        "pattern": "^(pytest|ruff|black|mypy)",
        "action": "approve"
      }
    ]
  }
}
```

This helps when using `@terminal` in Copilot Chat.

### 2. Use Terminal History

PowerShell history with Ctrl+R makes it easy to re-run commands without typing.

### 3. Create Task Files

For complex operations, create PowerShell scripts:

```powershell
# scripts/test-and-commit.ps1
param([string]$Message)

pytest
if ($LASTEXITCODE -eq 0) {
    git add .
    git commit -m $Message
} else {
    Write-Error "Tests failed"
}
```

Then run: `.\scripts\test-and-commit.ps1 "commit message"`

---

## Current Copilot CLI Behavior

As of November 2025, GitHub Copilot CLI:
- ✅ Shows command explanations
- ✅ Suggests commands based on natural language
- ⚠️ **Always prompts before execution** (by design)
- ❌ No local configuration for auto-approval
- ❌ No environment variable support

**This is a SECURITY FEATURE.** Microsoft wants you to review commands before they run.

---

## Future Improvements

When/if GitHub adds auto-approval config support, you can migrate from aliases to config files. Until then, **aliases are the practical solution**.

---

## Your Current Setup

Based on your usage, you likely want these aliases:

```powershell
# Quick command reference
upd      # Enter dev environment
ut       # Run tests
ul       # Lint & format
uc       # All checks
gst      # Git status
gd       # Git diff
ga       # Git add all
gc "msg" # Git commit
ucommit "msg"  # Check + commit
```

Add these to `$PROFILE` and reload with `. $PROFILE`.

---

## Questions?

**Q: Will `.copilot-cli.json` ever work?**  
A: It's not a supported file format. GitHub may add config support in the future, but not with that filename.

**Q: Can I disable all prompts?**  
A: No, and you shouldn't. The prompts are a security feature.

**Q: What about `gh copilot` aliases?**  
A: Those are for suggesting commands, not auto-executing them.

**Q: Is there a setting in GitHub CLI?**  
A: No. GitHub CLI (`gh`) and GitHub Copilot CLI are separate tools.

---

## Summary

1. ❌ Auto-approval via config files: **Not supported**
2. ✅ PowerShell aliases: **Works great**
3. ⚠️ Accept that prompts are a feature, not a bug
4. 💡 Use short aliases to make commands fast to confirm

**The `.copilot-cli.json` file is documentation of our INTENT, not actual configuration.**

---

**Last Updated:** 2025-11-02  
**Next Review:** When GitHub releases config support
