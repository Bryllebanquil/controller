# Test Script: Verify CMD and PowerShell are ENABLED

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  TESTING CMD AND POWERSHELL STATUS" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Check PowerShell ExecutionPolicy
Write-Host "[TEST 1] Checking PowerShell ExecutionPolicy..." -ForegroundColor Yellow
$policy = Get-ExecutionPolicy -Scope CurrentUser
if ($policy -eq "Unrestricted" -or $policy -eq "Bypass") {
    Write-Host "  ✅ PowerShell ExecutionPolicy: $policy (ENABLED)" -ForegroundColor Green
} else {
    Write-Host "  ⚠️ PowerShell ExecutionPolicy: $policy (May have restrictions)" -ForegroundColor Yellow
}
Write-Host ""

# Test 2: Check CMD registry setting
Write-Host "[TEST 2] Checking CMD registry setting..." -ForegroundColor Yellow
try {
    $cmdDisabled = Get-ItemProperty -Path "HKCU:\Software\Policies\Microsoft\Windows\System" -Name DisableCMD -ErrorAction Stop
    if ($cmdDisabled.DisableCMD -eq 0) {
        Write-Host "  ✅ CMD DisableCMD = 0 (ENABLED)" -ForegroundColor Green
    } elseif ($cmdDisabled.DisableCMD -eq 1) {
        Write-Host "  ❌ CMD DisableCMD = 1 (DISABLED)" -ForegroundColor Red
        Write-Host "     Run: reg add ""HKCU\Software\Policies\Microsoft\Windows\System"" /v DisableCMD /t REG_DWORD /d 0 /f" -ForegroundColor Yellow
    } else {
        Write-Host "  ⚠️ CMD DisableCMD = $($cmdDisabled.DisableCMD) (Unknown value)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✅ CMD DisableCMD not set (ENABLED by default)" -ForegroundColor Green
}
Write-Host ""

# Test 3: Test PowerShell command execution
Write-Host "[TEST 3] Testing PowerShell command execution..." -ForegroundColor Yellow
try {
    $result = Get-Process powershell -ErrorAction Stop | Select-Object -First 1
    Write-Host "  ✅ PowerShell commands work!" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️ PowerShell command failed: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# Test 4: Test CMD availability
Write-Host "[TEST 4] Testing CMD availability..." -ForegroundColor Yellow
try {
    $cmdPath = Get-Command cmd.exe -ErrorAction Stop
    Write-Host "  ✅ CMD.exe found at: $($cmdPath.Source)" -ForegroundColor Green
    
    # Try to run a CMD command
    $testOutput = cmd /c "echo CMD is working"
    if ($testOutput -eq "CMD is working") {
        Write-Host "  ✅ CMD execution works!" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ CMD execution returned unexpected output" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ CMD not found or blocked: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: Check Task Manager
Write-Host "[TEST 5] Checking Task Manager status..." -ForegroundColor Yellow
try {
    $tmDisabled = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\System" -Name DisableTaskMgr -ErrorAction Stop
    if ($tmDisabled.DisableTaskMgr -eq 0) {
        Write-Host "  ✅ Task Manager ENABLED" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Task Manager DISABLED" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✅ Task Manager not restricted (ENABLED by default)" -ForegroundColor Green
}
Write-Host ""

# Test 6: Check Registry Editor
Write-Host "[TEST 6] Checking Registry Editor status..." -ForegroundColor Yellow
try {
    $regDisabled = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\System" -Name DisableRegistryTools -ErrorAction Stop
    if ($regDisabled.DisableRegistryTools -eq 0) {
        Write-Host "  ✅ Registry Editor ENABLED" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Registry Editor DISABLED" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✅ Registry Editor not restricted (ENABLED by default)" -ForegroundColor Green
}
Write-Host ""

# Test 7: Check UAC status
Write-Host "[TEST 7] Checking UAC status..." -ForegroundColor Yellow
try {
    $uacEnabled = Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name EnableLUA -ErrorAction Stop
    if ($uacEnabled.EnableLUA -eq 0) {
        Write-Host "  ⚠️ UAC DISABLED (as configured by client.py)" -ForegroundColor Yellow
    } else {
        Write-Host "  ✅ UAC ENABLED" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠️ Cannot read UAC status (may require admin)" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  SUMMARY" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Expected Configuration:" -ForegroundColor White
Write-Host "  ✅ CMD - ENABLED" -ForegroundColor Green
Write-Host "  ✅ PowerShell - ENABLED (Unrestricted)" -ForegroundColor Green
Write-Host "  ✅ Task Manager - ENABLED" -ForegroundColor Green
Write-Host "  ✅ Registry Editor - ENABLED" -ForegroundColor Green
Write-Host "  ⚠️ UAC - DISABLED (by design)" -ForegroundColor Yellow
Write-Host ""
Write-Host "If any tool is DISABLED, run:" -ForegroundColor Yellow
Write-Host "  - For CMD: EMERGENCY_ENABLE_CMD.bat" -ForegroundColor White
Write-Host "  - For PowerShell: Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Unrestricted -Force" -ForegroundColor White
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
