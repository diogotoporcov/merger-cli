# Testing Merger CLI Artifacts

This guide explains how to test the standalone installers and packages generated for `merger-cli` using our enterprise-grade integration test suite.

## The Standalone Test Suite

We use a unified `pytest` suite located at `tests/test_standalone.py` to verify the functionality of built artifacts (binaries, `.deb` packages, etc.) across all platforms. This ensures consistent verification and framework-standard reporting.

To run these tests manually:
1.  **Build the binary**: `pyinstaller merger.spec`
2.  **Run pytest**:
    ```bash
    pytest tests/test_standalone.py --merger-bin=dist/merger-cli
    ```

The suite covers:
- CLI versioning and help information.
- Core merge logic (recursive scanning, file reading).
- `merger.ignore` pattern matching.
- JSON and plain text exporters.
- Basic package injection/purge command stability.

## Quick Automation Scripts

We provide helper scripts that handle the build process and then invoke the `pytest` suite:

- **Windows**: `.\scripts\test_windows.ps1` (PowerShell)
- **Linux**: `.\scripts\test_linux.ps1` (PowerShell) - Runs tests inside a clean Docker container.
- **macOS**: `./scripts/test_macos.sh` (Bash)

These scripts:
1. Clean previous build artifacts.
2. Build the standalone binary with PyInstaller.
3. **Execute `pytest tests/test_standalone.py --merger-bin=...`**.
4. (Optional) Build installers (e.g., Inno Setup on Windows, `.deb` on Linux).

## Linux Artifacts (via Docker)

You can test the Linux standalone binary and the `.deb` package in a clean Ubuntu environment using Docker.

1.  **Ensure Docker is running**.
2.  **Run the test script**:
    ```powershell
    # On Windows
    .\scripts\test_linux.ps1
    ```
    Alternatively, manually:
    ```bash
    docker build -t merger-test-linux -f Dockerfile.test_linux .
    docker run --rm merger-test-linux
    ```

This script will:
*   Build the standalone binary with PyInstaller (Linux version).
*   Build the Debian package (`.deb`) using `nFPM`.
*   Install the `.deb` package and verify it correctly pulls `libmagic1`.
*   Verify that `merger` can be called globally and correctly identifies/merges files.
*   Test both the installed version and the standalone binary.

## Windows Artifacts

### 1. Standalone Binary
To verify the standalone `.exe` works:
1.  Build it locally:
    ```powershell
    pyinstaller merger.spec
    ```
2.  Run the generated binary:
    ```powershell
    .\dist\merger-cli.exe --version
    ```
3.  Test merge functionality:
    ```powershell
    cd some_project
    ..\dist\merger-cli.exe .
    ```

### 2. MSI/EXE Installer (Inno Setup)
To test the installer:
1.  Compile the installer using Inno Setup (requires `ISCC.exe` in PATH):
    ```powershell
    ISCC.exe installer.iss
    ```
2.  Run `dist\merger-cli-windows-installer.exe` and follow the steps.
3.  Verify `merger` is added to your PATH (you may need to restart your terminal).
4.  Run `merger --version` from any directory.

## Known Limitations in Standalone Bundles

*   **Package Injection (`--inject`)**: In the standalone (PyInstaller) version, `pip` is bundled inside the executable. Some package installations may fail if they depend on a full Python interpreter environment or if `pip` needs to call subprocesses that are not available in the bundle.
*   **libmagic**: On Linux, the `.deb` package automatically handles `libmagic1`. On Windows, the binary includes `python-magic-bin` which contains all required DLLs.

## Automated CI Testing
The project includes GitHub Actions workflows to build and release these artifacts automatically on tags (`api-v*` for the API and `cli-v*` for the CLI).
