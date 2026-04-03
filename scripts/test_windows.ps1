# Script to test the Windows standalone binary and installer

Write-Host "--- Testing Windows Build and Standalone ---" -ForegroundColor Cyan

# 1. Clean previous builds
Write-Host "Cleaning dist and build directories..."
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# 2. Build with PyInstaller
Write-Host "Building standalone binary with PyInstaller..."
python -m PyInstaller packaging\merger.spec
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
python -m pytest packages/merger-cli/tests/test_standalone.py --merger-bin=$merger_exe
if ($LASTEXITCODE -ne 0) {
    Write-Host "Standalone tests failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

# 5. Installer test (WiX Toolset)
$wix_exe = "C:\Program Files\WiX Toolset v7.0\bin\wix.exe"
if (-not (Test-Path $wix_exe)) {
    # Try to find wix tools in PATH if not in standard locations
    $wix_cmd = Get-Command wix -ErrorAction SilentlyContinue
    if ($wix_cmd) { $wix_exe = $wix_cmd.Source }
}

if (-not (Test-Path $wix_exe)) {
    Write-Host "WiX Toolset (wix.exe) not found. This is required for MSI installer build." -ForegroundColor Red
    exit 1
}

Write-Host "Generating WiX source file..." -ForegroundColor Cyan
python scripts\generate_installer.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to generate WiX source files!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Building Windows MSI installer (WiX v4+)..." -ForegroundColor Cyan

# 1. Add required extensions
Write-Host "Checking/Adding WiX extensions..."
& "$wix_exe" extension add WixToolset.UI.wixext --acceptEula true
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to add WiX extensions!" -ForegroundColor Red
    exit $LASTEXITCODE
}

# 2. Build (compile & link)
Write-Host "Compiling and linking MSI..."
& "$wix_exe" build -arch x64 -ext WixToolset.UI.wixext packaging\merger.wxs -o "dist\merger-cli-installer.msi" --acceptEula true

if ($LASTEXITCODE -eq 0) {
    Write-Host "MSI Installer built successfully at dist\merger-cli-installer.msi" -ForegroundColor Green
} else {
    Write-Host "MSI Installer build failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "--- Windows tests completed successfully ---" -ForegroundColor Green
