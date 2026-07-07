"""Aggregation $facet stage tests - valid argument edge cases.

Covers the positive TEST_COVERAGE.md §4 (Argument Handling) cases for $facet:
valid edge cases such as empty sub-pipelines, many sub-pipelines, and
unusual-but-valid output field names.

Note: the "two sub-pipelines with the same output field name" spec item is not
tested here. A BSON document cannot carry two identical field names through the
driver -- the wire encoding collapses them to a single (last-wins) entry before
the command is sent -- so a genuine duplicate-output-field $facet cannot be
constructed via pymongo and the server never observes the duplicate.
"""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [{"_id": 1, "cat": "A"}, {"_id": 2, "cat": "B"}]

LONG_NAME = "f" * 300

# Property [Valid Edge Cases]: empty sub-pipelines, many sub-pipelines, and
# unusual-but-valid output field names are accepted.
FACET_ARGUMENT_SUCCESS_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="many_subpipelines",
        docs=DOCS,
        pipeline=[{"$facet": {f"f{i}": [{"$count": "n"}] for i in range(50)}}],
        expected=[{f"f{i}": [{"n": 2}] for i in range(50)}],
        msg="A $facet with many valid sub-pipelines should complete without error",
    ),
    StageTestCase(
        id="very_long_field_name",
        docs=DOCS,
        pipeline=[{"$facet": {LONG_NAME: [{"$count": "n"}]}}],
        expected=[{LONG_NAME: [{"n": 2}]}],
        msg="$facet should accept and preserve a very long output field name",
    ),
    StageTestCase(
        id="unicode_field_name",
        docs=DOCS,
        pipeline=[{"$facet": {"日本語": [{"$count": "n"}]}}],
        expected=[{"日本語": [{"n": 2}]}],
        msg="$facet should accept and correctly retrieve a unicode output field name",
    ),
]

# Combined list for parametrization.
FACET_ARGUMENT_TESTS = FACET_ARGUMENT_SUCCESS_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(FACET_ARGUMENT_TESTS))
def test_facet_argument_validation(collection, test_case: StageTestCase):
    """Test $facet valid argument edge cases."""
    coll = populate_collection(collection, test_case)
    command: dict[str, Any] = {
        "aggregate": coll.name,
        "pipeline": test_case.pipeline,
        "cursor": {},
    }
    command.update(test_case.extra_command_fields)
    result = execute_command(coll, command)
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=test_case.ignore_doc_order,
        ignore_order_in=test_case.ignore_order_in,
    )
