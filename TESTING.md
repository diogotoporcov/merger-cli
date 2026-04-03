# Testing Merger CLI Artifacts

This guide explains how to test the standalone installers and packages generated for `merger-cli` using the integration test suite.

## The Standalone Test Suite

A unified `pytest` suite located at `tests/test_standalone.py` is used to verify the functionality of built artifacts (binaries, `.deb` packages, etc.) across all platforms. This ensures consistent verification and framework-standard reporting.

To run these tests manually:
1.  **Build the binary**: `pyinstaller packaging/merger.spec`
2.  **Run pytest**:
    ```bash
    pytest packages/merger-cli/tests/test_standalone.py --merger-bin=dist/merger-cli/merger
    ```

The suite covers:
- CLI versioning and help information.
- Core merge logic (recursive scanning, file reading).
- `merger.ignore` pattern matching.
- JSON and plain text exporters.
- Basic package injection/purge command stability.

## Quick Automation Scripts

Helper scripts are provided to handle the build process and then invoke the `pytest` suite:

- **Windows**: `.\scripts\test_windows.ps1` (PowerShell)
- **Linux**: `./scripts/test_linux.sh` (Bash)
- **macOS**: `./scripts/test_macos.sh` (Bash)

These scripts:
1. Clean previous build artifacts.
2. Build the standalone binary with PyInstaller.
3. **Execute `pytest packages/merger-cli/tests/test_standalone.py --merger-bin=...`**.
4. (Optional) Build installers (e.g., MSI on Windows, `.deb` on Linux).
5. (If running as Admin/Root) Install the package, run the test suite against the installed binary, and uninstall it.

## Linux Artifacts
The `scripts/test_linux.sh` script automates the build and verification of the Linux standalone binary and the `.deb` package.

This script will:
*   Build the standalone binary with PyInstaller (Linux version).
*   Build the Debian package (`.deb`) using `nFPM`.
*   (If running as root/sudo) Install the `.deb` package, verify it correctly pulls dependencies, and test the installed `merger` binary using the `pytest` suite.

## Windows Artifacts

### 1. Standalone Binary
To verify the standalone `.exe` works:
1.  Build it locally:
    ```powershell
    pyinstaller packaging/merger.spec
    ```
2.  Run the generated binary:
    ```powershell
    .\dist\merger-cli\merger.exe --version
    ```
3.  Test merge functionality:
    ```powershell
    cd some_project
    ..\dist\merger-cli\merger.exe .
    ```

### 2. MSI Installer (WiX)
To test the installer:
1.  Run the automation script:
    ```powershell
    .\scripts\test_windows.ps1
    ```
    If running with Administrator privileges, it will automatically perform a silent install/uninstall test.
2.  Alternatively, manually run `dist\merger-cli-installer.msi`.
3.  Verify `merger` is added to your PATH (you may need to restart your terminal).
4.  Run `merger --version` from any directory.

## Known Limitations in Standalone Bundles

*   **Package Injection (`--inject`)**: In the standalone (PyInstaller) version, `pip` is bundled inside the executable. Some package installations may fail if they depend on a full Python interpreter environment or if `pip` needs to call subprocesses that are not available in the bundle.
*   **libmagic**: On Linux, the `.deb` package automatically handles `libmagic1`. On Windows, the binary includes `python-magic-bin` which contains all required DLLs.

## Automated CI Testing
The project includes GitHub Actions workflows to build and release these artifacts automatically on tags (`api-v*` for the API and `cli-v*` for the CLI).
