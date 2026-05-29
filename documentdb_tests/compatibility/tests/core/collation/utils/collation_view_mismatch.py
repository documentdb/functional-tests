"""Shared infrastructure for collation view-mismatch tests.

Many stages ($lookup, $graphLookup, $unionWith) share the same pattern:
a pipeline references a secondary collection that may be wrapped in a
collated view, the source may also be wrapped in a collated view, and
the aggregate command may carry its own collation. This module provides
a generic test case with prepare/build_command methods matching the
CommandTestCase interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pymongo.collection import Collection
from pymongo.database import Database

from documentdb_tests.framework.test_case import BaseTestCase

# Sentinel used in pipelines to mark where the secondary collection name
# should be substituted at runtime.
SECONDARY = object()


def _substitute_sentinel(obj: Any, sentinel: object, replacement: str) -> Any:
    """Recursively replace *sentinel* with *replacement* in nested structures."""
    if obj is sentinel:
        return replacement
    if isinstance(obj, dict):
        return {k: _substitute_sentinel(v, sentinel, replacement) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_substitute_sentinel(item, sentinel, replacement) for item in obj]
    return obj


@dataclass(frozen=True)
class ViewMismatchTestCase(BaseTestCase):
    """Test case for collation view-mismatch behavior across stages.

    Attributes:
        docs: Documents to insert into the source collection.
        secondary_docs: Documents to insert into the secondary collection.
        pipeline: Aggregation pipeline. Use the SECONDARY sentinel wherever
            the secondary collection name should appear.
        secondary_view_collation: If set, creates a view on the secondary
            collection with this collation and targets the view instead.
        source_view_collation: If set, creates a view on the source
            collection with this collation and aggregates from the view.
        command_collation: If set, added as the ``collation`` field on the
            aggregate command.
        ignore_order_in: Passed through to assertResult.
    """

    docs: list[dict[str, Any]] = field(default_factory=list)
    secondary_docs: list[dict[str, Any]] = field(default_factory=list)
    pipeline: list[dict[str, Any]] = field(default_factory=list)
    secondary_view_collation: dict[str, Any] | None = None
    source_view_collation: dict[str, Any] | None = None
    command_collation: dict[str, Any] | None = None
    ignore_order_in: list[str] | None = None

    def prepare(self, db: Database, collection: Collection) -> Collection:
        """Set up source, secondary, and optional views. Returns the agg source."""
        secondary_col_name = f"{collection.name}_secondary"

        # Populate source.
        if self.docs:
            collection.insert_many(self.docs)

        # Populate secondary.
        db.create_collection(secondary_col_name)
        if self.secondary_docs:
            db[secondary_col_name].insert_many(self.secondary_docs)

        # Optionally wrap secondary in a view.
        if self.secondary_view_collation is not None:
            db.command(
                "create",
                f"{secondary_col_name}_view",
                viewOn=secondary_col_name,
                pipeline=[],
                collation=self.secondary_view_collation,
            )

        # Optionally wrap source in a view.
        if self.source_view_collation is not None:
            source_view_name = f"{collection.name}_view"
            db.command(
                "create",
                source_view_name,
                viewOn=collection.name,
                pipeline=[],
                collation=self.source_view_collation,
            )
            return db[source_view_name]

        return collection

    def build_command(self, collection: Collection) -> dict[str, Any]:
        """Build the aggregate command with sentinel substitution."""
        # Derive the fixture name: if we wrapped the source in a view, strip the suffix.
        fixture_name = (
            collection.name.removesuffix("_view")
            if self.source_view_collation is not None
            else collection.name
        )
        base = f"{fixture_name}_secondary"
        secondary_name = f"{base}_view" if self.secondary_view_collation is not None else base
        pipeline = _substitute_sentinel(self.pipeline, SECONDARY, secondary_name)
        command: dict[str, Any] = {
            "aggregate": collection.name,
            "pipeline": pipeline,
            "cursor": {},
        }
        if self.command_collation is not None:
            command["collation"] = self.command_collation
        return command
