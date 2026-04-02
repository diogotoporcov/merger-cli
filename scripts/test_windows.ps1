# Script to test the Windows standalone binary and installer

Write-Host "--- Testing Windows Build and Standalone ---" -ForegroundColor Cyan

# 1. Clean previous builds
Write-Host "Cleaning dist and build directories..."
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# 2. Build with PyInstaller
Write-Host "Building standalone binary with PyInstaller..."
pyinstaller packaging\merger.spec
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller build failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

# 3. Verify standalone binary exists
$merger_exe = "dist\merger-cli\merger.exe"
if (-not (Test-Path $merger_exe)) {
    Write-Host "Standalone binary not found at $merger_exe" -ForegroundColor Red
    exit 1
}

# 4. Run tests with pytest
Write-Host "Running standalone tests with pytest..." -ForegroundColor Cyan
pytest packages/merger-cli/tests/test_standalone.py --merger-bin=$merger_exe
if ($LASTEXITCODE -ne 0) {
    Write-Host "Standalone tests failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

# 5. Installer test (Inno Setup)
$iscc_path = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (Test-Path $iscc_path) {
    Write-Host "Building Windows installer..."
    & $iscc_path packaging\installer.iss
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Installer built successfully at dist\merger-cli-windows-installer.exe" -ForegroundColor Green
    } else {
        Write-Host "Installer build failed!" -ForegroundColor Red
    }
} else {
    Write-Host "Inno Setup (ISCC.exe) not found at $iscc_path. Skipping installer build." -ForegroundColor Yellow
}

Write-Host "--- Windows tests completed successfully ---" -ForegroundColor Green
