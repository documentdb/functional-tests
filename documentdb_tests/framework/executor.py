"""
Unified execution and assertion utilities for tests.
"""

import time
from datetime import timezone
from typing import Any, Dict

from bson.codec_options import CodecOptions

TZ_AWARE_CODEC: CodecOptions = CodecOptions(tz_aware=True, tzinfo=timezone.utc)


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
        result = db.command(command, codec_options=codec_options, session=session)
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
        result = db.command(command, session=session)
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
