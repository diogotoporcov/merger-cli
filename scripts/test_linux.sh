#!/bin/bash
set -e

# Script to test the Linux build and standalone binary natively
echo "--- Testing Linux Build and Standalone ---"

# 1. Clean previous builds
echo "Cleaning dist and build directories..."
rm -rf dist build

# 2. Build with PyInstaller
echo "Building standalone binary with PyInstaller..."
pyinstaller packaging/merger.spec

# 3. Verify standalone binary exists
if [ ! -f dist/merger-cli ]; then
    echo "Standalone binary not found at dist/merger-cli"
    exit 1
fi

# 4. Run tests with pytest
echo "Running standalone tests with pytest..."
pytest tests/test_standalone.py --merger-bin=dist/merger-cli

# 5. Build and verify .deb package (if nfpm is available)
if command -v nfpm >/dev/null 2>&1; then
    echo "Building .deb package..."
    # Extract version from pyproject.toml
    PKG_VERSION=$(grep -Po '(?<=version = ")[^"]+' pyproject.toml)
    VERSION=$PKG_VERSION nfpm package --config packaging/nfpm.yaml --target dist/merger-cli.deb
    echo "Installer built successfully at dist/merger-cli.deb"
    
    # Try to install and test if sudo is available or running as root
    if [ "$(id -u)" -eq 0 ]; then
        echo "Running as root, testing .deb installation..."
        apt-get update && apt-get install -y ./dist/merger-cli.deb
        pytest tests/test_standalone.py --merger-bin=/usr/bin/merger
    elif command -v sudo >/dev/null 2>&1; then
        echo "sudo available, testing .deb installation..."
        sudo apt-get update && sudo apt-get install -y ./dist/merger-cli.deb
        pytest tests/test_standalone.py --merger-bin=/usr/bin/merger
    fi
else
    echo "nfpm not found. Skipping .deb package build."
fi

echo "--- Linux tests completed successfully ---"
