import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import time
import random

class EasyAPIGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Easy API Endpoints")
        self.root.geometry("300x200")
        self.root.resizable(False, False)
        
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
            
        # State variables
        self.server_running = False
        self.server_status = "STOPPED"
        self.endpoint_count = 0
        self.port = 9000
        self.uptime_start = None
        self.request_count = 0
        self.status_index = 0
        self.status_cycling = True
        
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
            bg="#4a5d4a",  # Desaturated green
            fg="#e0e0e0",  # Light gray text
            border=0,
            activebackground="#5a6d5a",
            command=self.toggle_server
        )
        self.start_stop_button.pack(fill="both", expand=True)
        self.start_stop_button.bind("<Enter>", lambda e: self.show_hover_text("START SERVER"))
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
        self.server_status = "STARTING..."
        self.update_status_display("STARTING...", "#ffaa66")  # Soft orange
        self.start_stop_button.config(text="⏸", bg="#6a5a4a")  # Desaturated orange
        
        # Simulate server startup
        def startup():
            time.sleep(2)  # Simulate startup time
            self.server_running = True
            self.server_status = "RUNNING"
            self.uptime_start = time.time()
            self.endpoint_count = random.randint(3, 12)  # Mock endpoint count
            self.request_count = 0
            
            self.start_stop_button.config(text="⏸", bg="#6a4a4a")  # Desaturated red
            self.update_status_messages()
            
        threading.Thread(target=startup, daemon=True).start()
        
    def stop_server(self):
        """Stop the server"""
        self.server_status = "STOPPING..."
        self.update_status_display("STOPPING...", "#ffaa66")  # Soft orange
        self.start_stop_button.config(text="⏸", bg="#6a5a4a")  # Desaturated orange
        
        # Simulate server shutdown
        def shutdown():
            time.sleep(1)  # Simulate shutdown time
            self.server_running = False
            self.server_status = "STOPPED"
            self.uptime_start = None
            
            self.start_stop_button.config(text="▶", bg="#4a5d4a")  # Back to desaturated green
            self.update_status_messages()
            
        threading.Thread(target=shutdown, daemon=True).start()
        
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
        
    def hide_hover_text(self):
        """Hide hover text and resume cycling"""
        self.status_cycling = True
        if self.status_messages:
            message, color = self.status_messages[self.status_index]
            self.update_status_display(message, color)
            
    def open_settings(self):
        """Open settings dialog"""
        messagebox.showinfo("Settings", "Settings dialog would open here!")
        
    def open_folder(self):
        """Open endpoints folder"""
        messagebox.showinfo("Folder", "Would open endpoints folder!")
        
    def open_logs(self):
        """Open logs in default editor"""
        messagebox.showinfo("Logs", "Would open webhook.log in default editor!")
        
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = EasyAPIGUI()
    app.run()