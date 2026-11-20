"""Tests for $sample stage statistical properties.

These tests verify statistical properties (randomness, distribution) of
$sample, which require repeated execution rather than the single-command
StageTestCase pattern. Each test computes its statistic over the repeated
runs and checks it with assertSuccess.
"""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


# Property [Randomness]: repeated executions of the same $sample pipeline may
# return different documents.
@pytest.mark.aggregate
def test_sample_statistical_randomness(collection):
    """Test $sample can reach every document in the collection.

    Samples size=1 repeatedly until every document has been seen at least once.
    """
    # Expected completion is ~12 iterations for n_docs=5.
    n_docs = 5
    # False failure is not expected even if the test ran once per second until
    # the heat death of the universe for max_iterations=1500.
    max_iterations = 1500

    all_ids = set(range(n_docs))
    collection.insert_many([{"_id": i} for i in all_ids])
    seen: set[int] = set()
    result = None
    for _ in range(max_iterations):
        result = execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [{"$sample": {"size": 1}}],
                "cursor": {},
            },
        )
        if isinstance(result, Exception):
            break
        seen.add(result["cursor"]["firstBatch"][0]["_id"])
        if seen == all_ids:
            break

    # An error from any run is reported as is; otherwise check which documents
    # were never returned.
    summary = result if isinstance(result, Exception) else {"unreached": sorted(all_ids - seen)}
    assertSuccess(
        summary,
        {"unreached": []},
        raw_res=True,
        msg=f"$sample should reach every document within {max_iterations} iterations",
    )


# Property [Uniformity]: $sample selects documents with approximately equal
# probability rather than favoring particular documents.
@pytest.mark.aggregate
def test_sample_statistical_uniformity(collection):
    """Test $sample selects each document with roughly equal probability.

    Samples size=1 repeatedly and checks every document is selected often enough.
    """
    n_docs = 5
    # Expected count per document is n_samples/n_docs = 600.
    n_samples = 3000
    # False failure is not expected even if the test ran once per second until
    # the heat death of the universe for min_count=50.
    min_count = 50

    collection.insert_many([{"_id": i} for i in range(n_docs)])
    counts: dict[int, int] = dict.fromkeys(range(n_docs), 0)
    result = None
    for _ in range(n_samples):
        result = execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [{"$sample": {"size": 1}}],
                "cursor": {},
            },
        )
        if isinstance(result, Exception):
            break
        counts[result["cursor"]["firstBatch"][0]["_id"]] += 1

    # An error from any run is reported as is; otherwise check which documents
    # were selected fewer than min_count times.
    if isinstance(result, Exception):
        summary = result
    else:
        summary = {"underfilled": sorted(k for k, v in counts.items() if v < min_count)}
    assertSuccess(
        summary,
        {"underfilled": []},
        raw_res=True,
        msg=(
            f"$sample should select every document at least {min_count} times out of "
            f"{n_samples} (expected ~{n_samples // n_docs})"
        ),
    )
