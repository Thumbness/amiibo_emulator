#!/bin/bash
# Start Amiibo GUI Client on Unix/Linux/macOS

echo "=========================================="
echo "Starting Amiibo GUI Client"
echo "=========================================="
echo ""

# Change to script directory
cd "$(dirname "$0")/amiibo_emulator"

# Check if client file exists
if [ ! -f "src/client_gui.py" ]; then
    echo "Error: client_gui.py not found!"
    echo "Make sure you're in the correct directory"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    echo "Please install Python 3"
    exit 1
fi

echo "Starting GUI client..."
echo ""

# Run the GUI
python3 src/client_gui.py

if [ $? -ne 0 ]; then
    echo ""
    echo "GUI closed with error"
fi
