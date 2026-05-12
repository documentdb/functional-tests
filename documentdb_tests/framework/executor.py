"""
Unified execution and assertion utilities for tests.
"""

from datetime import timezone
from typing import Any, Dict, Union

from bson.codec_options import CodecOptions

TZ_AWARE_CODEC = CodecOptions(tz_aware=True, tzinfo=timezone.utc)


def execute_command(
    collection, command: Dict, codec_options=TZ_AWARE_CODEC
) -> Union[Any, Exception]:
    """
    Execute a DocumentDB command and return result or exception.

    Args:
        collection: DocumentDB collection
        command: Command to execute via runCommand
        codec_options: CodecOptions for result decoding.
            Defaults to UTC-aware datetime decoding.

    Returns:
        Result if successful, Exception if failed
    """
    try:
        db = collection.database
        result = db.command(command, codec_options=codec_options)
        return result
    except Exception as e:
        return e


def execute_admin_command(collection, command: Dict) -> Union[Any, Exception]:
    """
    Execute a DocumentDB command on admin database and return result or exception.

    Args:
        collection: DocumentDB collection
        command: Command to execute via runCommand

    Returns:
        Result if successful, Exception if failed
    """
    try:
        db = collection.database.client.admin
        result = db.command(command)
        return result
    except Exception as e:
        return e
