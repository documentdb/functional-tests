"""Utilities for renameCollection tests."""

from typing import Any

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
)


def cross_db_cleanup_ns(cmd: dict[str, Any], ctx: CommandContext, register: Any) -> None:
    """Register cleanup for the target namespace if it differs from the source db."""
    target_ns = cmd.get("to", "") if isinstance(cmd.get("to"), str) else ""
    target_db = target_ns.split(".", 1)[0] if target_ns else ""
    if target_db and target_db != ctx.database:
        register(target_ns)
