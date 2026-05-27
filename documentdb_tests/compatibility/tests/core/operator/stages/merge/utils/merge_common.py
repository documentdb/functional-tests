"""Shared infrastructure for $merge stage tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)


def _setup_merge_target(
    collection: Any,
    test_case: StageTestCase,
    target_docs: Any = None,
    target_indexes: list[IndexModel] | None = None,
) -> str:
    """Populate the source collection and a per-test target collection.

    Drops the target, then creates it per ``target_docs`` (None=not created,
    []=created empty, [..]=created with documents) and applies ``target_indexes``.
    Returns the target collection name.
    """
    db = collection.database
    target = f"{collection.name}_{test_case.id}"
    populate_collection(collection, test_case)
    db.drop_collection(target)
    if target_docs is not None:
        if target_docs:
            db[target].insert_many(target_docs)
        else:
            db.create_collection(target)
    if target_indexes:
        db[target].create_indexes(target_indexes)
    return target


# Sentinel for the dynamic target collection name. Test cases write the sentinel
# into the pipeline definition wherever the runtime target collection should
# appear.
TARGET = object()


def _substitute_target(pipeline: list[dict[str, Any]], target: str) -> list[dict[str, Any]]:
    """Replace all ``TARGET`` sentinel occurrences in the pipeline with ``target``."""

    def _replace(obj: Any) -> Any:
        if obj is TARGET:
            return target
        if isinstance(obj, dict):
            return {k: _replace(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_replace(item) for item in obj]
        return obj

    return cast(list[dict[str, Any]], _replace(pipeline))


@dataclass(frozen=True)
class MergeTestCase(StageTestCase):
    """Test case for $merge behavior.

    Attributes:
        target_docs: Documents to pre-populate in the target collection.
            None means the target is not created, [] creates it empty.
        target_indexes: Indexes to create on the target collection.
        agg_options: Additional fields merged into the aggregate command.

    Use the ``TARGET`` sentinel in the pipeline wherever the runtime target
    collection name should be substituted.
    """

    target_docs: list[dict[str, Any]] | None = None
    agg_options: dict[str, Any] | None = None
    target_indexes: list[IndexModel] | None = None

    def prepare(self, collection: Any) -> str:
        """Populate the source and per-test target collections.

        Returns the per-test target collection name, which the caller passes to
        :meth:`build_command` (and uses when reading the target back).
        """
        return _setup_merge_target(
            collection,
            self,
            target_docs=self.target_docs,
            target_indexes=self.target_indexes,
        )

    def build_command(self, collection: Any, target: str) -> dict[str, Any]:
        """Build the aggregate command that runs the $merge pipeline.

        Substitutes the ``TARGET`` sentinel with ``target`` and applies
        ``agg_let`` and ``agg_options`` when present.
        """
        agg_cmd: dict[str, Any] = {
            "aggregate": collection.name,
            "pipeline": _substitute_target(self.pipeline, target),
            "cursor": {},
        }
        if self.agg_options:
            agg_cmd.update(self.agg_options)
        return agg_cmd
