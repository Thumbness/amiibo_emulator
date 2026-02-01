"""
Amiibo GUI Client for Windows

Tkinter GUI that connects to headless Raspberry Pi server.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import socket
import json
import threading
import time

class AmiiboClient:
    """Network client for Amiibo server"""
    
    def __init__(self, host, port=5555):
        self.host = host
        self.port = port
        self.connected = False
    
    def connect(self):
        """Test connection to server"""
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            test_socket.connect((self.host, self.port))
            test_socket.close()
            self.connected = True
            return True
        except Exception as e:
            self.connected = False
            raise Exception(f"Connection failed: {e}")
    
    def send_command(self, command):
        """Send command and get response (new connection each time)"""
        if not self.connected:
            raise Exception("Not connected to server")
        
        sock = None
        try:
            # Create new connection for each command
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((self.host, self.port))
            
            # Send command
            message = json.dumps(command).encode('utf-8')
            sock.sendall(message)
            
            # Read until newline delimiter
            data = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
                
                # Check if we have complete message
                if b'\n' in data:
                    # Get first complete message
                    lines = data.split(b'\n', 1)
                    message_data = lines[0]
                    
                    # Parse JSON
                    response = json.loads(message_data.decode('utf-8'))
                    return response
            
            raise Exception("No response received")
            
        except socket.timeout:
            raise Exception("Response timeout")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON parse error: {e}")
        except Exception as e:
            raise Exception(f"Communication error: {e}")
        finally:
            if sock:
                sock.close()
    
    def disconnect(self):
        """Disconnect from server"""
        self.connected = False


class AmiiboGUI:
    """Tkinter GUI for Amiibo system"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Amiibo Writer - Remote Control")
        self.root.geometry("800x600")
        
        self.client = None
        self.state = None
        self.update_thread = None
        self.running = False
        
        self.create_widgets()
        self.show_connection_dialog()
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_label = ttk.Label(main_frame, text="Not connected", relief=tk.SUNKEN)
        self.status_label.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Left panel - Categories
        left_frame = ttk.LabelFrame(main_frame, text="Categories", padding="5")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.category_listbox = tk.Listbox(left_frame, height=20, width=30)
        self.category_listbox.pack(fill=tk.BOTH, expand=True)
        self.category_listbox.bind('<<ListboxSelect>>', self.on_category_select)
        
        # Middle panel - Characters
        middle_frame = ttk.LabelFrame(main_frame, text="Characters", padding="5")
        middle_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        
        self.character_listbox = tk.Listbox(middle_frame, height=20, width=30)
        self.character_listbox.pack(fill=tk.BOTH, expand=True)
        self.character_listbox.bind('<<ListboxSelect>>', self.on_character_select)
        
        # Right panel - Actions
        right_frame = ttk.LabelFrame(main_frame, text="Actions", padding="5")
        right_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        # Current Amiibo display
        ttk.Label(right_frame, text="Selected Amiibo:").pack(pady=(0, 5))
        self.amiibo_label = ttk.Label(right_frame, text="None", font=('Arial', 12, 'bold'))
        self.amiibo_label.pack(pady=(0, 20))
        
        # Write button
        self.write_button = ttk.Button(right_frame, text="Write to Tag", command=self.write_tag, state=tk.DISABLED)
        self.write_button.pack(fill=tk.X, pady=5)
        
        # Detect tag button
        self.detect_button = ttk.Button(right_frame, text="Detect Tag", command=self.detect_tag)
        self.detect_button.pack(fill=tk.X, pady=5)
        
        # Progress bar
        ttk.Label(right_frame, text="Write Progress:").pack(pady=(20, 5))
        self.progress_bar = ttk.Progressbar(right_frame, mode='determinate', maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status text
        ttk.Label(right_frame, text="Status:").pack(pady=(20, 5))
        self.status_text = scrolledtext.ScrolledText(right_frame, height=10, width=30)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(1, weight=1)
    
    def show_connection_dialog(self):
        """Show connection dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Connect to Raspberry Pi")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Raspberry Pi IP Address:").pack(pady=(20, 5))
        
        ip_entry = ttk.Entry(dialog, width=30)
        ip_entry.pack(pady=5)
        
        # Try to load saved hostname
        saved_host = self.load_hostname()
        ip_entry.insert(0, saved_host if saved_host else "thumbness")
        ip_entry.focus()
        
        # Auto-connect checkbox
        auto_connect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(dialog, text="Auto-connect on startup", variable=auto_connect_var).pack(pady=5)
        
        def connect():
            host = ip_entry.get().strip()
            if not host:
                messagebox.showerror("Error", "Please enter an IP address")
                return
            
            try:
                self.log("Connecting to " + host + "...")
                self.client = AmiiboClient(host)
                self.client.connect()
                self.log("✓ Connected!")
                self.status_label.config(text=f"Connected to {host}")
                
                # Save hostname if auto-connect is enabled
                if auto_connect_var.get():
                    self.save_hostname(host)
                
                dialog.destroy()
                self.start_updates()
                self.refresh_state()
            except Exception as e:
                messagebox.showerror("Connection Error", str(e))
                self.log(f"✗ Connection failed: {e}")
        
        ttk.Button(dialog, text="Connect", command=connect).pack(pady=10)
        
        # Bind Enter key
        ip_entry.bind('<Return>', lambda e: connect())
        
        # Try auto-connect if hostname is saved and auto-connect enabled
        if saved_host:
            def auto_connect():
                try:
                    self.log(f"Auto-connecting to {saved_host}...")
                    self.client = AmiiboClient(saved_host)
                    self.client.connect()
                    self.log("✓ Connected!")
                    self.status_label.config(text=f"Connected to {saved_host}")
                    dialog.destroy()
                    self.start_updates()
                    self.refresh_state()
                except Exception as e:
                    self.log(f"✗ Auto-connect failed: {e}")
            
            self.root.after(500, auto_connect)
    
    def save_hostname(self, hostname):
        """Save hostname to config file"""
        try:
            import os
            config_file = os.path.join(os.path.dirname(__file__), '.amiibo_config')
            with open(config_file, 'w') as f:
                f.write(hostname)
        except Exception as e:
            print(f"Failed to save hostname: {e}")
    
    def load_hostname(self):
        """Load hostname from config file"""
        try:
            import os
            config_file = os.path.join(os.path.dirname(__file__), '.amiibo_config')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            print(f"Failed to load hostname: {e}")
        return None
    
    def start_updates(self):
        """Start background update thread"""
        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
    
    def update_loop(self):
        """Background update loop"""
        last_state_str = None
        
        while self.running:
            try:
                if self.client and self.client.connected:
                    response = self.client.send_command({'cmd': 'get_state'})
                    if response.get('success'):
                        new_state = response.get('data')
                        # Only update UI if state actually changed
                        new_state_str = json.dumps(new_state, sort_keys=True)
                        if new_state_str != last_state_str:
                            self.state = new_state
                            last_state_str = new_state_str
                            self.root.after(0, self.update_ui)
            except Exception as e:
                # Only log errors occasionally to avoid spam
                pass
            
            time.sleep(1.0)  # Slower polling - 1 second instead of 0.5
    
    def update_ui(self):
        """Update UI with current state"""
        if not self.state:
            return
        
        # Update categories
        categories = self.state.get('categories', [])
        current_cat = self.state.get('current_category', 0)
        
        if len(categories) != self.category_listbox.size():
            self.category_listbox.delete(0, tk.END)
            for cat in categories:
                self.category_listbox.insert(tk.END, cat.get('name', 'Unknown'))
        
        if current_cat < self.category_listbox.size():
            self.category_listbox.selection_clear(0, tk.END)
            self.category_listbox.selection_set(current_cat)
            self.category_listbox.see(current_cat)
        
        # Update characters
        characters = self.state.get('characters', [])
        current_char = self.state.get('current_character', 0)
        
        self.character_listbox.delete(0, tk.END)
        for char in characters:
            # Use 'character' key, fallback to 'name', then 'Unknown'
            char_name = char.get('character', char.get('name', 'Unknown'))
            self.character_listbox.insert(tk.END, char_name)
        
        if current_char < self.character_listbox.size():
            self.character_listbox.selection_clear(0, tk.END)
            self.character_listbox.selection_set(current_char)
            self.character_listbox.see(current_char)
        
        # Update current Amiibo
        amiibo = self.state.get('current_amiibo')
        if amiibo:
            self.amiibo_label.config(text=amiibo)
            self.write_button.config(state=tk.NORMAL)
        else:
            self.amiibo_label.config(text="None")
            self.write_button.config(state=tk.DISABLED)
        
        # Update progress
        progress = self.state.get('write_progress', 0)
        self.progress_bar['value'] = progress
        
        # Update status
        status = self.state.get('status', 'idle')
        if status == 'writing':
            self.log(f"Writing... {progress}%")
        elif status == 'write_complete':
            self.log("✓ Write complete!")
        elif status == 'write_error':
            self.log("✗ Write failed!")
    
    def refresh_state(self):
        """Manually refresh state"""
        try:
            response = self.client.send_command({'cmd': 'get_state'})
            if response.get('success'):
                self.state = response.get('data')
                self.update_ui()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh: {e}")
    
    def on_category_select(self, event):
        """Handle category selection"""
        selection = self.category_listbox.curselection()
        if selection:
            index = selection[0]
            try:
                response = self.client.send_command({
                    'cmd': 'set_category',
                    'index': index
                })
                if response.get('success'):
                    self.log(f"Selected category: {index}")
                    # Update will happen in background thread
            except Exception as e:
                self.log(f"Error: {e}")
    
    def on_character_select(self, event):
        """Handle character selection"""
        selection = self.character_listbox.curselection()
        if selection:
            index = selection[0]
            try:
                # First set the character index
                response = self.client.send_command({
                    'cmd': 'set_character',
                    'index': index
                })
                # Then load it
                if response.get('success'):
                    response = self.client.send_command({
                        'cmd': 'select_character',
                        'index': index
                    })
                    if response.get('success'):
                        self.log(f"Loaded character: {index}")
            except Exception as e:
                self.log(f"Error: {e}")
    
    def write_tag(self):
        """Write to tag"""
        if not self.state or not self.state.get('current_amiibo'):
            messagebox.showwarning("Warning", "No Amiibo selected")
            return
        
        result = messagebox.askyesno(
            "Write Tag",
            f"Write '{self.state.get('current_amiibo')}' to tag?\n\nPlace NTAG215 tag on reader now."
        )
        
        if result:
            try:
                self.log("Starting write...")
                self.write_button.config(state=tk.DISABLED)
                
                # Send write command in background
                def write_thread():
                    try:
                        response = self.client.send_command({'cmd': 'write_tag'})
                        if response.get('success'):
                            self.root.after(0, lambda: self.log("✓ Write successful!"))
                        else:
                            self.root.after(0, lambda: self.log("✗ Write failed!"))
                    except Exception as e:
                        self.root.after(0, lambda: self.log(f"✗ Error: {e}"))
                    finally:
                        self.root.after(0, lambda: self.write_button.config(state=tk.NORMAL))
                
                threading.Thread(target=write_thread, daemon=True).start()
                
            except Exception as e:
                self.log(f"Error: {e}")
                self.write_button.config(state=tk.NORMAL)
    
    def detect_tag(self):
        """Detect if tag is present"""
        try:
            self.log("Detecting tag...")
            response = self.client.send_command({'cmd': 'detect_tag'})
            if response.get('success'):
                if response.get('detected'):
                    self.log("✓ Tag detected!")
                    messagebox.showinfo("Tag Detection", "Tag detected!")
                else:
                    self.log("✗ No tag detected")
                    messagebox.showwarning("Tag Detection", "No tag detected")
        except Exception as e:
            self.log(f"Error: {e}")
            messagebox.showerror("Error", str(e))
    
    def log(self, message):
        """Log message to status text"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
    
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        if self.client:
            self.client.disconnect()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = AmiiboGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
