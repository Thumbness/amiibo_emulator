#!/usr/bin/env python3
"""
Continuous NFC Tag Detection

Continuously polls for tags - easier to test placement.
"""

import time
import smbus2
import sys

class ContinuousDetector:
    """Continuous tag detector"""
    
    def __init__(self):
        self.i2c = smbus2.SMBus(1)
        self.address = 0x24
        
        print("Initializing PN532...")
        self._init_pn532()
        print("✓ Ready to detect tags")
        print()
    
    def _init_pn532(self):
        """Initialize PN532"""
        # Get firmware version
        cmd = [0x00, 0x00, 0xFF, 0x02, 0xFE, 0xD4, 0x02, 0x2A, 0x00]
        msg = smbus2.i2c_msg.write(self.address, cmd)
        self.i2c.i2c_rdwr(msg)
        time.sleep(0.05)
        
        msg = smbus2.i2c_msg.read(self.address, 20)
        self.i2c.i2c_rdwr(msg)
        response = list(msg)
        
        if len(response) > 10:
            if response[0] == 0x01:
                ver = response[10]
                rev = response[11]
            else:
                ver = response[9]
                rev = response[10]
            print(f"  Firmware: v{ver}.{rev}")
        
        # Configure SAM
        cmd = [0x00, 0x00, 0xFF, 0x04, 0xFC, 0xD4, 0x14, 0x01, 0x14, 0x01, 0x02, 0x00]
        msg = smbus2.i2c_msg.write(self.address, cmd)
        self.i2c.i2c_rdwr(msg)
        time.sleep(0.05)
        
        msg = smbus2.i2c_msg.read(self.address, 20)
        self.i2c.i2c_rdwr(msg)
    
    def detect_once(self):
        """Try to detect a tag once"""
        try:
            # InListPassiveTarget command
            cmd = [0x00, 0x00, 0xFF, 0x04, 0xFC, 0xD4, 0x4A, 0x01, 0x00, 0xE1, 0x00]
            msg = smbus2.i2c_msg.write(self.address, cmd)
            self.i2c.i2c_rdwr(msg)
            
            time.sleep(0.15)  # Wait for tag detection
            
            msg = smbus2.i2c_msg.read(self.address, 64)
            self.i2c.i2c_rdwr(msg)
            response = list(msg)
            
            # Skip ready byte
            if response[0] == 0x01:
                response = response[1:]
            
            # Check if we got a valid response with tag data
            # Look for the response pattern
            if len(response) > 15:
                # Find number of tags
                for i in range(min(12, len(response))):
                    if response[i] == 0x01:  # 1 tag found
                        # Try to extract UID
                        try:
                            # UID length is usually 5-7 bytes after some offset
                            for offset in range(i, min(i+10, len(response))):
                                uid_len = response[offset]
                                if 4 <= uid_len <= 10:
                                    uid_start = offset + 1
                                    if uid_start + uid_len <= len(response):
                                        uid = bytes(response[uid_start:uid_start+uid_len])
                                        # Verify it's not all zeros or all 0x80
                                        if uid != b'\x00' * len(uid) and uid != b'\x80' * len(uid):
                                            return uid
                        except:
                            pass
            
            return None
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def run(self):
        """Continuously detect tags"""
        print("=" * 60)
        print("Continuous Tag Detection")
        print("=" * 60)
        print()
        print("Place your NTAG215 tag on the PN532 antenna...")
        print("The script will continuously check for tags.")
        print("Press Ctrl+C to exit")
        print()
        
        last_uid = None
        no_tag_count = 0
        
        try:
            while True:
                uid = self.detect_once()
                
                if uid:
                    if uid != last_uid:
                        print(f"\n✓ TAG DETECTED!")
                        print(f"  UID: {uid.hex().upper()}")
                        print(f"  Length: {len(uid)} bytes")
                        print(f"  Type: {'NTAG215' if len(uid) == 7 else 'Unknown'}")
                        print()
                        last_uid = uid
                        no_tag_count = 0
                    sys.stdout.write(".")
                    sys.stdout.flush()
                else:
                    if last_uid is not None:
                        print("\n✗ Tag removed")
                        last_uid = None
                    no_tag_count += 1
                    if no_tag_count % 10 == 0:
                        sys.stdout.write(".")
                        sys.stdout.flush()
                
                time.sleep(0.3)  # Check every 300ms
                
        except KeyboardInterrupt:
            print("\n\nExiting...")
        finally:
            self.i2c.close()

if __name__ == "__main__":
    detector = ContinuousDetector()
    detector.run()
