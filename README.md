# Amiibo Hackbox - Headless NFC Writer

A complete Amiibo writing system with a headless Raspberry Pi server and GUI client. Write custom Amiibo tags remotely over your network!

## Features

- **Headless Operation** - No LCD or buttons needed on Pi
- **Remote Control** - GUI client for Windows/Linux
- **Network-Based** - Control from anywhere on your network
- **Auto-Connect** - Saves your Pi hostname for quick startup
- **26 Categories** - Browse 100+ Amiibo characters
- **Flipper Zero Format** - Compatible with .nfc files
- **Real-Time Updates** - See progress as tags are written
- **No I2C Conflicts** - PN532 has exclusive bus access

## Hardware Requirements

### Raspberry Pi Setup

| Component | Specification | Notes |
|-----------|--------------|-------|
| **Raspberry Pi** | Any model with GPIO | Tested on Pi 3/4 |
| **PN532 NFC Module** | I2C mode | Must support NTAG215 |
| **Power Supply** | 5V 2.5A+ | Standard Pi power |
| **Network** | WiFi or Ethernet | For remote control |
| **NTAG215 Tags** | Blank NFC tags | **Required** - S50/MIFARE won't work! |

### Client PC

- Windows 10/11 or Linux
- Python 3.7+
- Network connection to Pi

## What You Need to Buy

### Essential:
- **NTAG215 NFC Tags**
  - Search: "NTAG215 NFC tags" or "Amiibo compatible tags"
  - **Must be NTAG215** - Other types won't work!

### If You Don't Have:
- **PN532 NFC Module** 
  - Must support I2C mode
  - Usually has DIP switches or jumpers
- **Raspberry Pi** 
  - Any model with GPIO pins
  - Pi Zero W works but slower

## Hardware Connections

### PN532 to Raspberry Pi (I2C Mode)

| PN532 Pin | Raspberry Pi Pin | BCM GPIO | Description |
|-----------|------------------|----------|-------------|
| VCC | Pin 1 | 3.3V | Power |
| GND | Pin 6 | GND | Ground |
| SDA | Pin 3 | GPIO 2 | I2C Data |
| SCL | Pin 5 | GPIO 3 | I2C Clock |

### PN532 Mode Configuration

Set PN532 to **I2C mode**:
- **DIP Switches:** Set to `0 1` (OFF ON)
- **Jumpers:** Connect I2C mode pins (check your module's manual)

## Installation

### On Raspberry Pi

1. **Enable I2C:**
```bash
sudo raspi-config
# Navigate to: Interface Options -> I2C -> Enable
sudo reboot
```

2. **Install Dependencies:**
```bash
sudo apt update
sudo apt install python3 python3-pip git -y
pip3 install smbus2 RPi.GPIO
```

3. **Clone/Copy Project:**
```bash
cd ~
# Either clone from git or copy files via scp
# scp -r amiibo_emulator pi@<hostname>:/home/pi/
```

4. **Test PN532 Connection:**
```bash
sudo i2cdetect -y 1
# Should show device at address 0x24
```

### On Client PC

1. **Install Python:**
   - Download from [python.org](https://www.python.org/downloads/)
   - Check "Add Python to PATH" during installation

2. **No Additional Dependencies Needed!**
   - GUI uses only Python standard library (tkinter)

## Usage

### Quick Start

**On Raspberry Pi:**
```bash
cd ~/amiibo_emulator
chmod +x start_amiibo_server.sh
./start_amiibo_server.sh
```

**On Windows:**
```cmd
cd amiibo_emulator
start_gui.bat
```

**On Linux/Mac:**
```bash
cd amiibo_emulator
chmod +x start_gui.sh
./start_gui.sh
```

### Step-by-Step

1. **Start Server on Pi:**
```bash
ssh pi@thumbness  # or use your Pi's IP
cd ~/amiibo_emulator
sudo python3 src/server_headless.py
```

You should see:
```
============================================================
Headless Amiibo Server
============================================================

PN532 Firmware: v1.0
SAM configured for tag writing
Server listening on port 5555
Waiting for client connections...
```

2. **Launch GUI Client:**
   - **Windows:** Double-click `amiibo_emulator/start_gui.bat`
   - **Linux/Mac:** Run `./amiibo_emulator/start_gui.sh`
   - Or manually: `python amiibo_emulator/src/client_gui.py`
   - Enter Pi hostname (e.g., `thumbness`) or IP address
   - Check "Auto-connect on startup" to save it
   - Click "Connect"

3. **Write an Amiibo:**
   - Browse categories in left panel
   - Select character in middle panel
   - Place NTAG215 tag on PN532
   - Click "Write to Tag"
   - Wait for completion

## Configuration

### Change Server Port

Edit `amiibo_emulator/src/server_headless.py`:
```python
server = AmiiboServer(port=5555)  # Change port here
```

Edit `amiibo_emulator/src/client_gui.py`:
```python
def __init__(self, host, port=5555):  # Change port here
```

### Change Auto-Connect Hostname

The GUI saves your last connection in `amiibo_emulator/src/.amiibo_config`. To change:
- Delete the `.amiibo_config` file
- Or edit it manually with your Pi's hostname/IP

## Troubleshooting

### "No connection could be made"
- Server is running on Pi: `sudo python3 src/server_headless.py`
- Pi is on network: `ping <pi-hostname/IP>`
- Firewall allows port 5555
- Using correct hostname/IP

### "No tag detected"
- Using **NTAG215** tags (not S50/MIFARE)
- Tag is placed flat on PN532
- PN532 is in I2C mode
- I2C is enabled: `sudo i2cdetect -y 1`

### "I2C Error 121"
- Only PN532 on I2C bus (no LCD!)
- Wiring is correct
- PN532 mode switches set correctly

### "Permission denied"
- Run server with sudo: `sudo python3 src/server_headless.py`
- I2C permissions: `sudo usermod -a -G i2c pi`

### GUI Won't Start
- Python installed: `python --version`
- In correct directory
- File exists: `ls amiibo_emulator/src/client_gui.py`

### Server Script Fails
- Make executable: `chmod +x start_amiibo_server.sh`
- Run from amiibo_emulator directory
- Check file has Unix line endings (LF not CRLF)

## Adding New Amiibos

1. Place `.nfc` files in `amiibo_emulator/amiibo_data/categories/YourCategory/`
2. Run index regenerator:
```bash
cd ~/amiibo_emulator
python3 utils/regenerate_index.py
```
3. Restart server

## Security Notes

- Server runs on local network only (0.0.0.0:5555)
- No authentication required (trust your network!)
- No encryption (data is on local network)
- Requires sudo for I2C access

## How It Works

1. **Server (Pi):**
   - Listens on port 5555
   - Manages PN532 via I2C
   - Loads Amiibo data from files
   - Writes to NTAG215 tags

2. **Client (GUI):**
   - Connects via TCP socket
   - Sends JSON commands
   - Displays real-time status
   - Auto-reconnects on startup

3. **Protocol:**
   - JSON messages with newline delimiters
   - New connection per command
   - Simple request/response pattern

## License

This project is for educational purposes only. Amiibo is a trademark of Nintendo. This tool is not affiliated with or endorsed by Nintendo.