#!/bin/bash
set -e

# Script to test the macOS standalone binary
echo "--- Testing macOS Build and Standalone ---"

# 1. Clean previous builds
echo "Cleaning dist and build directories..."
rm -rf dist build

# 2. Build with PyInstaller
echo "Building standalone binary with PyInstaller..."
pyinstaller packaging/merger.spec

# 3. Verify standalone binary exists
if [ ! -f dist/merger-cli/merger ]; then
    echo "Standalone binary not found at dist/merger-cli/merger"
    exit 1
fi

# 4. Run tests with pytest
echo "Running standalone tests with pytest..."
pytest packages/merger-cli/tests/test_standalone.py --merger-bin=dist/merger-cli/merger

echo "--- macOS tests completed successfully ---"
