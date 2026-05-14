"""Shared helpers for $out stage tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)


@dataclass(frozen=True)
class OutTestCase(StageTestCase):
    """Data-driven test case for ``$out`` stage tests.

    Attributes:
        target_coll: Name of the output collection.
        target_db: Target database name.  ``None`` means use the current database.
        out_spec: Extra fields to merge into the ``$out`` document form.
        expected_type: Expected collection type after ``$out`` runs.
        expected_options: Expected collection options after ``$out`` runs.
    """

    target_coll: str = "target"
    target_db: str | None = None
    out_spec: Any = None
    expected_type: str = "collection"
    expected_options: dict[str, Any] | None = None

    def build_out_stage(self, collection: Collection) -> dict[str, Any]:
        """Build the ``$out`` stage spec from this test case."""
        db_name = self.target_db or collection.database.name
        target = self.target_coll
        if self.out_spec is not None or self.target_db is not None:
            spec: dict[str, Any] = {"db": db_name, "coll": target}
            if self.out_spec:
                spec.update(self.out_spec)
            return {"$out": spec}
        return {"$out": target}
