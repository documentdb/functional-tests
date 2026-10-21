"""
Unified execution and assertion utilities for tests.
"""

import time
from datetime import timezone
from typing import Any, Dict, List, Tuple

from bson.codec_options import CodecOptions

from documentdb_tests.framework.lazy_payload import materialize

TZ_AWARE_CODEC: CodecOptions = CodecOptions(tz_aware=True, tzinfo=timezone.utc)

# Server cursors opened through execute_command/execute_admin_command.
#
# A raw command such as {"find": ..., "batchSize": 2} or an aggregate with
# $changeStream returns a cursor id that no driver object owns, so nothing
# closes it when the test ends. The server keeps it until its idle timeout,
# and engines that cap open cursors per instance then reject the next test's
# find/aggregate with "too many cursors". Each entry is (client, namespace,
# cursor id); close_tracked_cursors() kills them at test teardown.
_tracked_cursors: List[Tuple[Any, str, int]] = []


def _track_cursor(client, result: Any) -> None:
    """Remember the server cursor a command result left open, if any."""
    if not isinstance(result, dict):
        return
    cursor = result.get("cursor")
    if not isinstance(cursor, dict):
        return
    cursor_id = cursor.get("id")
    ns = cursor.get("ns")
    if cursor_id and isinstance(ns, str) and "." in ns:
        _tracked_cursors.append((client, ns, cursor_id))


def close_tracked_cursors() -> None:
    """Kill every server cursor tracked since the last call, best effort.

    Cursors that are already exhausted or killed are reported by the server
    in cursorsNotFound, which is not an error. Any failure is ignored: this is
    cleanup, and it must never change a test's outcome.
    """
    by_namespace: Dict[Tuple[int, str], Tuple[Any, List[int]]] = {}
    for client, ns, cursor_id in _tracked_cursors:
        _, ids = by_namespace.setdefault((id(client), ns), (client, []))
        ids.append(cursor_id)
    _tracked_cursors.clear()
    for (_, ns), (client, ids) in by_namespace.items():
        db_name, coll_name = ns.split(".", 1)
        try:
            client[db_name].command({"killCursors": coll_name, "cursors": ids})
        except Exception:
            pass


def execute_command(collection, command: Dict, codec_options=TZ_AWARE_CODEC, session=None) -> Any:
    """
    Execute a DocumentDB command and return result or exception.

    Args:
        collection: DocumentDB collection
        command: Command to execute via runCommand
        codec_options: CodecOptions for result decoding.
            Defaults to UTC-aware datetime decoding.
        session: Optional ClientSession for session-aware commands.

    Returns:
        Result if successful, Exception if failed
    """
    try:
        db = collection.database
        result = db.command(materialize(command), codec_options=codec_options, session=session)
        _track_cursor(db.client, result)
        return result
    except Exception as e:
        return e


def execute_admin_command(collection, command: Dict, session=None) -> Any:
    """
    Execute a DocumentDB command on admin database and return result or exception.

    Args:
        collection: DocumentDB collection
        command: Command to execute via runCommand
        session: Optional ClientSession for session-aware commands.

    Returns:
        Result if successful, Exception if failed
    """
    try:
        db = collection.database.client.admin
        result = db.command(materialize(command), session=session)
        _track_cursor(db.client, result)
        return result
    except Exception as e:
        return e


def execute_admin_with_retry_command(
    collection, command: Dict, *, retry_code: int, timeout: float = 30.0, interval: float = 0.2
) -> Any:
    """
    Run an admin command, retrying while it fails with ``retry_code``.

    Any other result (success or a different error) is returned immediately. On
    timeout, the last result is returned as-is.

    Args:
        collection: DocumentDB collection
        command: Command to execute via runCommand on the admin database
        retry_code: Error code to treat as transient and retry past
        timeout: Maximum seconds to keep retrying before returning the last result
        interval: Seconds to wait between attempts

    Returns:
        Result if successful, Exception if failed
    """
    deadline = time.monotonic() + timeout
    while True:
        result = execute_admin_command(collection, command)
        should_retry = isinstance(result, Exception) and getattr(result, "code", None) == retry_code
        if not should_retry or time.monotonic() >= deadline:
            return result
        time.sleep(interval)
