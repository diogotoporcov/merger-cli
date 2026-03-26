#!/bin/bash
set -e

# Extract name and version from pyproject.toml
PACKAGE_NAME=$(grep "^name =" pyproject.toml | cut -d'"' -f2)
VERSION=$(grep "^version =" pyproject.toml | cut -d'"' -f2)

if [ -z "$PACKAGE_NAME" ] || [ -z "$VERSION" ]; then
  echo "Error: Could not find package name or version in pyproject.toml"
  exit 1
fi

# Check if version exists on PyPI
URL="https://pypi.org/pypi/$PACKAGE_NAME/$VERSION/json"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL")

# Set outputs for GitHub Action
if [ -n "$GITHUB_OUTPUT" ]; then
  echo "package_name=$PACKAGE_NAME" >> "$GITHUB_OUTPUT"
  echo "version=$VERSION" >> "$GITHUB_OUTPUT"
  
  if [ "$STATUS_CODE" -eq 200 ]; then
    echo "should_publish=false" >> "$GITHUB_OUTPUT"
  else
    echo "should_publish=true" >> "$GITHUB_OUTPUT"
  fi
fi

# Log results
if [ "$STATUS_CODE" -eq 200 ]; then
  echo "Version $VERSION of $PACKAGE_NAME already exists on PyPI. Publish will be skipped."
else
  echo "Version $VERSION of $PACKAGE_NAME is not on PyPI. Publish will run."
fi
