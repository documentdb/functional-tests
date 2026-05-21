"""Shared helpers for $out stage tests."""

from __future__ import annotations

import uuid
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
        target_coll: Explicit override for the output-collection suffix.
            When ``None`` (the default) the test-case **id** is used, so
            every test case automatically gets a collision-free target
            without the author having to invent a name.  Set this only
            when the test intentionally needs a specific collection name
            (e.g. collection-name-acceptance tests with special chars).
        target_db: Target database name prefix.  ``None`` means use the
            current database.  When set, :meth:`resolve_target_db`
            appends a short UUID to make the name collision-free across
            parallel workers.
        out_spec: Extra fields to merge into the ``$out`` document form.
        expected_type: Expected collection type after ``$out`` runs.
        expected_options: Expected collection options after ``$out`` runs.
    """

    target_coll: str | None = None
    target_db: str | None = None
    out_spec: Any = None
    expected_type: str = "collection"
    expected_options: dict[str, Any] | None = None

    def resolve_target_db(self) -> str | None:
        """Return ``target_db`` with a UUID suffix for parallel safety.

        Returns ``None`` when ``target_db`` is not set, otherwise appends
        a short random UUID so that parallel workers never collide on the
        same database name.
        """
        if self.target_db is None:
            return None
        return f"{self.target_db}_{uuid.uuid4().hex[:8]}"

    def build_out_stage(
        self, collection: Collection, *, resolved_db: str | None = None
    ) -> dict[str, Any]:
        """Build the ``$out`` stage spec from this test case.

        Args:
            collection: The source collection fixture.
            resolved_db: Pre-resolved database name from
                :meth:`resolve_target_db`.  When ``None`` and
                ``target_db`` is set, falls back to the raw
                ``target_db`` value (callers should prefer passing a
                resolved name for parallel safety).
        """
        db_name = resolved_db or self.target_db or collection.database.name
        target = target_name(collection, self)
        if self.out_spec is not None or self.target_db is not None:
            spec: dict[str, Any] = {"db": db_name, "coll": target}
            if self.out_spec:
                spec.update(self.out_spec)
            return {"$out": spec}
        return {"$out": target}


def target_name(collection: Collection, test_case: OutTestCase) -> str:
    """Return the full target collection name, unique per test worker.

    Uses ``test_case.target_coll`` when explicitly set, otherwise falls
    back to ``test_case.id`` so every test case automatically gets a
    collision-free target without the author having to invent a name.
    """
    suffix = test_case.target_coll if test_case.target_coll is not None else test_case.id
    return f"{collection.name}_{suffix}"
