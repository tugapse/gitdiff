#!/bin/bash

# --- CONFIGURATION ---
FOLDER=$(dirname -- $(realpath -- "$0"))

python3 $FOLDER/main.py "$@"