#!/bin/env bash

set -e

# Check for system dependencies
echo "Checking system dependencies..."
MISSING_DEPS=0

for cmd in python3; do
  if ! command -v "$cmd" &> /dev/null; then
    # Fallback to check for pip3 if pip is missing
    if [ "$cmd" = "pip" ] && command -v pip3 &> /dev/null; then
      continue
    fi
    echo "Error: $cmd is not installed."
    MISSING_DEPS=1
  fi
done

if [ $MISSING_DEPS -ne 0 ]; then
  echo "Please install the missing dependencies and run the script again."
  exit 1
fi


# get current scriot location
SCRIPT_DIR=$(dirname -- $(realpath -- "$0"))


echo ""
echo "======================================================"
echo "Build completed successfully!"
echo "To start the application, from project folder run:"
echo ""
echo "  ./run.sh [options] repo_path"
echo ""
echo "======================================================"