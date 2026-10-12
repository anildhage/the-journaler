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
