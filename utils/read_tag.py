#!/usr/bin/env python3
"""
Simple NFC Tag Reader

Reads and displays information from NTAG215 tags.
"""

import time
import smbus2

class SimpleNFCReader:
    """Simple PN532 reader for NTAG215 tags"""
    
    CMD_GETFIRMWAREVERSION = 0x02
    CMD_SAMCONFIGURATION = 0x14
    CMD_INLISTPASSIVETARGET = 0x4A
    CMD_INDATAEXCHANGE = 0x40
    NTAG_CMD_READ = 0x30
    
    def __init__(self, i2c_bus=1):
        self.i2c = smbus2.SMBus(i2c_bus)
        self.address = 0x24
        
        print("Initializing PN532...")
        version = self.get_firmware_version()
        if version:
            print(f"✓ PN532 Firmware: v{version[1]}.{version[2]}")
        else:
            raise RuntimeError("PN532 communication failed")
        
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
            print(f"Error: {e}")
            return None
    
    def _configure_sam(self):
        """Configure SAM"""
        cmd = self._build_command(self.CMD_SAMCONFIGURATION, [0x01, 0x14, 0x01])
        self._send_command(cmd)
        time.sleep(0.05)
        self._read_response()
        print("✓ SAM configured")
    
    def _build_command(self, cmd, data=None):
        """Build PN532 command frame"""
        if data is None:
            data = []
        
        length = len(data) + 1
        lcs = (~length + 1) & 0xFF
        
        frame = [0x00, 0x00, 0xFF, length, lcs, 0xD4, cmd]
        frame.extend(data)
        
        dcs = (~sum([0xD4, cmd] + data) + 1) & 0xFF
        frame.append(dcs)
        frame.append(0x00)
        
        return frame
    
    def _send_command(self, cmd):
        """Send command"""
        time.sleep(0.01)
        msg = smbus2.i2c_msg.write(self.address, cmd)
        self.i2c.i2c_rdwr(msg)
        time.sleep(0.01)
    
    def _read_response(self, length=64):
        """Read response"""
        time.sleep(0.05)
        msg = smbus2.i2c_msg.read(self.address, length)
        self.i2c.i2c_rdwr(msg)
        response = list(msg)
        if response[0] == 0x01:
            response = response[1:]
        return response
    
    def detect_tag(self):
        """Detect tag and return UID"""
        print("\nDetecting tag...")
        cmd = self._build_command(self.CMD_INLISTPASSIVETARGET, [0x01, 0x00])
        self._send_command(cmd)
        time.sleep(0.2)
        response = self._read_response()
        
        if not response:
            print("✗ No response from PN532")
            return None
        
        print(f"Response: {bytes(response[:30]).hex()}")
        
        # Try to find UID in response
        for offset in range(min(15, len(response))):
            if response[offset] > 0 and response[offset] < 5:
                try:
                    uid_offset = offset + 5
                    if uid_offset < len(response):
                        uid_length = response[uid_offset]
                        if 4 <= uid_length <= 10:
                            uid = bytes(response[uid_offset+1:uid_offset+1+uid_length])
                            if len(uid) == uid_length:
                                return uid
                except:
                    continue
        
        print("✗ No tag detected")
        return None
    
    def read_page(self, page_num):
        """Read a page (4 bytes) from tag"""
        cmd_data = [0x01, self.NTAG_CMD_READ, page_num]
        cmd = self._build_command(self.CMD_INDATAEXCHANGE, cmd_data)
        self._send_command(cmd)
        time.sleep(0.05)
        response = self._read_response()
        
        # Extract data from response
        if response and len(response) > 10:
            # Data starts after header
            for i in range(len(response) - 16):
                if response[i] == 0xD5 and response[i+1] == 0x41 and response[i+2] == 0x00:
                    return bytes(response[i+3:i+19])  # 16 bytes (4 pages)
        return None
    
    def read_tag_info(self):
        """Read and display tag information"""
        uid = self.detect_tag()
        if not uid:
            return False
        
        print(f"\n✓ Tag detected!")
        print(f"  UID: {uid.hex().upper()}")
        print(f"  UID Length: {len(uid)} bytes")
        
        # Read first few pages
        print("\nReading tag data...")
        print("=" * 60)
        
        for page in range(0, 20):  # Read first 20 pages
            data = self.read_page(page)
            if data:
                # Show 4 pages at a time (16 bytes)
                for i in range(4):
                    page_num = page + i
                    offset = i * 4
                    page_data = data[offset:offset+4]
                    hex_str = ' '.join(f'{b:02X}' for b in page_data)
                    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in page_data)
                    print(f"Page {page_num:3d}: {hex_str}  {ascii_str}")
                break  # Only need one read for 4 pages
            else:
                print(f"Page {page:3d}: Failed to read")
                break
        
        print("=" * 60)
        
        # Check if it looks like an Amiibo
        data = self.read_page(0)
        if data:
            # Check for Amiibo signature (pages 21-22 contain game/character ID)
            amiibo_data = self.read_page(21)
            if amiibo_data:
                game_id = amiibo_data[2:4]
                char_id = amiibo_data[0:2]
                print(f"\nAmiibo Info:")
                print(f"  Character ID: {char_id.hex().upper()}")
                print(f"  Game ID: {game_id.hex().upper()}")
        
        return True
    
    def cleanup(self):
        """Cleanup"""
        self.i2c.close()

def main():
    print("=" * 60)
    print("NFC Tag Reader")
    print("=" * 60)
    print()
    
    try:
        reader = SimpleNFCReader()
        
        print("\nPlace your NTAG215 tag on the PN532 reader...")
        print("Press Ctrl+C to exit")
        print()
        
        while True:
            if reader.read_tag_info():
                print("\n✓ Read complete!")
                break
            else:
                print("\nNo tag detected. Place tag on reader and press Enter...")
                input()
        
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            reader.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()
