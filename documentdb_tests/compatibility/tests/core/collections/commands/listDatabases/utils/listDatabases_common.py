"""Shared expected-value patterns for listDatabases tests.

Each function returns a dict of property checks suitable for the
``expected`` argument of :class:`CommandTestCase`.
"""

from __future__ import annotations

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.framework.property_checks import Contains, Eq, Exists, IsType, NotExists


def basic_success(ctx: CommandContext) -> dict:
    """Successful response containing the test database."""
    return {
        "ok": Eq(1.0),
        "totalSize": Exists(),
        "databases": Contains("name", ctx.database),
    }


def full_structure_success(_) -> dict:
    """Full response with correct BSON types for all fields."""
    return {
        "ok": Eq(1.0),
        "totalSize": IsType("long"),
        "totalSizeMb": IsType("long"),
        "databases.0": {
            "name": IsType("string"),
            "sizeOnDisk": IsType("long"),
            "empty": IsType("bool"),
        },
    }


def name_only_success(_) -> dict:
    """Name-only response with size fields absent."""
    return {
        "ok": Eq(1.0),
        "totalSize": NotExists(),
        "totalSizeMb": NotExists(),
        "databases.0": {
            "name": IsType("string"),
            "sizeOnDisk": NotExists(),
            "empty": NotExists(),
        },
    }
