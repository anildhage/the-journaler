# Learning the MCP Setup in This Project

This guide connects the MCP ideas to the implementation in this folder. It is
intended as a walkthrough, not just a list of commands.

## 1. Start with the mental model

MCP is a standard way for an AI application to ask another program for
context or actions. In this setup there are three roles:

1. **MCP host**: the AI application, for example an MCP-enabled AnythingLLM.
2. **MCP client**: the MCP component inside that AI application. It connects,
   discovers tools, and sends tool requests.
3. **MCP server**: this project's `mcp_server/server.py`. It advertises
   read-only operations and returns their results.

The host/client does not get unrestricted filesystem access from MCP. It can
only ask for the operations that this server explicitly exposes.

The Streamlit journal application and this MCP server are separate processes.
The Streamlit application does not need to be running for an MCP client to
read organized notes.

## 2. Define the smallest useful capability

The initial requirement was: let AI clients read files in `organized/`, and
nothing else. That led to three tools:

| Tool | What it does | Example |
| --- | --- | --- |
| `list_folders` | Lists folders under `organized/`, including nested folders | `journal/2026` |
| `list_files` | Lists Markdown files under the root or a selected folder | `journal/2026/entry.md` |
| `read_file` | Returns the UTF-8 text of one Markdown file | Contents of `journal/2026/entry.md` |

There are deliberately no tools to create, edit, or delete files, and no
access to `inbox/`, `raw-markdown/`, configuration, or processing logs.

## 3. Turn Python functions into MCP tools

In `server.py`, the official Python SDK provides `FastMCP`. The server is
created with a name and local HTTP settings:

```python
mcp = FastMCP(
    "The Outlander Journaler",
    host="127.0.0.1",
    port=8765,
    streamable_http_path="/mcp",
)
```

Each exposed function has an `@mcp.tool()` decorator. The function name,
annotations, and docstring tell the SDK and client what the tool is called,
which arguments it accepts, and what it does. For example:

```python
@mcp.tool()
def read_file(path: str) -> str:
    """Read a UTF-8 Markdown file using its path relative to organized/."""
```

The MCP client can discover this tool and its `path` argument without knowing
how the Python function is implemented. It calls `read_file` with a relative
path; the server returns the text or a useful error.

## 4. Fix the data boundary before reading anything

The server computes the project root from the location of `server.py`, then
sets the one allowed content root to the project's `organized/` directory.
This avoids relying on whichever directory the client happens to use as its
working directory.

Every path supplied by a client is treated as untrusted:

1. Absolute paths and paths containing `..` are rejected.
2. Each path component is checked for symbolic links.
3. The resolved path must still be inside `organized/`.
4. `read_file` accepts only `.md` files that exist as files.
5. Folder/file enumeration does not follow symbolic links.

These checks make requests such as `../config/settings.json` invalid.
Enumeration returns paths relative to `organized/`, so the client can pass a
listed path directly to `read_file`.

The server is read-only at the application level: its tools contain no write
or delete operations. The OS account running it still needs filesystem read
access to `organized/`.

## 5. Keep the tools separate from the connection method

MCP transports are ways to carry MCP messages; they do not change what the
tools can do. This server offers two:

### stdio

An MCP client launches the Python server as a child process and exchanges MCP
messages through the process's standard input and output. This is usually the
simplest option for a desktop AI client on the same computer.

The client configuration points to:

- **Command**: the project's `.venv` Python executable.
- **Arguments**: the absolute path to `mcp_server/server.py` and
  `--transport stdio`.
- **Working directory**: preferably the project root.

The server defaults to stdio if no transport is specified. Do not print
diagnostic messages to stdout in stdio mode; stdout carries the MCP protocol.

### Streamable HTTP

The MCP server runs as a local web service. A client connects to:

```text
http://127.0.0.1:8765/mcp
```

Start it from the project root with:

```bash
.venv/bin/python mcp_server/server.py --transport streamable-http
```

It binds to `127.0.0.1`, not a network-facing address. The server must remain
running while clients use it. Because it has no authentication, keep this
endpoint local and do not change the bind address to expose it to other
machines without first designing and implementing appropriate access
controls.

For either transport, the MCP host and server must be able to access the same
organized files. A client running in a separate container may not see files
on the host unless the directory is deliberately mounted into that container.

## 6. Install and launch

The SDK is pinned in the project's root `requirements.txt`:

```text
mcp==1.30.0
```

Install or refresh dependencies in the existing project environment:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

The complete system and Python setup is documented in the root
`REQUIREMENTS.md`. The MCP server itself is run independently of Streamlit.

## 7. Test the implementation

### Automated safety and behavior tests

From the project root:

```bash
.venv/bin/python -m unittest discover -s test -v
```

`test/test_mcp_server.py` uses a temporary directory rather than touching
real journal content. It verifies folder/file listing, Markdown reading,
non-Markdown rejection, traversal rejection, and symlink rejection.

### Interactive protocol test

The MCP Inspector can connect to either transport. For stdio, configure it to
launch the same command shown above. For HTTP, start the server and connect
the Inspector to `http://127.0.0.1:8765/mcp`.

Then try this sequence:

1. Call `list_folders`.
2. Call `list_files` with no folder, or pass one of the listed folder paths.
3. Pass a returned Markdown path to `read_file`.
4. Try `read_file` with `../some-file.md`; the server should reject it.

The Inspector is only a development/testing client; it is not required by the
application or by the server at runtime.

## 8. What happens when an AI asks for a note?

For example, when asked to summarize a note in a folder, the AI can:

1. Ask `list_folders` or `list_files` to discover available notes.
2. Choose a returned relative path such as `journal/2026/entry.md`.
3. Call `read_file` with that path.
4. Use the returned text as context for its answer.

The AI application decides when to call tools. The server only validates the
request, reads the allowed file, and returns its text.

## 9. A safe roadmap for expanding it

Keep this first version narrow. If you later want more capability:

1. Add a specific read-only operation, such as title search, rather than
   exposing arbitrary filesystem paths.
2. Add automated tests for its inputs, results, and failure cases.
3. Keep every operation constrained to the same resolved `organized/` root.
4. If HTTP ever needs to be reachable from another device, first add
   authentication, authorization, and an explicit network security design.
5. Add write operations only as a separate, deliberate feature with
   confirmation and tests; MCP itself does not make a tool read-only.

This separation keeps the Streamlit application, the MCP server, and each AI
client independent while making the filesystem boundary explicit.
