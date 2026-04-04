# Script to test the Windows standalone binary and installer
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Warning: Script is not running as Administrator. MSI installation test might fail." -ForegroundColor Yellow
}

Write-Host "--- Testing Windows Build and Standalone ---" -ForegroundColor Cyan

# 1. Clean previous builds
Write-Host "Cleaning dist and build directories..."
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# 2. Build with PyInstaller
Write-Host "Building standalone binary with PyInstaller..."
python -m PyInstaller --noconfirm packaging\merger.spec
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
$wix_exe = "wix"
$wix_full_path = "C:\Program Files\WiX Toolset v7.0\bin\wix.exe"
if (Test-Path $wix_full_path) {
    $wix_exe = $wix_full_path
} else {
    $wix_cmd = Get-Command wix -ErrorAction SilentlyContinue
    if ($wix_cmd) {
        $wix_exe = $wix_cmd.Source
    } else {
        Write-Host "WiX Toolset (wix.exe) not found in PATH or standard locations." -ForegroundColor Red
        Write-Host "Please install WiX v4+ (dotnet tool install --global wix) or WiX v7." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Using WiX Toolset: $wix_exe" -ForegroundColor Cyan
$wix_version = (& "$wix_exe" --version)
Write-Host "WiX Version: $wix_version"

# Handle WiX v7+ OSMF EULA if needed
if ($wix_version -like "7.*") {
    Write-Host "Accepting WiX v7 EULA..."
    & "$wix_exe" eula accept wix7 --acceptEula true
}

Write-Host "Preparing MSI metadata and license..." -ForegroundColor Cyan
$metadata = @{}
python scripts\metadata_helper.py | ForEach-Object {
    if ($_ -match "([^=]+)=(.*)") {
        $metadata[$Matches[1]] = $Matches[2]
    }
}

python scripts\metadata_helper.py --rtf | Out-Null

Write-Host "Building Windows MSI installer (WiX v4+)..." -ForegroundColor Cyan

# 1. Add required extensions
Write-Host "Checking/Adding WiX extensions..."
$wix_major = 0
if ($wix_version -match "^(\d+)") {
    $wix_major = [int]$Matches[1]
}

$ext_version = ""
if ($wix_major -eq 5) {
    $ext_version = "5.0.2"
} elseif ($wix_major -eq 4) {
    $ext_version = "4.0.5"
} elseif ($wix_major -ge 7) {
    $ext_version = "7.0.0-rc.2"
}

$ext_pkg_ui = "WixToolset.UI.wixext"
$ext_pkg_util = "WixToolset.Util.wixext"
if ($ext_version) {
    $ext_pkg_ui = "$ext_pkg_ui/$ext_version"
    $ext_pkg_util = "$ext_pkg_util/$ext_version"
}

$addExtArgsUi = if ($wix_version -ge "7.0") { "extension", "add", "$ext_pkg_ui", "--acceptEula", "true" } else { "extension", "add", "$ext_pkg_ui" }
& "$wix_exe" $addExtArgsUi
$addExtArgsUtil = if ($wix_version -ge "7.0") { "extension", "add", "$ext_pkg_util", "--acceptEula", "true" } else { "extension", "add", "$ext_pkg_util" }
& "$wix_exe" $addExtArgsUtil

# 2. Build (compile & link)
Write-Host "Compiling and linking MSI..."
$acceptEulaFlag = if ($wix_version -ge "7.0") { "--acceptEula", "true" } else { @() }
& "$wix_exe" build -arch x64 -ext WixToolset.UI.wixext -ext WixToolset.Util.wixext `
    -d Version=$($metadata["msi_version"]) `
    -d Description="$($metadata["description"])" `
    -d Homepage="$($metadata["homepage"])" `
    -d LicenseRtf="packaging\license.rtf" `
    packaging\merger.wxs -o "dist\merger-cli-installer.msi" $acceptEulaFlag

if ($LASTEXITCODE -eq 0) {
    Write-Host "MSI Installer built successfully at dist\merger-cli-installer.msi" -ForegroundColor Green
} else {
    Write-Host "MSI Installer build failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

# 6. Verify MSI installation and functionality
Write-Host "--- Verifying MSI installation and functionality ---" -ForegroundColor Cyan
if ($isAdmin) {
    $msi_path = "dist\merger-cli-installer.msi"
    $install_dir_machine = "C:\Program Files\MergerCLI"
    $install_dir_user = "$env:LOCALAPPDATA\Programs\MergerCLI"
    $install_log = "dist\install.log"

    Write-Host "Attempting silent installation of MSI (Per-Machine)..."
    $process = Start-Process msiexec.exe -ArgumentList "/i `"$msi_path`" /qn /norestart ALLUSERS=1 WixAppFolder=WixPerMachineFolder /L*V `"$install_log`"" -Wait -PassThru
    
    if ($process.ExitCode -eq 0 -or $process.ExitCode -eq 3010) {
        Write-Host "MSI installed successfully (Per-Machine)." -ForegroundColor Green
        $installed_exe = "$install_dir_machine\merger.exe"
        
        # Run tests against the installed binary
        if (Test-Path $installed_exe) {
            Write-Host "Verified: $installed_exe exists." -ForegroundColor Green
            Write-Host "Running standalone tests against installed binary (Per-Machine)..." -ForegroundColor Cyan
            python -m pytest packages/merger-cli/tests/test_standalone.py --merger-bin=$installed_exe
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Tests against installed binary failed!" -ForegroundColor Red
                $verified = $false
            } else {
                Write-Host "Installed binary passed all tests." -ForegroundColor Green
                $verified = $true
            }
        } else {
            Write-Host "Verification failed: $installed_exe NOT found after installation!" -ForegroundColor Red
            if (Test-Path $install_dir_machine) {
                Write-Host "Contents of ${install_dir_machine}:"
                Get-ChildItem -Path $install_dir_machine -Recurse | Select-Object FullName
            } else {
                Write-Host "Directory $install_dir_machine does not exist!"
            }
            $verified = $false
        }
        
        Write-Host "Uninstalling MSI..."
        Start-Process msiexec.exe -ArgumentList "/x `"$msi_path`" /qn /norestart" -Wait
        
        if (-not $verified) {
            Write-Host "MSI verification failed!" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "MSI installation failed (Per-Machine) with exit code $($process.ExitCode)!" -ForegroundColor Red
        if (Test-Path $install_log) {
            Write-Host "Last 20 lines of installation log:"
            Get-Content $install_log -Tail 20
        }
        exit $process.ExitCode
    }

    Write-Host "Attempting silent installation of MSI (Per-User)..."
    Remove-Item $install_log -ErrorAction SilentlyContinue
    $process = Start-Process msiexec.exe -ArgumentList "/i `"$msi_path`" /qn /norestart ALLUSERS=2 MSIINSTALLPERUSER=1 WixAppFolder=WixPerUserFolder /L*V `"$install_log`"" -Wait -PassThru

    if ($process.ExitCode -eq 0 -or $process.ExitCode -eq 3010) {
        Write-Host "MSI installed successfully (Per-User)." -ForegroundColor Green
        $installed_exe = "$install_dir_user\merger.exe"
        
        # Run tests against the installed binary
        if (Test-Path $installed_exe) {
            Write-Host "Verified: $installed_exe exists." -ForegroundColor Green
            Write-Host "Running standalone tests against installed binary (Per-User)..." -ForegroundColor Cyan
            python -m pytest packages/merger-cli/tests/test_standalone.py --merger-bin=$installed_exe
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Tests against installed binary failed!" -ForegroundColor Red
                $verified = $false
            } else {
                Write-Host "Installed binary passed all tests." -ForegroundColor Green
                $verified = $true
            }
        } else {
            Write-Host "Verification failed: $installed_exe NOT found after installation!" -ForegroundColor Red
            if (Test-Path $install_dir_user) {
                Write-Host "Contents of ${install_dir_user}:"
                Get-ChildItem -Path $install_dir_user -Recurse | Select-Object FullName
            } else {
                Write-Host "Directory $install_dir_user does not exist!"
            }
            $verified = $false
        }
        
        Write-Host "Uninstalling MSI..."
        Start-Process msiexec.exe -ArgumentList "/x `"$msi_path`" /qn /norestart" -Wait
        
        if (-not $verified) {
            Write-Host "MSI verification failed!" -ForegroundColor Red
            exit 1
        }
        Write-Host "MSI verification completed successfully (Per-User)." -ForegroundColor Green
    } else {
        Write-Host "MSI installation failed (Per-User) with exit code $($process.ExitCode)!" -ForegroundColor Red
        if (Test-Path $install_log) {
            Write-Host "Last 20 lines of installation log:"
            Get-Content $install_log -Tail 20
        }
        exit $process.ExitCode
    }
} else {
    Write-Host "Skipping MSI installation and verification test (Admin privileges required)." -ForegroundColor Yellow
}

Write-Host "--- Windows tests completed successfully ---" -ForegroundColor Green
