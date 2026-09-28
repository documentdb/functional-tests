"""Shared fixtures for $search stage tests.

The dynamic-mapping ``indexed_collection`` corpus is queried read-only by most
$search test files, so it is built once per package here rather than duplicated
per file. Single-operator corpora (wildcard, equals, in, ...) stay inline in
their own test file, since each is used by exactly one file."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.search.utils.search_common import (
    FIXTURE_DOCS,
    create_dynamic_search_index,
)
from documentdb_tests.framework import fixtures


@pytest.fixture(scope="package")
def indexed_collection(engine_client, worker_id):
    """A package-scoped collection populated with the fixture docs and a ready
    dynamic search index, shared read-only across the matching tests so the
    index is built and polled once rather than per test."""
    db_name = fixtures.generate_database_name("stages_search_shared", worker_id)
    fixtures.cleanup_database(engine_client, db_name)
    db = engine_client[db_name]
    coll = db["indexed"]
    coll.insert_many(FIXTURE_DOCS)
    create_dynamic_search_index(coll)
    yield coll
    fixtures.cleanup_database(engine_client, db_name)
