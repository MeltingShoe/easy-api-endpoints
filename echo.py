import sys
import os

# Get the file path from the environment variable
payload_file = os.environ.get('WEBHOOK_PAYLOAD', '')

# Read the content from the file
try:
    with open(payload_file, 'r') as f:
        input_data = f.read()
except Exception as e:
    input_data = f"Error reading file: {str(e)}"

# Print the received data to standard output
print(f"Python script received: {input_data}")