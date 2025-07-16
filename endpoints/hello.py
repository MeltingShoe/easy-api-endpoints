import sys
import json

# Read data from stdin
input_data = sys.stdin.read()

# Try to parse as JSON
try:
    data = json.loads(input_data)
    name = data.get('name', 'World')
except (json.JSONDecodeError, TypeError):
    # If not valid JSON, use the input as is or default to "World"
    name = input_data.strip() if input_data.strip() else 'World'

# Print the greeting
print(f"Hello, {name}! Welcome to the API.") 