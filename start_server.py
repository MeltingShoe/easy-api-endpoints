import os
import sys
import glob
import yaml
import subprocess
import time
import signal
import psutil

# Fixed paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENDPOINTS_DIR = os.path.join(SCRIPT_DIR, "endpoints")
HOOKS_FILE = os.path.join(SCRIPT_DIR, "hooks.yaml")
LAUNCHER_SCRIPT = os.path.join(SCRIPT_DIR, "call_endpoint.py")
WORKING_DIR = SCRIPT_DIR

# Configuration file
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.yaml")

def load_config():
    """Load configuration from YAML file."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
        # print(f"Loaded configuration from {CONFIG_FILE}")
        return config
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        print("Using default configuration")
        return {
            "webhook_executable": "webhook",
            "python_executable": "python",
            "bash_executable": "bash",
            "port": 9000,
            "verbose": True
        }

# Load configuration
CONFIG = load_config()

def get_endpoint_files():
    """Get all files in the endpoints directory recursively."""
    files = []
    extensions = ['*.py', '*.sh', '*.bat', '*.ps1']
    
    for ext in extensions:
        pattern = os.path.join(ENDPOINTS_DIR, '**', ext)
        files.extend(glob.glob(pattern, recursive=True))
    
    return files

def generate_hook_config(endpoint_files):
    """Generate the hooks.yaml configuration based on the endpoint files."""
    hooks = []
    
    for endpoint_file in endpoint_files:
        # Get the relative path from the endpoints directory (preserves nesting!)
        relative_path = os.path.relpath(endpoint_file, ENDPOINTS_DIR)
        
        # Get the path without extension for the hook ID
        hook_id = os.path.splitext(relative_path)[0].replace('\\', '/')
        
        # Create the hook configuration
        hook = {
            "id": hook_id,
            "execute-command": CONFIG["python_executable"],
            "pass-arguments-to-command": [
                {
                    "source": "string",
                    "name": LAUNCHER_SCRIPT
                },
                {
                    "source": "string",
                    "name": relative_path  # Pass full path, not just filename
                }
            ],
            "pass-file-to-command": [
                {
                    "source": "raw-request-body",
                    "envname": "WEBHOOK_PAYLOAD",
                    "base64decode": False
                }
            ],
            "command-working-directory": WORKING_DIR,
            "include-command-output-in-response": True
        }
        
        hooks.append(hook)
    
    return hooks

def write_hooks_file(hooks):
    """Write the hooks configuration to the YAML file."""
    with open(HOOKS_FILE, 'w') as f:
        yaml.dump(hooks, f, default_flow_style=False)
    print(f"Generated {HOOKS_FILE} with {len(hooks)} hooks")

def kill_webhook_processes():
    """Kill any existing webhook processes."""
    for proc in psutil.process_iter(['pid', 'name']):
        if 'webhook' in proc.info['name'].lower():
            try:
                process = psutil.Process(proc.info['pid'])
                process.terminate()
                print(f"Terminated webhook process with PID {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

def start_webhook_server():
    """Start the webhook server with the generated hooks file."""
    try:
        # Kill any existing webhook processes
        kill_webhook_processes()
        time.sleep(1)  # Give processes time to terminate
        
        # Build the command
        cmd = [CONFIG["webhook_executable"], "-hooks", HOOKS_FILE]
        
        # Add optional parameters
        if CONFIG.get("port"):
            cmd.extend(["-port", str(CONFIG["port"])])
        if CONFIG.get("verbose", False):
            cmd.append("-verbose")
        if CONFIG.get("urlprefix") is not None:
            cmd.extend(["-urlprefix", CONFIG.get("urlprefix")])
        if CONFIG.get("urlprefix") is not None:
            cmd.extend(["-urlprefix", CONFIG.get("urlprefix")])
        
        print(f"Starting webhook server with command: {' '.join(cmd)}")
        
        # Use Popen to start the process and redirect output
        with open("webhook.log", "w") as log_file:
            process = subprocess.Popen(
                cmd, 
                stdout=log_file, 
                stderr=subprocess.STDOUT,
                text=True
            )
        
        # Wait a moment to see if the process starts successfully
        time.sleep(2)
        
        # Check if the process is still running
        if process.poll() is None:
            print("Webhook server started successfully")
            print(f"Server is running with PID {process.pid}")
            print(f"Server is listening on port {CONFIG.get('port', 9000)}")
            print("Press Ctrl+C to stop the server")
            
            # Keep the script running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping webhook server...")
                process.terminate()
                process.wait()
                print("Webhook server stopped")
        else:
            print("Failed to start webhook server")
            print(f"Exit code: {process.returncode}")
            print("Check webhook.log for details")
    
    except Exception as e:
        print(f"Error starting webhook server: {str(e)}")

def main():
    """Main function to update hooks and start the webhook server."""
    # Create endpoints directory if it doesn't exist
    if not os.path.exists(ENDPOINTS_DIR):
        os.makedirs(ENDPOINTS_DIR)
        print(f"Created {ENDPOINTS_DIR} directory")
    
    # Get all endpoint files
    endpoint_files = get_endpoint_files()
    if not endpoint_files:
        print(f"No endpoint files found in {ENDPOINTS_DIR} directory")
        print("Add some .py, .sh, .bat, or .ps1 files to get started!")
        return
    
    print(f"Found {len(endpoint_files)} endpoint files:")
    prefix = CONFIG.get("urlprefix", "hooks")
    url_prefix = f"/{prefix}" if prefix else ""
    
    for file in endpoint_files:
        relative_path = os.path.relpath(file, ENDPOINTS_DIR)
        hook_id = os.path.splitext(relative_path)[0].replace('\\', '/')
        print(f"  - {relative_path} → {url_prefix}/{hook_id}")
    
    # Generate and write hooks configuration
    hooks = generate_hook_config(endpoint_files)
    write_hooks_file(hooks)
    
    # Start the webhook server
    start_webhook_server()

if __name__ == "__main__":
    main()