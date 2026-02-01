"""
Main Application for Amiibo Writer - Raspberry Pi Version

Rewritable Amiibo system - write any Amiibo to a single NTAG215 tag!
"""

import time
import gc
import signal
import sys

# Force unbuffered output for immediate debug logs
sys.stdout = sys.stderr = open(sys.stdout.fileno(), 'w', buffering=1)

from amiibo_emulator.src.nfc_controller_writer import AmiiboWriter
from amiibo_emulator.src.file_manager import FileManager
from ui_controller_rpi import UIController
from amiibo_emulator.src.config_rpi import HardwareConfig, AppConfig

class AmiiboWriterApp:
    """Main Amiibo Writer Application for Raspberry Pi"""
    
    # UI States
    STATE_BROWSING = 0
    STATE_READY_TO_WRITE = 1
    STATE_WAITING_FOR_TAG = 2
    STATE_WRITING = 3
    STATE_WRITE_COMPLETE = 4
    STATE_WRITE_ERROR = 5
    
    def __init__(self):
        """Initialize the Amiibo Writer Application"""
        print("Initializing Amiibo Writer for Raspberry Pi...")
        print("Rewritable Amiibo System")
        print()
        
        # Initialize components
        self.file_manager = FileManager()
        
        # Initialize UI controller with I2C
        self.ui_controller = UIController(
            i2c_bus=HardwareConfig.I2C_BUS,
            button_pins=HardwareConfig.BUTTON_PINS,
            lcd_address=HardwareConfig.LCD_I2C_ADDRESS
        )
        
        # Initialize NFC writer with shared I2C bus
        self.nfc_writer = AmiiboWriter(
            i2c_bus=HardwareConfig.I2C_BUS,
            shared_i2c=self.ui_controller.lcd.bus if self.ui_controller.lcd_initialized else None
        )
        
        # Application state
        self.current_category_index = 0
        self.current_character_index = 0
        self.current_amiibo = None
        self.is_running = True
        self.last_activity = time.time()
        self.app_state = self.STATE_BROWSING
        self.write_progress = 0
        
        # Statistics
        self.write_count = 0
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print()
        print("=" * 50)
        print("Amiibo Writer initialized successfully!")
        print("=" * 50)
        
        # Display startup message
        self.ui_controller.display_text("Amiibo Writer", "Ready!")
        time.sleep(2)
        
        # Clear any button presses during startup
        self.ui_controller.check_buttons()
        print("Startup complete - ready for input")
    
    def _signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        print("\nShutdown signal received...")
        self.is_running = False
    
    def run(self):
        """Main application loop"""
        print("Starting main application loop...")
        
        # Force initial display update
        categories = self.file_manager.get_categories()
        if categories:
            self.ui_controller.current_state = self.ui_controller.STATE_CATEGORY_BROWSER
            self.ui_controller.selected_category = 0
            self.ui_controller.update_display(categories=categories)
            print(f"Displaying category: {categories[0]['name']}")
        
        time.sleep(0.5)
        last_update_time = time.time()
        
        while self.is_running:
            try:
                current_time = time.time()
                delta_time = current_time - last_update_time
                last_update_time = current_time
                
                # Update UI based on state
                self._update_ui()
                
                # Handle user input
                self._handle_user_input()
                
                # Garbage collection
                if current_time % 10 < delta_time:
                    gc.collect()
                
                # Small delay
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("Application interrupted by user")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)
    
    def _update_ui(self):
        """Update the user interface"""
        categories = self.file_manager.get_categories()
        characters = []
        
        # Get current characters if in character browser
        if self.ui_controller.current_state == self.ui_controller.STATE_CHARACTER_BROWSER:
            if categories:
                category_id = categories[self.current_category_index]['id']
                characters = self.file_manager.get_characters(category_id)
        
        # Update display based on app state
        if self.app_state == self.STATE_WAITING_FOR_TAG:
            self.ui_controller.display_text("Place tag on", "reader...")
        elif self.app_state == self.STATE_WRITING:
            char_name = self.current_amiibo.get('character', 'Unknown')[:12]
            self.ui_controller.display_text("Writing...", f"{char_name} {self.write_progress}%")
        elif self.app_state == self.STATE_WRITE_COMPLETE:
            self.ui_controller.display_text("Write Complete!", "Remove tag")
        elif self.app_state == self.STATE_WRITE_ERROR:
            self.ui_controller.display_text("Write Failed!", "Try again")
        else:
            # Normal browsing
            try:
                self.ui_controller.update_display(
                    categories=categories,
                    characters=characters,
                    current_amiibo=self.current_amiibo
                )
            except OSError as e:
                print(f"⚠ UI update skipped (I2C busy): {e}")
    
    def _handle_user_input(self):
        """Handle user input from buttons"""
        self.last_activity = time.time()
        
        categories = self.file_manager.get_categories()
        characters = []
        
        if self.ui_controller.current_state == self.ui_controller.STATE_CHARACTER_BROWSER:
            if categories:
                category_id = categories[self.current_category_index]['id']
                characters = self.file_manager.get_characters(category_id)
        
        action = self.ui_controller.handle_navigation(categories, characters)
        
        if action:
            self._process_action(action)
    
    def _process_action(self, action):
        """Process navigation actions"""
        action_type = action.get('type')
        
        if action_type == 'category_change':
            self.current_category_index = action['index']
            self.app_state = self.STATE_BROWSING
            print(f"Category changed to: {self.current_category_index}")
        
        elif action_type == 'enter_category':
            self.current_category_index = action['category_index']
            self.app_state = self.STATE_BROWSING
            print(f"Entering category: {self.current_category_index}")
        
        elif action_type == 'character_change':
            self.current_character_index = action['index']
            self.app_state = self.STATE_BROWSING
            print(f"Character changed to: {self.current_character_index}")
        
        elif action_type == 'select_character':
            self.current_character_index = action['character_index']
            self._load_selected_character()
            self.app_state = self.STATE_READY_TO_WRITE
            print(f"Selected character: {self.current_character_index}")
        
        elif action_type == 'transmit_character' or action_type == 'start_transmission':
            # Transmit button = Write button
            self.current_character_index = action.get('character_index', self.current_character_index)
            self._start_write_process()
        
        elif action_type == 'quick_transmit':
            self._start_write_process()
        
        elif action_type == 'back_to_characters':
            self.app_state = self.STATE_BROWSING
            self.ui_controller.current_state = self.ui_controller.STATE_CHARACTER_BROWSER
    
    def _load_selected_character(self):
        """Load the currently selected character"""
        categories = self.file_manager.get_categories()
        if not categories:
            return
        
        category_id = categories[self.current_category_index]['id']
        characters = self.file_manager.get_characters(category_id)
        
        if not characters:
            return
        
        character = characters[self.current_character_index]
        file_path = character['path']
        
        # Load Amiibo
        if self.nfc_writer.load_amiibo(file_path):
            self.current_amiibo = self.nfc_writer.current_amiibo
            print(f"Loaded: {self.current_amiibo.get('character', 'Unknown')}")
        else:
            print("Failed to load Amiibo")
    
    def _start_write_process(self):
        """Start the write process"""
        if not self.current_amiibo:
            # Try to load current selection
            self._load_selected_character()
            if not self.current_amiibo:
                print("No Amiibo loaded for writing")
                return
        
        print(f"Starting write process for: {self.current_amiibo.get('character', 'Unknown')}")
        self.app_state = self.STATE_WAITING_FOR_TAG
        self.ui_controller.display_text("Place tag on", "reader...")
        
        # Wait a moment for user to see message
        time.sleep(1)
        
        # Try to write
        self._write_to_tag()
    
    def _write_to_tag(self):
        """Write Amiibo to tag"""
        self.app_state = self.STATE_WRITING
        self.write_progress = 0
        
        def progress_callback(progress):
            self.write_progress = progress
            self._update_ui()
        
        try:
            if self.nfc_writer.write_to_tag(progress_callback):
                self.app_state = self.STATE_WRITE_COMPLETE
                self.write_count += 1
                print(f"✓ Write complete! Total writes: {self.write_count}")
                time.sleep(2)
                self.app_state = self.STATE_BROWSING
                self.ui_controller.current_state = self.ui_controller.STATE_CHARACTER_BROWSER
            else:
                self.app_state = self.STATE_WRITE_ERROR
                print("✗ Write failed")
                time.sleep(2)
                self.app_state = self.STATE_BROWSING
                self.ui_controller.current_state = self.ui_controller.STATE_CHARACTER_BROWSER
        except Exception as e:
            print(f"Error during write: {e}")
            self.app_state = self.STATE_WRITE_ERROR
            time.sleep(2)
            self.app_state = self.STATE_BROWSING
    
    def get_status(self):
        """Get application status"""
        return {
            'categories': len(self.file_manager.get_categories()),
            'current_category': self.current_category_index,
            'current_character': self.current_character_index,
            'current_amiibo': self.current_amiibo.get('character', 'None') if self.current_amiibo else 'None',
            'write_count': self.write_count,
            'app_state': self.app_state
        }
    
    def print_status(self):
        """Print current status"""
        status = self.get_status()
        print("\n=== Amiibo Writer Status ===")
        print(f"Categories: {status['categories']}")
        print(f"Current Category: {status['current_category']}")
        print(f"Current Character: {status['current_character']}")
        print(f"Current Amiibo: {status['current_amiibo']}")
        print(f"Total Writes: {status['write_count']}")
        print(f"App State: {status['app_state']}")
        print("============================\n")
    
    def stop(self):
        """Stop the application"""
        print("Stopping Amiibo Writer...")
        self.is_running = False
        self.ui_controller.enter_sleep_mode()
        
        # Cleanup resources
        try:
            self.nfc_writer.cleanup()
            self.ui_controller.cleanup()
        except Exception as e:
            print(f"Error during cleanup: {e}")

def main():
    """Main entry point"""
    app = None
    try:
        # Create and run application
        app = AmiiboWriterApp()
        
        # Print initial status
        app.print_status()
        
        # Run main loop
        app.run()
        
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if app:
            try:
                app.stop()
            except:
                pass
        print("Application terminated")

if __name__ == "__main__":
    main()
