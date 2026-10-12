# Requirements

## Ubuntu system

Install Python, virtual-environment support, and FFmpeg:

```bash
sudo apt update
sudo apt install python3 python3-venv ffmpeg
```

Ollama must also be installed and running for model discovery and Markdown
processing. Install Ollama for Ubuntu using its official installation
instructions, then pull at least one model in Ollama.

## Python virtual environment

From the project directory, create and populate `.venv`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

`requirements.txt` lists the application's direct Python dependencies.
Whisper's PyTorch and other Python dependencies are installed transitively.
The test suite uses Python's standard-library `unittest` and needs no extra
test packages.

## MCP server

The read-only MCP server uses the `mcp` package already listed in
`requirements.txt`. It runs independently from Streamlit and supports stdio
clients or a Streamable HTTP endpoint bound to localhost.

For stdio clients, configure the client to launch:

```text
command: /absolute/path/to/the-journaler/.venv/bin/python
args:    /absolute/path/to/the-journaler/mcp_server/server.py --transport stdio
```

For local Streamable HTTP clients, start the server with:

```bash
.venv/bin/python mcp_server/server.py --transport streamable-http
```

Connect the client to `http://127.0.0.1:8765/mcp`. The HTTP server binds only
to the local machine.
