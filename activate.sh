#!/bin/bash
# Auto-activation script for Brainnet virtual environment
# Source this file or add to your shell config

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/.venv"

if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    export PYTHONPATH="$SCRIPT_DIR/lms/minah/src:$PYTHONPATH"
    # Only show message if not already activated
    if [ -z "$VIRTUAL_ENV" ] || [ "$VIRTUAL_ENV" != "$VENV_PATH" ]; then
        echo "✅ Brainnet virtual environment activated (Python $(python --version | cut -d' ' -f2))"
    fi
else
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "   Run: python3.11 -m venv .venv && source .venv/bin/activate && pip install -r lms/minah/requirements.txt"
    return 1 2>/dev/null || exit 1
fi

