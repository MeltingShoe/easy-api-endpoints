import sys
import os
import subprocess
from update_hooks import CONFIG

# Check if script name is provided as argument
if len(sys.argv) < 2:
    print("Error: No script specified")
    sys.exit(1)

# Get the script name from the argument
script_name = sys.argv[1]
script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "endpoints", script_name)

# Check if the script exists
if not os.path.exists(script_path):
    print(f"Error: Script {script_name} not found at {script_path}")
    sys.exit(1)

# Get the file path from the environment variable
payload_file = os.environ.get('WEBHOOK_PAYLOAD', '')

# Read the content from the file
try:
    with open(payload_file, 'r') as f:
        payload_content = f.read()
except Exception as e:
    print(f"Error reading payload file: {str(e)}")
    sys.exit(1)

# Determine how to execute the script based on its extension
if script_name.endswith('.py'):
    cmd = [sys.executable, script_path]
elif script_name.endswith('.sh'):
    cmd = [CONFIG['bash_executable'], script_path]
else:
    cmd = [script_path]

# Run the script and pipe the payload to its stdin
try:
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate(input=payload_content)
    
    # Print the script's output
    print(stdout, end='')
    
    # If there was an error, print it to stderr
    if stderr:
        print(stderr, file=sys.stderr, end='')
    
    # Exit with the same code as the script
    sys.exit(process.returncode)
except Exception as e:
    print(f"Error executing script: {str(e)}")
    sys.exit(1)