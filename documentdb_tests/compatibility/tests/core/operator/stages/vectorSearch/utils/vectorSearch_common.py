"""Shared dataclass and pre-filter constants for $vectorSearch stage tests.

The ``VectorSearchTest`` dataclass tags each case with the fixture and execution
mode it runs under. The ObjectId/UUID constants are stored on the shared corpus
(see conftest.py) and queried back by the filter, parentFilter, and
explainOptions test files, so they live here rather than in any single file."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from bson import ObjectId
from bson.binary import Binary, UuidRepresentation

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)


@dataclass(frozen=True)
class VectorSearchTest(StageTestCase):
    """A $vectorSearch case, tagged with the collection fixture and execution mode it runs under."""

    collection_fixture: str = "vector_search_collection"
    explain: bool = False
    raw_res: bool = False


# ObjectId and UUID values for the filter pre-filtering tests. The specific
# values are arbitrary; only the A/B partition matters: each is stored on some
# corpus docs and queried back, so a filter on "A" must return exactly the docs
# that stored "A" and none that stored "B".
_FILTER_OID_A = ObjectId("5a9427648b0beebeb69537a5")

_FILTER_OID_B = ObjectId("5a9427648b0beebeb69537b6")

_FILTER_UUID_A = Binary.from_uuid(
    uuid.UUID("11111111-1111-1111-1111-111111111111"), UuidRepresentation.STANDARD
)

_FILTER_UUID_B = Binary.from_uuid(
    uuid.UUID("22222222-2222-2222-2222-222222222222"), UuidRepresentation.STANDARD
)
