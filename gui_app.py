import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import time
import random
import json
import os

# Try to import tray dependencies, fallback if not available
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

class EasyAPIGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Easy API Endpoints")
        self.root.geometry("300x200")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_main_window_close)
        
        # Initialize state variables FIRST
        self.server_running = False
        self.server_status = "STOPPED"
        self.endpoint_count = 0
        self.port = 9000
        self.uptime_start = None
        self.request_count = 0
        self.status_index = 0
        self.status_cycling = True
        self.open_dialogs = []  # Track open modal dialogs
        self.server_process = None  # Track server process
        self.tray_icon = None  # System tray icon
        self.is_minimized_to_tray = False
        
        # Dark theme colors
        self.bg_color = "#2b2b2b"  # Dark gray background
        self.root.configure(bg=self.bg_color)
        
        # Try to set dark title bar (Windows 10/11)
        try:
            self.root.tk.call('tk', 'windowingsystem')  # Check if we can modify window
            # This works on Windows with newer tkinter versions
            self.root.wm_attributes('-transparentcolor', '')
        except:
            pass
        
        # Load settings
        self.load_settings()
        
        # Set up system tray if available (AFTER initializing variables)
        if TRAY_AVAILABLE:
            self.create_tray_icon()
            
        # Auto-start server if enabled
        if self.auto_start:
            # Start server after a brief delay to let UI finish loading
            self.root.after(1000, self.auto_start_server)
        
        # Status messages to cycle through
        self.status_messages = [
            ("SERVER STOPPED", "red"),
            ("0 ENDPOINTS", "gray"),
            ("PORT 9000", "gray")
        ]
        
        self.setup_ui()
        self.start_status_cycling()
        
    def setup_ui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Left side - big start/stop button (2/3 width)
        self.start_stop_frame = tk.Frame(main_frame, bg="#404040", relief="solid", bd=1)
        self.start_stop_frame.place(x=0, y=0, width=184, height=184)
        
        self.start_stop_button = tk.Button(
            self.start_stop_frame,
            text="▶",
            font=("Arial", 96),
            bg="#6a4a4a",  # Desaturated red
            fg="#e0e0e0",  # Light gray text
            border=0,
            activebackground="#5a6d5a",
            command=self.toggle_server
        )
        self.start_stop_button.pack(fill="both", expand=True)
        self.start_stop_button.bind("<Enter>", self.on_button_enter)
        self.start_stop_button.bind("<Leave>", lambda e: self.hide_hover_text())
        
        # Right side frame (1/3 width)
        right_frame = tk.Frame(main_frame, bg=self.bg_color)
        right_frame.place(x=190, y=0, width=95, height=184)
        
        # Settings button (top 1/4)
        self.settings_button = tk.Button(
            right_frame,
            text="⚙",
            font=("Arial", 14),
            bg="#4a5a6a",  # Desaturated blue
            fg="#e0e0e0",
            border=0,
            activebackground="#5a6a7a",
            command=self.open_settings
        )
        self.settings_button.place(x=0, y=0, width=46, height=46)
        self.settings_button.bind("<Enter>", lambda e: self.show_hover_text("SETTINGS"))
        self.settings_button.bind("<Leave>", lambda e: self.hide_hover_text())
        
        # Logs button (top right of first 1/4)
        self.logs_button = tk.Button(
            right_frame,
            text="📄",
            font=("Arial", 18),
            bg="#6a6a4a",  # Desaturated yellow
            fg="#e0e0e0",
            border=0,
            activebackground="#7a7a5a",
            command=self.open_logs
        )
        self.logs_button.place(x=49, y=0, width=46, height=46)
        self.logs_button.bind("<Enter>", lambda e: self.show_hover_text("VIEW LOGS"))
        self.logs_button.bind("<Leave>", lambda e: self.hide_hover_text())
        
        # Folder button (middle 1/2)
        self.folder_button = tk.Button(
            right_frame,
            text="📁",
            font=("Arial", 32),
            bg="#6a5a4a",  # Desaturated coral
            fg="#e0e0e0",
            border=0,
            activebackground="#7a6a5a",
            command=self.open_folder
        )
        self.folder_button.place(x=0, y=49, width=95, height=92)
        self.folder_button.bind("<Enter>", lambda e: self.show_hover_text("OPEN ENDPOINTS"))
        self.folder_button.bind("<Leave>", lambda e: self.hide_hover_text())
        
        # Status line (bottom 1/4)
        self.status_frame = tk.Frame(right_frame, bg=self.bg_color)
        self.status_frame.place(x=0, y=144, width=95, height=40)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="SERVER STOPPED",
            font=("Arial", 10),
            fg="#ff6666",  # Soft red
            bg=self.bg_color,
            wraplength=90,
            justify="center"
        )
        self.status_label.pack(fill="both", expand=True)
        
    def toggle_server(self):
        """Toggle server start/stop"""
        if not self.server_running:
            self.start_server()
        else:
            self.stop_server()
            
    def start_server(self):
        """Start the server"""
        if self.server_process and self.server_process.poll() is None:
            return  # Server already running
            
        self.server_status = "STARTING..."
        self.update_status_display("STARTING...", "#ffaa66")  # Soft orange
        self.start_stop_button.config(text="⏸", bg="#6a5a4a")  # Desaturated orange
        
        # Start actual server process
        def startup():
            try:
                import subprocess
                import os
                
                # Get the full path to start_server.py
                script_path = os.path.join(os.getcwd(), "start_server.py")
                
                self.server_process = subprocess.Popen(
                    ["python", script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=os.getcwd(),
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                
                # Give it a moment to start
                time.sleep(3)
                
                # Check if process started successfully
                if self.server_process.poll() is None:
                    self.server_running = True
                    self.server_status = "RUNNING"
                    self.uptime_start = time.time()
                    self.endpoint_count = self.count_endpoint_files()
                    self.request_count = 0
                    
                    self.start_stop_button.config(text="⏸", bg="#4a6a4a")  # Desaturated green
                    self.update_status_messages()
                else:
                    # Server failed to start - get error output
                    stdout, stderr = self.server_process.communicate()
                    error_msg = stdout or stderr or "Unknown error"
                    
                    self.server_running = False
                    self.server_status = "FAILED"
                    self.start_stop_button.config(text="▶", bg="#6a4a4a")
                    self.update_status_display("START FAILED", "red")
                    print(f"Server startup failed with exit code {self.server_process.returncode}")
                    print(f"Error output: {error_msg}")
                    
            except Exception as e:
                self.server_running = False
                self.server_status = "ERROR"
                self.start_stop_button.config(text="▶", bg="#6a4a4a")
                self.update_status_display("START ERROR", "red")
                print(f"Error starting server: {e}")
            
        threading.Thread(target=startup, daemon=True).start()
        
    def stop_server(self):
        """Stop the server"""
        self.server_status = "STOPPING..."
        self.update_status_display("STOPPING...", "#ffaa66")  # Soft orange
        self.start_stop_button.config(text="⏸", bg="#6a5a4a")  # Desaturated orange
        
        # Stop actual server process
        def shutdown():
            try:
                if self.server_process and self.server_process.poll() is None:
                    # Terminate the process
                    self.server_process.terminate()
                    
                    # Give it time to terminate gracefully
                    time.sleep(1)
                    
                    # Force kill if it's still running
                    if self.server_process.poll() is None:
                        self.server_process.kill()
                        self.server_process.wait()
                
                self.server_running = False
                self.server_status = "STOPPED"
                self.uptime_start = None
                self.server_process = None
                
                self.start_stop_button.config(text="▶", bg="#6a4a4a")  # Back to desaturated red
                self.update_status_messages()
                
            except Exception as e:
                self.server_running = False
                self.server_status = "STOPPED"
                self.uptime_start = None
                self.server_process = None
                self.start_stop_button.config(text="▶", bg="#6a4a4a")
                self.update_status_messages()
                print(f"Error stopping server: {e}")
            
        threading.Thread(target=shutdown, daemon=True).start()
    
    def count_endpoint_files(self):
        """Count the number of endpoint files in the endpoints directory"""
        try:
            import glob
            import os
            
            endpoints_dir = getattr(self, 'endpoints_path', './endpoints')
            if not os.path.exists(endpoints_dir):
                return 0
                
            extensions = ['*.py', '*.sh', '*.bat', '*.ps1']
            count = 0
            
            for ext in extensions:
                pattern = os.path.join(endpoints_dir, '**', ext)
                files = glob.glob(pattern, recursive=True)
                count += len(files)
                
            return count
        except:
            return 0
        
    def update_status_messages(self):
        """Update the status messages based on server state"""
        if self.server_running:
            uptime_str = self.get_uptime_string()
            self.status_messages = [
                ("SERVER RUNNING", "#66ff66"),  # Soft green
                (f"{self.endpoint_count} ENDPOINTS", "#66ff66"),
                (f"PORT {self.port}", "#66ff66"),
                (uptime_str, "#66ff66"),
                (f"REQUESTS {self.request_count}", "#66ff66")
            ]
        else:
            self.status_messages = [
                ("SERVER STOPPED", "#ff6666"),  # Soft red
                (f"{self.endpoint_count} ENDPOINTS", "#888888"),  # Gray
                (f"PORT {self.port}", "#888888")
            ]
            
    def get_uptime_string(self):
        """Get formatted uptime string"""
        if not self.uptime_start:
            return "UPTIME 0:00"
            
        uptime_seconds = int(time.time() - self.uptime_start)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        
        if hours > 0:
            return f"UPTIME {hours}:{minutes:02d}"
        else:
            return f"UPTIME {minutes}:00"
            
    def start_status_cycling(self):
        """Start the status cycling thread"""
        def cycle_status():
            while True:
                if self.status_cycling and len(self.status_messages) > 1:
                    self.status_index = (self.status_index + 1) % len(self.status_messages)
                    message, color = self.status_messages[self.status_index]
                    self.update_status_display(message, color)
                    
                    # Update request count occasionally
                    if self.server_running and random.random() < 0.3:
                        self.request_count += random.randint(1, 3)
                        self.update_status_messages()
                        
                time.sleep(3)  # Cycle every 3 seconds
                
        threading.Thread(target=cycle_status, daemon=True).start()
        
    def update_status_display(self, text, color):
        """Update the status label"""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=text, fg=color)
            
    def show_hover_text(self, text):
        """Show hover text in status line"""
        self.status_cycling = False
        self.update_status_display(text, "#cccccc")  # Light gray for hover text
        
    def on_button_enter(self, event):
        """Show appropriate hover text based on server state"""
        if self.server_running:
            self.show_hover_text("STOP SERVER")
        else:
            self.show_hover_text("START SERVER")
    
    def hide_hover_text(self):
        """Hide hover text and resume cycling"""
        self.status_cycling = True
        if self.status_messages and self.status_index < len(self.status_messages):
            message, color = self.status_messages[self.status_index]
            self.update_status_display(message, color)
        elif self.status_messages:
            # Reset index if out of bounds
            self.status_index = 0
            message, color = self.status_messages[self.status_index]
            self.update_status_display(message, color)
            
    def open_settings(self):
        """Open settings dialog"""
        self.create_settings_dialog()
        
    def open_folder(self):
        """Open endpoints folder"""
        import subprocess
        import os
        
        endpoints_path = "endpoints"
        if os.path.exists(endpoints_path):
            subprocess.run(["explorer", endpoints_path])
        else:
            messagebox.showerror("Error", f"Endpoints folder '{endpoints_path}' not found!")
        
    def open_logs(self):
        """Open logs in default editor"""
        import subprocess
        import os
        
        log_path = "webhook.log"
        if os.path.exists(log_path):
            try:
                # Try default handler first
                subprocess.run(["start", "", log_path], shell=True, check=True)
            except subprocess.CalledProcessError:
                try:
                    # Fallback to notepad (can usually read locked files)
                    subprocess.run(["notepad", log_path], check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # If still locked, show a helpful message
                    messagebox.showwarning("File Locked", 
                        f"The log file is currently locked by the running server.\n"
                        f"You can view it at: {os.path.abspath(log_path)}\n"
                        f"Try stopping the server first, or use a text editor that can read locked files.")
        else:
            messagebox.showerror("Error", f"Log file '{log_path}' not found!")
    
    def create_settings_dialog(self):
        """Create and show the settings dialog"""
        # Create the dialog window
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("320x180")
        settings_window.resizable(False, False)
        settings_window.configure(bg=self.bg_color)
        
        # Make it modal
        settings_window.transient(self.root)
        
        # Track this dialog and set up proper close handling
        self.open_dialogs.append(settings_window)
        
        def close_settings():
            if settings_window in self.open_dialogs:
                self.open_dialogs.remove(settings_window)
            settings_window.grab_release()
            settings_window.destroy()
            
        settings_window.protocol("WM_DELETE_WINDOW", close_settings)
        settings_window.grab_set()
        
        # Center the dialog on the main window
        self.center_window(settings_window, 320, 160)
        
        # Main frame
        main_frame = tk.Frame(settings_window, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=12, pady=8)
        
        # Top section - Executables
        exec_frame = tk.Frame(main_frame, bg=self.bg_color)
        exec_frame.pack(fill="x", pady=(0, 8))
        
        # Webhook path  
        tk.Label(exec_frame, text="Webhook:", bg=self.bg_color, fg="#e0e0e0").grid(row=0, column=0, sticky="w", pady=3)
        self.webhook_path_var = tk.StringVar(value=self.webhook_path)
        tk.Button(exec_frame, text="📁", command=lambda: self.browse_file(self.webhook_path_var), bg="#6a5a4a", fg="#e0e0e0", border=0, width=3, height=1).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=3)
        
        # Python path
        tk.Label(exec_frame, text="Python:", bg=self.bg_color, fg="#e0e0e0").grid(row=1, column=0, sticky="w", pady=3)
        self.python_path_var = tk.StringVar(value=self.python_path)
        tk.Button(exec_frame, text="📁", command=lambda: self.browse_file(self.python_path_var), bg="#6a5a4a", fg="#e0e0e0", border=0, width=3, height=1).grid(row=1, column=1, sticky="w", padx=(10, 0), pady=3)
        
        # Bash path
        tk.Label(exec_frame, text="Bash:", bg=self.bg_color, fg="#e0e0e0").grid(row=2, column=0, sticky="w", pady=3)
        self.bash_path_var = tk.StringVar(value=self.bash_path)
        tk.Button(exec_frame, text="📁", command=lambda: self.browse_file(self.bash_path_var), bg="#6a5a4a", fg="#e0e0e0", border=0, width=3, height=1).grid(row=2, column=1, sticky="w", padx=(10, 0), pady=3)
        
        # Endpoints folder path
        tk.Label(exec_frame, text="Endpoints:", bg=self.bg_color, fg="#e0e0e0").grid(row=3, column=0, sticky="w", pady=3)
        self.endpoints_path_var = tk.StringVar(value=self.endpoints_path)
        tk.Button(exec_frame, text="📁", command=lambda: self.browse_folder(self.endpoints_path_var), bg="#6a5a4a", fg="#e0e0e0", border=0, width=3, height=1).grid(row=3, column=1, sticky="w", padx=(10, 0), pady=3)
        
        # Port in top-right area
        tk.Label(exec_frame, text="Port:", bg=self.bg_color, fg="#e0e0e0").grid(row=0, column=2, sticky="w", padx=(20, 5), pady=3)
        self.port_var = tk.StringVar(value=str(self.port))
        port_entry = tk.Entry(exec_frame, textvariable=self.port_var, bg="#404040", fg="#e0e0e0", insertbackground="#e0e0e0", width=10)
        port_entry.grid(row=0, column=3, sticky="w", pady=3)
        
        # Options under port
        self.auto_start_var = tk.BooleanVar(value=self.auto_start)
        self.auto_start_checkbox = tk.Checkbutton(exec_frame, text="Auto start on launch", variable=self.auto_start_var, 
                      bg=self.bg_color, fg="#e0e0e0", selectcolor="#404040", command=self.toggle_auto_minimize)
        self.auto_start_checkbox.grid(row=1, column=2, columnspan=2, sticky="w", padx=(20, 0), pady=3)
        
        self.auto_minimize_var = tk.BooleanVar(value=self.auto_minimize)
        self.auto_minimize_checkbox = tk.Checkbutton(exec_frame, text="Auto minimize", variable=self.auto_minimize_var, 
                      bg=self.bg_color, fg="#888888" if not self.auto_start else "#e0e0e0", selectcolor="#404040", 
                      state="disabled" if not self.auto_start else "normal")
        self.auto_minimize_checkbox.grid(row=2, column=2, columnspan=2, sticky="w", padx=(20, 0), pady=3)
        
        # Buttons aligned with checkboxes
        tk.Button(exec_frame, text="Cancel", command=close_settings, 
                 bg="#6a4a4a", fg="#e0e0e0", border=0, padx=20).grid(row=3, column=3, sticky="e", padx=(5, 0), pady=3)
        tk.Button(exec_frame, text="Save", command=lambda: self.save_settings_dialog(settings_window),
                 bg="#4a6a4a", fg="#e0e0e0", border=0, padx=20).grid(row=3, column=2, sticky="e", padx=(20, 0), pady=3)
    
    def center_window(self, window, width, height):
        """Center a window on the parent window"""
        # Get parent window position and size
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def browse_folder(self, var):
        """Open folder browser dialog"""
        folder = filedialog.askdirectory()
        if folder:
            var.set(folder)
    
    def browse_file(self, var):
        """Open file browser dialog"""
        file = filedialog.askopenfilename()
        if file:
            var.set(file)
    
    def toggle_auto_minimize(self):
        """Enable/disable auto minimize based on auto start setting"""
        if self.auto_start_var.get():
            self.auto_minimize_checkbox.config(state="normal", fg="#e0e0e0")
        else:
            self.auto_minimize_var.set(False)
            self.auto_minimize_checkbox.config(state="disabled", fg="#888888")
    
    def save_settings_dialog(self, window):
        """Save settings from dialog and close"""
        try:
            # Validate port
            new_port = int(self.port_var.get())
            if not (1 <= new_port <= 65535):
                raise ValueError("Port must be between 1 and 65535")
            
            # Update instance variables
            self.webhook_path = self.webhook_path_var.get()
            self.python_path = self.python_path_var.get()
            self.bash_path = self.bash_path_var.get()
            self.endpoints_path = self.endpoints_path_var.get()
            self.port = new_port
            self.auto_start = self.auto_start_var.get()
            self.auto_minimize = self.auto_minimize_var.get()
            
            # Save to file
            self.save_settings()
            
            # Close dialog properly
            if window in self.open_dialogs:
                self.open_dialogs.remove(window)
            window.grab_release()
            window.destroy()
            

            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid port number: {e}")
    
    def load_settings(self):
        """Load settings from gui_settings.json"""
        settings_file = "gui_settings.json"
        defaults = {
            "webhook_path": "webhook",
            "python_path": "python", 
            "bash_path": "bash",
            "endpoints_path": "./endpoints",
            "port": 9000,
            "auto_start": False,
            "auto_minimize": False
        }
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    
                # Update defaults with loaded values
                for key, value in settings.items():
                    if key in defaults:
                        defaults[key] = value
                        
        except Exception as e:
            print(f"Error loading settings: {e}")
            
        # Apply settings to instance variables
        self.webhook_path = defaults["webhook_path"]
        self.python_path = defaults["python_path"] 
        self.bash_path = defaults["bash_path"]
        self.endpoints_path = defaults["endpoints_path"]
        self.port = defaults["port"]
        self.auto_start = defaults["auto_start"]
        self.auto_minimize = defaults["auto_minimize"]
    
    def save_settings(self):
        """Save current settings to gui_settings.json"""
        settings = {
            "webhook_path": getattr(self, 'webhook_path_var', tk.StringVar()).get() if hasattr(self, 'webhook_path_var') else self.webhook_path,
            "python_path": getattr(self, 'python_path_var', tk.StringVar()).get() if hasattr(self, 'python_path_var') else self.python_path,
            "bash_path": getattr(self, 'bash_path_var', tk.StringVar()).get() if hasattr(self, 'bash_path_var') else self.bash_path, 
            "endpoints_path": getattr(self, 'endpoints_path_var', tk.StringVar()).get() if hasattr(self, 'endpoints_path_var') else self.endpoints_path,
            "port": self.port,
            "auto_start": getattr(self, 'auto_start_var', tk.BooleanVar()).get() if hasattr(self, 'auto_start_var') else self.auto_start,
            "auto_minimize": getattr(self, 'auto_minimize_var', tk.BooleanVar()).get() if hasattr(self, 'auto_minimize_var') else self.auto_minimize
        }
        
        try:
            with open("gui_settings.json", 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def auto_start_server(self):
        """Auto-start server with optional minimize to tray"""
        if not self.server_running:
            self.start_server()
            
            # Auto-minimize if enabled and tray is available
            if self.auto_minimize and TRAY_AVAILABLE and self.tray_icon:
                # Wait a bit for server to start, then minimize
                self.root.after(3000, self.hide_to_tray)
    
    def create_tray_icon(self):
        """Create system tray icon"""
        if not TRAY_AVAILABLE:
            return
            
        # Create a simple icon image
        image = Image.new('RGB', (64, 64), color='black')
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill='green')
        draw.text((20, 24), "API", fill='white')
        
        # Create tray menu
        menu = pystray.Menu(
            pystray.MenuItem("Show", self.show_window, default=True),
            pystray.MenuItem("Start Server", self.tray_start_server, enabled=lambda item: not self.server_running),
            pystray.MenuItem("Stop Server", self.tray_stop_server, enabled=lambda item: self.server_running),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Endpoints", self.open_folder),
            pystray.MenuItem("Open Logs", self.open_logs),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("EasyAPI", image, "Easy API Endpoints", menu)
    
    def show_window(self, icon=None, item=None):
        """Show the main window from tray"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_minimized_to_tray = False
    
    def hide_to_tray(self):
        """Hide window to system tray"""
        if not TRAY_AVAILABLE or not self.tray_icon:
            # Fallback: just minimize normally
            self.root.iconify()
            return
            
        self.root.withdraw()
        self.is_minimized_to_tray = True
        if not self.tray_icon.visible:
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def tray_start_server(self, icon=None, item=None):
        """Start server from tray menu"""
        if not self.server_running:
            self.start_server()
    
    def tray_stop_server(self, icon=None, item=None):
        """Stop server from tray menu"""
        if self.server_running:
            self.stop_server()
    
    def quit_app(self, icon=None, item=None):
        """Completely quit the application"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.quit_application()
    
    def on_main_window_close(self):
        """Handle main window close event"""
        # If server is running and tray is available, minimize to tray instead of closing
        if self.server_running and TRAY_AVAILABLE and self.tray_icon:
            self.hide_to_tray()
            return
        
        # If server is running but no tray, ask user
        if self.server_running:
            result = messagebox.askyesno("Server Running", 
                                       "The server is still running. Do you want to stop it and quit?")
            if not result:
                return  # Don't close
        
        # Otherwise, quit the application
        self.quit_application()
    
    def quit_application(self):
        """Actually quit the application with cleanup"""
        # Kill ALL webhook processes to prevent orphans
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name']):
                if 'webhook' in proc.info['name'].lower():
                    try:
                        process = psutil.Process(proc.info['pid'])
                        process.terminate()
                        print(f"Terminated webhook process with PID {proc.info['pid']}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
        except ImportError:
            # Fallback if psutil not available
            pass
        
        # Stop the server process if running
        if self.server_process and self.server_process.poll() is None:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=2)
            except:
                try:
                    self.server_process.kill()
                    self.server_process.wait(timeout=1)
                except:
                    pass
        
        # Force close all dialogs by using tkinter's internal mechanism
        try:
            # Get all child windows
            children = self.root.tk.call('winfo', 'children', '.')
            for child in children:
                try:
                    # Check if it's a toplevel window
                    if self.root.tk.call('winfo', 'class', child) == 'Toplevel':
                        # Force destroy without grab handling
                        self.root.tk.call('destroy', child)
                except:
                    pass
        except:
            pass
        
        # Clear our tracking list
        self.open_dialogs.clear()
        
        # Exit the application completely
        import sys
        self.root.quit()
        self.root.destroy()
        sys.exit()
        
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = EasyAPIGUI()
    app.run()