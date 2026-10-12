"""Read-only MCP server for Markdown files under the organized directory."""

import argparse
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORGANIZED_ROOT = PROJECT_ROOT / "organized"

mcp = FastMCP(
    "The Outlander Journaler",
    host="127.0.0.1",
    port=8765,
    streamable_http_path="/mcp",
)


def _resolve_markdown_path(relative_path: str, *, allow_root: bool = False) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Path must stay inside the organized directory.")
    if not relative.parts:
        if allow_root:
            return ORGANIZED_ROOT
        raise ValueError("A relative Markdown file path is required.")

    candidate = ORGANIZED_ROOT
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError("Symbolic links are not exposed by this server.")

    resolved = candidate.resolve()
    if resolved != ORGANIZED_ROOT and not resolved.is_relative_to(ORGANIZED_ROOT):
        raise ValueError("Path must stay inside the organized directory.")
    return resolved


def _iter_markdown_files(folder: Path):
    for current_root, directories, filenames in os.walk(folder, followlinks=False):
        current_path = Path(current_root)
        directories[:] = sorted(
            directory
            for directory in directories
            if not (current_path / directory).is_symlink()
        )
        for filename in sorted(filenames):
            path = current_path / filename
            if path.suffix.lower() == ".md" and not path.is_symlink():
                yield path


@mcp.tool()
def list_folders() -> list[str]:
    """List organized folders, including nested folders, as relative paths."""
    if not ORGANIZED_ROOT.is_dir():
        return []

    folders = []
    for current_root, directories, _ in os.walk(ORGANIZED_ROOT, followlinks=False):
        current_path = Path(current_root)
        directories[:] = sorted(
            directory
            for directory in directories
            if not (current_path / directory).is_symlink()
        )
        folders.extend(
            (current_path / directory).relative_to(ORGANIZED_ROOT).as_posix()
            for directory in directories
        )
    return sorted(folders)


@mcp.tool()
def list_files(folder: str = "") -> list[str]:
    """List Markdown files relative to organized/, optionally within a folder."""
    selected_folder = _resolve_markdown_path(folder, allow_root=True)
    if not selected_folder.is_dir():
        raise NotADirectoryError(f"Organized folder not found: {folder}")
    return [
        path.relative_to(ORGANIZED_ROOT).as_posix()
        for path in _iter_markdown_files(selected_folder)
    ]


@mcp.tool()
def read_file(path: str) -> str:
    """Read a UTF-8 Markdown file using its path relative to organized/."""
    file_path = _resolve_markdown_path(path)
    if file_path.suffix.lower() != ".md":
        raise ValueError("Only Markdown files can be read.")
    if not file_path.is_file():
        raise FileNotFoundError(f"Organized Markdown file not found: {path}")
    return file_path.read_text(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
        help="MCP transport to use (default: stdio).",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
