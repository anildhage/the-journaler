"""Persistent storage for raw Markdown processing history."""

import os
import sqlite3
from contextlib import closing
from datetime import datetime


PROCESSING_LOG_DB = "./logs/processing_logs.sqlite3"


def _connect():
    os.makedirs(os.path.dirname(PROCESSING_LOG_DB), exist_ok=True)
    connection = sqlite3.connect(PROCESSING_LOG_DB)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS processing_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            filename TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            model TEXT,
            prompt TEXT,
            target_folder TEXT NOT NULL,
            source_removed INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    return connection


def record_processing_attempt(
    filename,
    status,
    message,
    model,
    prompt,
    target_folder,
    source_removed=False,
):
    """Persist a processing result and return its record ID."""
    with closing(_connect()) as connection, connection:
        cursor = connection.execute(
            """
            INSERT INTO processing_logs (
                created_at, filename, status, message, model, prompt,
                target_folder, source_removed
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().astimezone().isoformat(timespec="seconds"),
                filename,
                status,
                message,
                model,
                prompt,
                target_folder,
                int(source_removed),
            ),
        )
        return cursor.lastrowid


def update_processing_attempt(log_id, status, message, source_removed):
    """Update the final outcome after raw-file cleanup."""
    with closing(_connect()) as connection, connection:
        connection.execute(
            """
            UPDATE processing_logs
            SET status = ?, message = ?, source_removed = ?
            WHERE id = ?
            """,
            (status, message, int(source_removed), log_id),
        )


def list_processing_logs():
    """Return processing history, newest first."""
    with closing(_connect()) as connection:
        rows = connection.execute(
            """
            SELECT created_at, filename, status, message, model, prompt,
                   target_folder, source_removed
            FROM processing_logs
            ORDER BY id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]
