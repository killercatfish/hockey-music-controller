#!/bin/bash

# Hockey Music Controller - Installation and Launcher Script

echo "=========================================="
echo "Hockey Music Controller Setup"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_FILE="$SCRIPT_DIR/hockey_music_controller.py"

# Check if Python script exists
if [ ! -f "$PYTHON_FILE" ]; then
    echo "❌ Error: hockey_music_controller.py not found in this directory"
    echo "Please ensure all files are in the same folder."
    exit 1
fi

# Check Python installation
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Found: $PYTHON_VERSION"
else
    echo "❌ Error: Python 3 not found"
    echo "Please install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

# Check tkinter
echo "Checking tkinter (GUI library)..."
if python3 -c "import tkinter" 2>/dev/null; then
    echo "✅ Tkinter is available"
else
    echo "❌ Error: tkinter not available"
    echo "Please reinstall Python from python.org (not homebrew)"
    exit 1
fi

# Make Python script executable
echo "Setting permissions..."
chmod +x "$PYTHON_FILE"
echo "✅ Permissions set"

# Check if Music app is running
echo ""
echo "Checking Music app..."
if pgrep -x "Music" > /dev/null; then
    echo "✅ Music app is running"
else
    echo "⚠️  Music app is not running"
    echo "Would you like to open it now? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        open -a Music
        echo "✅ Music app opened"
        echo "Waiting for Music app to load..."
        sleep 3
    else
        echo "⚠️  Remember to open Music app before using the controller"
    fi
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Starting Hockey Music Controller..."
echo ""

# Launch the application
python3 "$PYTHON_FILE"
