#!/bin/bash
# Start Amiibo Headless Server on Raspberry Pi

echo "=========================================="
echo "Starting Amiibo Headless Server"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "Working directory: $SCRIPT_DIR"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠ This script needs sudo to access I2C"
    echo "Restarting with sudo..."
    sudo "$0" "$@"
    exit $?
fi

# Check if server file exists
if [ ! -f "server_headless.py" ]; then
    echo "✗ Error: server_headless.py not found!"
    echo "Current directory: $(pwd)"
    echo "Files in directory:"
    ls -la
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "✗ Error: Python 3 is not installed"
    exit 1
fi

# Check if required modules are installed
echo "Checking dependencies..."
python3 -c "import smbus2, RPi.GPIO" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠ Missing dependencies. Installing..."
    pip3 install smbus2 RPi.GPIO
fi

echo ""
echo "Starting server on port 5555..."
echo "Press Ctrl+C to stop"
echo ""

# Run the server
python3 server_headless.py

echo ""
echo "Server stopped"
