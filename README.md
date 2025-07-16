# Easy API Endpoints

A lightweight, flexible framework for quickly deploying API endpoints using the `webhook` tool.

## Overview

This project provides a simple way to create and deploy HTTP API endpoints without the overhead of a full web framework. It uses [adnanh/webhook](https://github.com/adnanh/webhook) to handle HTTP requests and route them to script-based endpoints.

Key features:
- **Drop-in Endpoints**: Add new API endpoints by simply dropping scripts into the `endpoints` directory
- **Automatic Configuration**: The system automatically generates webhook configurations for all endpoints
- **Flexible Script Support**: Supports Python, shell scripts, and other executable formats
- **Raw Request Handling**: Passes the raw HTTP request body to your scripts via stdin
- **Simple Deployment**: Single command to deploy all endpoints
- **Minimal Configuration**: Only executables and server settings need to be configured

## Requirements

- Python 3.x
- Go (for the webhook tool)
- PyYAML (`pip install pyyaml`)
- psutil (`pip install psutil`)
- [adnanh/webhook](https://github.com/adnanh/webhook) installed and in your PATH

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/easy-api-endpoints.git
   cd easy-api-endpoints
   ```

2. Install the required Python packages:
   ```
   pip install pyyaml psutil
   ```

3. Install the webhook tool:
   ```
   go install github.com/adnanh/webhook@latest
   ```

4. Create the endpoints directory (if it doesn't exist):
   ```
   mkdir -p endpoints
   ```

## Configuration

The framework uses a `config.yaml` file for minimal configuration settings. Here's an example:

```yaml
# Webhook API Framework Configuration

# Executables
webhook_executable: "C:\\Users\\melti\\go\\bin\\webhook"
python_executable: "C:\\Program Files\\Python313\\python.exe"

# Server settings
port: 9000
verbose: true
```

Edit this file to match your environment. If the file doesn't exist, the script will use default values.

All other paths are determined automatically relative to the repository:
- `endpoints_dir`: Always `./endpoints/` relative to the script
- `hooks_file`: Always `./hooks.yaml` relative to the script
- `launcher_script`: Always `./run-endpoint.py` relative to the script
- `working_dir`: Always the directory containing the script

## Creating Endpoints

To create a new API endpoint:

1. Create a script in the `endpoints` directory (e.g., `hello.py`, `users.py`, etc.)
2. The script should read input from stdin and print output to stdout
3. The endpoint URL will be `http://localhost:9000/hooks/{script-name-without-extension}`

### Example Endpoint

```python
# endpoints/hello.py
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
```

## Running the API Server

Start the API server with:

```
python update-hooks.py
```

This will:
1. Load configuration from `config.yaml` (or use defaults if not found)
2. Scan the `endpoints` directory for scripts
3. Generate a `hooks.yaml` configuration file
4. Kill any existing webhook processes
5. Start the webhook server with the generated configuration

The server will run until interrupted (Ctrl+C).

## Using the API

Once the server is running, you can access your endpoints using HTTP requests:

```bash
# Plain text request
curl -X POST http://localhost:9000/hooks/hello -d "Claude"

# JSON request
curl -X POST http://localhost:9000/hooks/hello \
  -H "Content-Type: application/json" \
  -d '{"name":"JSON User"}'
```

## How It Works

1. The `update-hooks.py` script scans the `endpoints` directory for endpoint scripts
2. For each script, it generates a hook configuration in `hooks.yaml`
3. When a request is received, webhook:
   - Saves the request body to a temporary file
   - Passes the file path to `run-endpoint.py` via an environment variable
   - `run-endpoint.py` reads the file contents and pipes them to the appropriate endpoint script
   - The endpoint script processes the input and returns a response
   - The response is sent back to the client

## Advanced Usage

### Supporting Different Script Types

The system automatically detects the script type based on file extension:
- `.py`: Executed with Python
- `.sh`: Executed with bash
- Other: Executed directly (must be executable)


## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

This project uses [adnanh/webhook](https://github.com/adnanh/webhook) for HTTP request handling. 
