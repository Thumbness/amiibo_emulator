#!/usr/bin/env python3
"""
Headless Amiibo Server for Raspberry Pi

Runs without LCD - controlled via network API.
"""

import time
import json
import socket
import threading
from amiibo_emulator.src.nfc_controller_writer import AmiiboWriter
from amiibo_emulator.src.file_manager import FileManager
import RPi.GPIO as GPIO

class AmiiboServer:
    """Headless Amiibo server with network API"""
    
    def __init__(self, port=5555):
        self.port = port
        self.running = False
        self.server_socket = None
        
        # Initialize components (no LCD!)
        print("Initializing headless Amiibo server...")
        self.file_manager = FileManager()
        self.nfc_writer = AmiiboWriter(i2c_bus=1)
        
        # State
        self.current_category = 0
        self.current_character = 0
        self.current_amiibo = None
        self.write_progress = 0
        self.status = "idle"
        
        # Setup GPIO (minimal - no buttons needed)
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        print(f"✓ Server initialized on port {self.port}")
    
    def get_state(self):
        """Get current state"""
        categories = self.file_manager.get_categories()
        characters = []
        
        if categories and self.current_category < len(categories):
            category_id = categories[self.current_category]['id']
            characters = self.file_manager.get_characters(category_id)
        
        return {
            'status': self.status,
            'categories': categories,
            'current_category': self.current_category,
            'characters': characters,
            'current_character': self.current_character,
            'current_amiibo': self.current_amiibo.get('character', None) if self.current_amiibo else None,
            'write_progress': self.write_progress
        }
    
    def handle_command(self, command):
        """Handle command from client"""
        cmd = command.get('cmd')
        
        if cmd == 'get_state':
            return {'success': True, 'data': self.get_state()}
        
        elif cmd == 'set_category':
            index = command.get('index', 0)
            categories = self.file_manager.get_categories()
            if 0 <= index < len(categories):
                self.current_category = index
                self.current_character = 0  # Reset character selection
            return {'success': True, 'data': self.get_state()}
        
        elif cmd == 'set_character':
            index = command.get('index', 0)
            categories = self.file_manager.get_categories()
            if categories:
                category_id = categories[self.current_category]['id']
                characters = self.file_manager.get_characters(category_id)
                if 0 <= index < len(characters):
                    self.current_character = index
            return {'success': True, 'data': self.get_state()}
        
        elif cmd == 'select_character':
            index = command.get('index', self.current_character)
            self.current_character = index
            self._load_character()
            return {'success': True, 'data': self.get_state()}
        
        elif cmd == 'write_tag':
            success = self._write_tag()
            return {'success': success, 'data': self.get_state()}
        
        elif cmd == 'detect_tag':
            uid = self.nfc_writer.nfc_writer.detect_tag()
            detected = uid is not None and len(uid) > 0
            return {'success': True, 'detected': detected}
        
        else:
            return {'success': False, 'error': 'Unknown command'}
    
    def _load_character(self):
        """Load selected character"""
        categories = self.file_manager.get_categories()
        if not categories:
            return False
        
        category_id = categories[self.current_category]['id']
        characters = self.file_manager.get_characters(category_id)
        
        if not characters or self.current_character >= len(characters):
            return False
        
        character = characters[self.current_character]
        file_path = character['path']
        
        if self.nfc_writer.load_amiibo(file_path):
            self.current_amiibo = self.nfc_writer.current_amiibo
            print(f"Loaded: {self.current_amiibo.get('character', 'Unknown')}")
            return True
        return False
    
    def _write_tag(self):
        """Write to tag"""
        if not self.current_amiibo:
            self._load_character()
            if not self.current_amiibo:
                return False
        
        self.status = "writing"
        self.write_progress = 0
        
        def progress_callback(progress):
            self.write_progress = progress
        
        try:
            success = self.nfc_writer.write_to_tag(progress_callback)
            self.status = "write_complete" if success else "write_error"
            time.sleep(2)
            self.status = "idle"
            return success
        except Exception as e:
            print(f"Write error: {e}")
            self.status = "write_error"
            time.sleep(2)
            self.status = "idle"
            return False
    
    def handle_client(self, client_socket, address):
        """Handle client connection"""
        print(f"Client connected: {address}")
        
        try:
            while self.running:
                # Receive command
                data = client_socket.recv(4096)
                if not data:
                    break
                
                try:
                    command = json.loads(data.decode('utf-8'))
                    response = self.handle_command(command)
                    response_data = json.dumps(response).encode('utf-8')
                    
                    # Send response with newline delimiter
                    client_socket.sendall(response_data + b'\n')
                    
                except json.JSONDecodeError:
                    error_response = {'success': False, 'error': 'Invalid JSON'}
                    response_data = json.dumps(error_response).encode('utf-8')
                    client_socket.sendall(response_data + b'\n')
                except Exception as e:
                    error_response = {'success': False, 'error': str(e)}
                    response_data = json.dumps(error_response).encode('utf-8')
                    client_socket.sendall(response_data + b'\n')
        
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            client_socket.close()
            print(f"Client disconnected: {address}")
    
    def start(self):
        """Start server"""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        
        print(f"✓ Server listening on port {self.port}")
        print("Waiting for client connections...")
        
        try:
            while self.running:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        self.nfc_writer.cleanup()
        GPIO.cleanup()
        print("Server stopped")

def main():
    print("=" * 60)
    print("Headless Amiibo Server")
    print("=" * 60)
    print()
    
    server = AmiiboServer(port=5555)
    
    try:
        server.start()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        server.stop()

if __name__ == "__main__":
    main()
