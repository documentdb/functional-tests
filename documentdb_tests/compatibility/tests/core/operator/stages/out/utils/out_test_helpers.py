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
        target_coll: Suffix for the output collection name.  At runtime the
            full name is ``f"{collection.name}_{target_coll}"`` — call
            :meth:`resolve_target_coll` to obtain it.
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

    def resolve_target_coll(self, collection: Collection) -> str:
        """Return the full target collection name, unique per test worker."""
        return f"{collection.name}_{self.target_coll}"

    def build_out_stage(self, collection: Collection) -> dict[str, Any]:
        """Build the ``$out`` stage spec from this test case."""
        db_name = self.target_db or collection.database.name
        target = self.resolve_target_coll(collection)
        if self.out_spec is not None or self.target_db is not None:
            spec: dict[str, Any] = {"db": db_name, "coll": target}
            if self.out_spec:
                spec.update(self.out_spec)
            return {"$out": spec}
        return {"$out": target}
