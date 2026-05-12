"""Tests for listCollections command."""

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.target_collection import (
    ViewCollection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, IsType, NotExists
from documentdb_tests.framework.test_constants import INT64_ZERO

# Property [Response Structure (nameOnly=false)]: each result document
# for a regular collection contains name (string), type (string),
# options (document), info (document), and idIndex (document); idIndex
# is absent for views; ok is 1.0 (double), cursor.ns is
# <db>.$cmd.listCollections, and cursor.id is Int64(0) when all results
# fit in firstBatch.
RESPONSE_STRUCTURE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.ns": Eq(f"{ctx.database}.$cmd.listCollections"),
            "cursor.id": Eq(INT64_ZERO),
            "cursor.firstBatch.0": {
                "name": IsType("string"),
                "type": IsType("string"),
                "options": IsType("object"),
                "info": IsType("object"),
                "idIndex": IsType("object"),
            },
        },
        msg="Regular collection should have all standard fields",
        id="regular_collection_fields",
    ),
    CommandTestCase(
        target_collection=ViewCollection(),
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.ns": Eq(f"{ctx.database}.$cmd.listCollections"),
            "cursor.id": Eq(INT64_ZERO),
            "cursor.firstBatch.0": {
                "name": IsType("string"),
                "type": Eq("view"),
                "options": IsType("object"),
                "info": IsType("object"),
                "idIndex": NotExists(),
            },
        },
        msg="View should not have idIndex field",
        id="view_no_id_index",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RESPONSE_STRUCTURE_TESTS))
def test_listCollections_response_structure(database_client, collection, test):
    """Test listCollections command input acceptance and output structure."""
    target = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(target)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
