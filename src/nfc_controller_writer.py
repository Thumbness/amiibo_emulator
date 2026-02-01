"""
PN532 NFC Controller for Writing NTAG215 Tags

Implements tag writing for rewritable Amiibo system.
"""

import time
import smbus2
import RPi.GPIO as GPIO

class NFCWriter:
    """PN532 controller for writing NTAG215 tags"""
    
    # PN532 Commands
    CMD_GETFIRMWAREVERSION = 0x02
    CMD_SAMCONFIGURATION = 0x14
    CMD_INLISTPASSIVETARGET = 0x4A
    CMD_INDATAEXCHANGE = 0x40
    
    # NTAG215 Commands
    NTAG_CMD_READ = 0x30
    NTAG_CMD_WRITE = 0xA2
    
    # Response codes
    PN532_PREAMBLE = 0x00
    PN532_STARTCODE1 = 0x00
    PN532_STARTCODE2 = 0xFF
    PN532_POSTAMBLE = 0x00
    PN532_HOSTTOPN532 = 0xD4
    PN532_PN532TOHOST = 0xD5
    
    def __init__(self, i2c_bus=1, shared_i2c=None):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Use shared I2C bus if provided
        if shared_i2c:
            self.i2c = shared_i2c
            self.owns_i2c = False
        else:
            self.i2c = smbus2.SMBus(i2c_bus)
            self.owns_i2c = True
        
        self.address = 0x24
        self.current_amiibo = None
        
        print("PN532 NFC Writer initializing...")
        
        # Test communication
        version = self.get_firmware_version()
        if version:
            print(f"✓ PN532 Firmware: v{version[1]}.{version[2]}")
        else:
            raise RuntimeError("PN532 communication failed")
        
        # Configure SAM
        self._configure_sam()
    
    def get_firmware_version(self):
        """Get firmware version"""
        try:
            cmd = [0x00, 0x00, 0xFF, 0x02, 0xFE, 0xD4, 0x02, 0x2A, 0x00]
            msg = smbus2.i2c_msg.write(self.address, cmd)
            self.i2c.i2c_rdwr(msg)
            
            time.sleep(0.05)
            
            msg = smbus2.i2c_msg.read(self.address, 20)
            self.i2c.i2c_rdwr(msg)
            response = list(msg)
            
            if len(response) > 12 and response[0] == 0x01:
                return (response[9], response[10], response[11], response[12])
            elif len(response) > 12:
                return (response[8], response[9], response[10], response[11])
            return None
        except Exception as e:
            print(f"Error getting firmware: {e}")
            return None
    
    def _configure_sam(self):
        """Configure SAM for normal mode"""
        try:
            cmd = self._build_command(self.CMD_SAMCONFIGURATION, [0x01, 0x14, 0x01])
            self._send_command(cmd)
            time.sleep(0.05)
            response = self._read_response()
            
            if response and len(response) > 0:
                print("✓ SAM configured for tag writing")
                return True
            else:
                print("⚠ SAM configuration may have failed")
                return False
        except Exception as e:
            print(f"Error configuring SAM: {e}")
            return False
    
    def _build_command(self, cmd, data=None):
        """Build PN532 command frame"""
        if data is None:
            data = []
        
        length = len(data) + 1
        lcs = (~length + 1) & 0xFF
        
        frame = [
            self.PN532_PREAMBLE,
            self.PN532_STARTCODE1,
            self.PN532_STARTCODE2,
            length,
            lcs,
            self.PN532_HOSTTOPN532,
            cmd
        ]
        
        frame.extend(data)
        
        dcs = (~sum([self.PN532_HOSTTOPN532, cmd] + data) + 1) & 0xFF
        frame.append(dcs)
        frame.append(self.PN532_POSTAMBLE)
        
        return frame
    
    def _send_command(self, cmd):
        """Send command to PN532"""
        try:
            time.sleep(0.01)
            msg = smbus2.i2c_msg.write(self.address, cmd)
            self.i2c.i2c_rdwr(msg)
            time.sleep(0.01)
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
    
    def _read_response(self, length=64):
        """Read response from PN532"""
        try:
            time.sleep(0.05)
            msg = smbus2.i2c_msg.read(self.address, length)
            self.i2c.i2c_rdwr(msg)
            response = list(msg)
            
            if response[0] == 0x01:
                response = response[1:]
            
            return response
        except Exception as e:
            print(f"Error reading response: {e}")
            return None
    
    def detect_tag(self):
        """Detect if an NTAG215 tag is present"""
        try:
            print("Detecting tag...")
            # InListPassiveTarget: 1 card, 106 kbps type A
            cmd = self._build_command(self.CMD_INLISTPASSIVETARGET, [0x01, 0x00])
            
            if not self._send_command(cmd):
                print("Failed to send detect command")
                return None
            
            time.sleep(0.2)  # Longer wait for tag detection
            response = self._read_response()
            
            if not response:
                print("No response from PN532")
                return None
            
            # Debug: show response
            print(f"Response length: {len(response)}")
            print(f"Response: {bytes(response[:20]).hex()}")
            
            # Parse response - format varies, try different offsets
            # Look for number of targets byte
            for offset in range(min(10, len(response))):
                if response[offset] > 0 and response[offset] < 5:  # Reasonable number of tags
                    # Try to extract UID
                    try:
                        uid_offset = offset + 5
                        if uid_offset < len(response):
                            uid_length = response[uid_offset]
                            if 4 <= uid_length <= 10:  # Valid UID length
                                uid = bytes(response[uid_offset+1:uid_offset+1+uid_length])
                                if len(uid) == uid_length:
                                    print(f"✓ Tag detected: UID = {uid.hex().upper()}")
                                    return uid
                    except:
                        continue
            
            print("No tag detected (no valid UID found in response)")
            return None
            
        except Exception as e:
            print(f"Error detecting tag: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def write_page(self, page_num, data):
        """Write 4 bytes to a specific page"""
        try:
            if len(data) != 4:
                raise ValueError("Page data must be exactly 4 bytes")
            
            # InDataExchange: write command
            cmd_data = [0x01, self.NTAG_CMD_WRITE, page_num] + list(data)
            cmd = self._build_command(self.CMD_INDATAEXCHANGE, cmd_data)
            
            if not self._send_command(cmd):
                return False
            
            time.sleep(0.05)
            response = self._read_response()
            
            # Check for success (response should contain 0xD5 0x41 0x00)
            if response and len(response) > 8:
                if response[6] == 0xD5 and response[7] == 0x41 and response[8] == 0x00:
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error writing page {page_num}: {e}")
            return False
    
    def write_amiibo(self, amiibo_data, progress_callback=None):
        """Write Amiibo data to NTAG215 tag"""
        try:
            print("Starting Amiibo write...")
            
            # Get raw data
            raw_data = amiibo_data.get('raw_data', b'')
            if len(raw_data) < 540:
                print(f"Invalid Amiibo data size: {len(raw_data)} bytes")
                return False
            
            # Detect tag
            uid = self.detect_tag()
            if not uid:
                print("✗ No tag detected - place tag on reader")
                return False
            
            # Write pages (NTAG215 has 135 pages, 4 bytes each)
            # Pages 0-2 are UID (read-only on real tags, but we write for completeness)
            # Pages 3-129 contain Amiibo data
            # Pages 130-134 are configuration/lock bytes
            
            total_pages = 135
            success_count = 0
            
            for page in range(4, 130):  # Write main data pages (skip UID pages 0-2)
                offset = page * 4
                page_data = raw_data[offset:offset+4]
                
                if len(page_data) < 4:
                    page_data = page_data + b'\x00' * (4 - len(page_data))
                
                if self.write_page(page, page_data):
                    success_count += 1
                    if progress_callback:
                        progress = int((page - 4) / (130 - 4) * 100)
                        progress_callback(progress)
                else:
                    print(f"✗ Failed to write page {page}")
                    return False
                
                # Small delay between writes
                time.sleep(0.01)
            
            print(f"✓ Successfully wrote {success_count} pages")
            return True
            
        except Exception as e:
            print(f"Error writing Amiibo: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_amiibo(self, file_path):
        """Load Amiibo from file"""
        try:
            import os
            filename = os.path.basename(file_path)
            character_name = filename.replace('.nfc', '').replace('_', ' ')
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            if content.startswith('Filetype: Flipper'):
                print("Detected Flipper Zero format")
                self.current_amiibo = self._parse_flipper_format(content, character_name)
                return self.current_amiibo is not None
            else:
                print("Unsupported format")
                return False
                
        except Exception as e:
            print(f"Error loading Amiibo: {e}")
            return False
    
    def _parse_flipper_format(self, content, character_name):
        """Parse Flipper Zero .nfc format"""
        lines = content.split('\n')
        uid_bytes = b''
        data_pages = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('UID:'):
                hex_str = line.split(':', 1)[1].strip()
                uid_bytes = bytes.fromhex(hex_str.replace(' ', ''))
                print(f"Found UID in file: {uid_bytes.hex().upper()}")
            elif line.startswith('Page '):
                parts = line.split(':', 1)
                if len(parts) >= 2:
                    page_num = int(parts[0].split()[1])
                    hex_data = parts[1].strip()
                    data_pages[page_num] = bytes.fromhex(hex_data.replace(' ', ''))
        
        if not uid_bytes:
            raise ValueError("No UID found in Flipper format file")
        
        # Reconstruct raw data from pages
        raw_data = bytearray(540)
        for page_num, page_data in data_pages.items():
            offset = page_num * 4
            if offset + len(page_data) <= len(raw_data):
                raw_data[offset:offset+len(page_data)] = page_data
        
        return {
            'raw_data': bytes(raw_data),
            'uid': uid_bytes.hex().upper(),
            'character': character_name
        }
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.owns_i2c:
                self.i2c.close()
            GPIO.cleanup()
        except:
            pass


class AmiiboWriter:
    """Amiibo writer with tag detection and writing"""
    
    def __init__(self, i2c_bus=1, shared_i2c=None):
        self.nfc_writer = NFCWriter(i2c_bus, shared_i2c)
        self.current_amiibo = None
    
    def load_amiibo(self, file_path):
        """Load Amiibo from file"""
        if self.nfc_writer.load_amiibo(file_path):
            self.current_amiibo = self.nfc_writer.current_amiibo
            print(f"✓ Loaded: {self.current_amiibo.get('character', 'Unknown')}")
            return True
        return False
    
    def detect_tag(self):
        """Detect if a tag is present"""
        return self.nfc_writer.detect_tag() is not None
    
    def write_to_tag(self, progress_callback=None):
        """Write current Amiibo to tag"""
        if not self.current_amiibo:
            print("No Amiibo loaded")
            return False
        
        print(f"Writing {self.current_amiibo.get('character', 'Unknown')} to tag...")
        return self.nfc_writer.write_amiibo(self.current_amiibo, progress_callback)
    
    def cleanup(self):
        """Cleanup resources"""
        self.nfc_writer.cleanup()
