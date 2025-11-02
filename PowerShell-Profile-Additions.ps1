# ============================================================================
# Add this to your PowerShell $PROFILE
# Location: notepad $PROFILE
# ============================================================================

# unpdf Development Environment
# ============================================================================

function Enter-UnpdfDev {
    <#
    .SYNOPSIS
    Navigate to unpdf project and activate virtual environment.
    #>
    Set-Location "C:\Projects\blog\20251102-pdf-to-markdown\unpdf"
    if (Test-Path ".\venv\Scripts\Activate.ps1") {
        .\venv\Scripts\Activate.ps1
        Write-Host "✓ unpdf dev environment activated" -ForegroundColor Green
        Write-Host "  Commands: ut (test), ul (lint), uc (check all)" -ForegroundColor Cyan
    } else {
        Write-Warning "Virtual environment not found. Run: python -m venv venv"
    }
}
Set-Alias upd Enter-UnpdfDev

function Invoke-UnpdfTest {
    <#
    .SYNOPSIS
    Run pytest tests for unpdf.
    .PARAMETER Path
    Optional path to specific test file or directory.
    #>
    param([string]$Path = "")
    
    if (-not $env:VIRTUAL_ENV) {
        Write-Warning "Activate virtual environment first: upd"
        return
    }
    
    if ($Path) {
        pytest $Path -v
    } else {
        pytest
    }
}
Set-Alias ut Invoke-UnpdfTest

function Invoke-UnpdfLint {
    <#
    .SYNOPSIS
    Run code formatters and linters.
    #>
    if (-not $env:VIRTUAL_ENV) {
        Write-Warning "Activate virtual environment first: upd"
        return
    }
    
    Write-Host "=== Black (formatting) ===" -ForegroundColor Cyan
    black unpdf/ tests/
    
    Write-Host "`n=== Ruff (linting) ===" -ForegroundColor Cyan
    ruff check unpdf/ tests/
    
    Write-Host "`n=== Mypy (type checking) ===" -ForegroundColor Cyan
    mypy unpdf/
    
    Write-Host "`n✓ Linting complete" -ForegroundColor Green
}
Set-Alias ul Invoke-UnpdfLint

function Invoke-UnpdfCheck {
    <#
    .SYNOPSIS
    Run all quality checks (tests, formatting, linting).
    #>
    if (-not $env:VIRTUAL_ENV) {
        Write-Warning "Activate virtual environment first: upd"
        return
    }
    
    Write-Host "=== Tests ===" -ForegroundColor Green
    pytest --quiet
    $testResult = $LASTEXITCODE
    
    Write-Host "`n=== Black ===" -ForegroundColor Green
    black --check unpdf/ tests/
    $blackResult = $LASTEXITCODE
    
    Write-Host "`n=== Ruff ===" -ForegroundColor Green
    ruff check unpdf/ tests/
    $ruffResult = $LASTEXITCODE
    
    Write-Host "`n=== Mypy ===" -ForegroundColor Green
    mypy unpdf/
    $mypyResult = $LASTEXITCODE
    
    if ($testResult -eq 0 -and $blackResult -eq 0 -and $ruffResult -eq 0 -and $mypyResult -eq 0) {
        Write-Host "`n✓ All checks passed!" -ForegroundColor Green
        return $true
    } else {
        Write-Warning "`nSome checks failed"
        return $false
    }
}
Set-Alias uc Invoke-UnpdfCheck

function Invoke-UnpdfCommit {
    <#
    .SYNOPSIS
    Run quality checks and commit if all pass.
    .PARAMETER Message
    Git commit message.
    #>
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message
    )
    
    if (-not $env:VIRTUAL_ENV) {
        Write-Warning "Activate virtual environment first: upd"
        return
    }
    
    Write-Host "Running quality checks..." -ForegroundColor Cyan
    $passed = Invoke-UnpdfCheck
    
    if ($passed) {
        Write-Host "`nCommitting changes..." -ForegroundColor Green
        git add .
        git commit -m $Message
        Write-Host "✓ Committed successfully" -ForegroundColor Green
    } else {
        Write-Warning "Fix quality check errors before committing"
    }
}
Set-Alias ucommit Invoke-UnpdfCommit

# Git Shortcuts
# ============================================================================

function gst { git status }
function gd { git diff }
function gl { git log --oneline -10 }
function ga { git add . }
function gc { 
    param([string]$msg) 
    if ($msg) {
        git commit -m $msg
    } else {
        Write-Warning "Usage: gc 'commit message'"
    }
}
function gp { git push }
function gpl { git pull }

# Usage Information
# ============================================================================

function Show-UnpdfCommands {
    <#
    .SYNOPSIS
    Show available unpdf development commands.
    #>
    Write-Host "`nUnpdf Development Commands:" -ForegroundColor Green
    Write-Host "  upd              - Enter unpdf dev environment" -ForegroundColor Cyan
    Write-Host "  ut [path]        - Run tests (optional: specific path)" -ForegroundColor Cyan
    Write-Host "  ul               - Run linters and formatters" -ForegroundColor Cyan
    Write-Host "  uc               - Run all quality checks" -ForegroundColor Cyan
    Write-Host "  ucommit 'msg'    - Check + commit if passing" -ForegroundColor Cyan
    Write-Host "`nGit Shortcuts:" -ForegroundColor Green
    Write-Host "  gst              - git status" -ForegroundColor Cyan
    Write-Host "  gd               - git diff" -ForegroundColor Cyan
    Write-Host "  gl               - git log (last 10)" -ForegroundColor Cyan
    Write-Host "  ga               - git add ." -ForegroundColor Cyan
    Write-Host "  gc 'msg'         - git commit" -ForegroundColor Cyan
    Write-Host "  gp               - git push" -ForegroundColor Cyan
    Write-Host "  gpl              - git pull" -ForegroundColor Cyan
    Write-Host ""
}
Set-Alias uphelp Show-UnpdfCommands

Write-Host "✓ unpdf development commands loaded. Type 'uphelp' for command list." -ForegroundColor Green
