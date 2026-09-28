"""Shared fixtures for $searchMeta stage tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.searchMeta.utils.searchMeta_common import (  # noqa: E501
    open_search_collection,
)


@pytest.fixture(scope="package")
def search_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Metadata search collection carrying a ``default`` and a non-default
    ``alt_idx`` index, for tests that select an index by name.

    Package-scoped and read-only: the search index is built and polled to READY
    once for all $searchMeta tests that request it."""
    with open_search_collection(
        engine_client, worker_id, "stages_searchmeta_shared::search_collection"
    ) as coll:
        yield coll
