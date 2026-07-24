"""Shared plumbing and corpus for $search stage tests.

$search tests cannot use the per-case declarative ``docs``/``indexes`` model: a
search index is heavyweight (created, then polled until queryable), so the
corpus and index are built once per package by the package-scoped
``indexed_collection`` fixture (see conftest.py) rather than per test case. This
module holds the create/poll helpers, the shared option constants, and the
dynamic-mapping corpus that fixture populates."""

from __future__ import annotations

import time
from typing import Any

from pymongo.collection import Collection
from pymongo.operations import SearchIndexModel

SEARCH_INDEX_NAME = "default"
INDEX_READY_TIMEOUT_SECONDS = 120

# Maximum number of query clauses the text operator accepts (inclusive); 'in' has no such cap.
QUERY_CLAUSE_CAP = 1024

# Shared corpus for the dynamic-mapping index. Docs 6-18 carry tokens probed only
# by specific analyzer, normalization, token-boundary, and fuzzy cases; none
# contains `quick`/`turtle`, so they do not perturb the matching, scoring, or
# count assertions in the other files.
FIXTURE_DOCS = [
    {"_id": 1, "title": "the quick brown fox", "body": "lazy dog"},
    {"_id": 2, "title": "slow green turtle", "body": "quick nap"},  # `quick` in body
    {"_id": 3, "title": "a quick quick quick rabbit"},  # repeats `quick` for the top score
    {"_id": 4, "title": "$quick literal dollar"},  # leading `$` matched as literal text
    {"_id": 5, "title": "mon résumé est prêt"},  # multi-byte token for highlight spans
    {"_id": 6, "title": "x"},  # single-character token
    {"_id": 7, "title": "σιγμα"},  # lowercase Greek
    {"_id": 8, "title": "день"},  # lowercase Cyrillic
    {"_id": 9, "title": "\U00010428"},  # Deseret small letter long I (U+10428)
    {"_id": 10, "title": "resume"},  # plain ASCII, distinct from doc 5's résumé
    {"_id": 11, "title": "caf\u00e9"},  # precomposed é (U+00E9)
    {"_id": 12, "title": "\ufb01le"},  # ligature ﬁ (U+FB01) + le
    {"_id": 13, "title": "stra\u00dfe"},  # German eszett (U+00DF)
    {"_id": 14, "title": "\u0131rmak"},  # Turkish dotless i (U+0131)
    {"_id": 15, "title": "a z"},  # ASCII range-edge letters as separate tokens
    {"_id": 16, "title": "word joined"},  # two tokens: word, joined
    {"_id": 17, "title": "wordjoined"},  # one token
    {"_id": 18, "title": "\u00e9fox"},  # 4 code points / 5 bytes (é is 2 bytes)
]


def create_search_index(collection: Collection, definition: dict[str, Any]) -> None:
    """Create a search index from a definition and poll until it is queryable."""
    collection.create_search_index(SearchIndexModel(definition=definition, name=SEARCH_INDEX_NAME))
    deadline = time.monotonic() + INDEX_READY_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        indexes = list(collection.list_search_indexes(SEARCH_INDEX_NAME))
        if indexes and indexes[0].get("queryable"):
            return
        time.sleep(1)
    raise RuntimeError(
        f"search index {SEARCH_INDEX_NAME!r} did not become queryable within "
        f"{INDEX_READY_TIMEOUT_SECONDS}s"
    )


def create_dynamic_search_index(collection: Collection) -> None:
    """Create a dynamic-mapping search index and poll until it is queryable."""
    create_search_index(collection, {"mappings": {"dynamic": True}})
