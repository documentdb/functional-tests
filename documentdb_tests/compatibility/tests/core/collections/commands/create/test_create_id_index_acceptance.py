"""Tests for the create command idIndex acceptance behavior."""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [IdIndex Null Bypass]: null idIndex is treated as omitted and the
# default _id index is created.
CREATE_ID_INDEX_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="null_treated_as_omitted",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": None,
        },
        expected={"ok": 1.0},
        msg="idIndex:null should be treated as omitted",
    ),
]

# Property [IdIndex Valid Specifications]: a valid idIndex with key:{_id:1} and
# a name creates the collection successfully. Version accepts int32, int64, and
# integral doubles for values 1 and 2.
CREATE_ID_INDEX_VALID_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="minimal_valid",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_"},
        },
        expected={"ok": 1.0},
        msg="Minimal valid idIndex should succeed",
    ),
    CommandTestCase(
        id="explicit_v2",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "v": 2},
        },
        expected={"ok": 1.0},
        msg="idIndex with explicit v:2 should succeed",
    ),
    CommandTestCase(
        id="explicit_v1",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "v": 1},
        },
        expected={"ok": 1.0},
        msg="idIndex with v:1 should succeed",
    ),
    CommandTestCase(
        id="v_int64",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "v": Int64(2)},
        },
        expected={"ok": 1.0},
        msg="idIndex with v as Int64(2) should succeed",
    ),
    CommandTestCase(
        id="v_double_2_0",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "v": 2.0},
        },
        expected={"ok": 1.0},
        msg="idIndex with v as double 2.0 should succeed",
    ),
]

# Property [IdIndex Name Normalization]: a custom name in idIndex is silently
# normalized to "_id_" regardless of the value provided.
CREATE_ID_INDEX_NAME_NORMALIZATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="custom_name_normalized",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "custom_name"},
        },
        expected={"ok": 1.0},
        msg="Custom name in idIndex should be silently normalized to _id_",
    ),
]

# Property [IdIndex Collation Matching]: idIndex collation must match the
# collection collation; when omitted it inherits the collection's.
CREATE_ID_INDEX_COLLATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="collation_simple_no_collection_collation",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "collation": {"locale": "simple"}},
        },
        expected={"ok": 1.0},
        msg="idIndex with collation simple on non-collated collection should succeed",
    ),
    CommandTestCase(
        id="collation_matches_collection",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en"},
            "idIndex": {"key": {"_id": 1}, "name": "_id_", "collation": {"locale": "en"}},
        },
        expected={"ok": 1.0},
        msg="idIndex collation matching collection collation should succeed",
    ),
    CommandTestCase(
        id="collation_omitted_inherits_collection",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "collation": {"locale": "en"},
            "idIndex": {"key": {"_id": 1}, "name": "_id_"},
        },
        expected={"ok": 1.0},
        msg="idIndex without collation should inherit collection collation",
    ),
]

# Property [IdIndex Compatibility]: idIndex is compatible with capped
# collections.
CREATE_ID_INDEX_COMPATIBILITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="compatible_with_capped",
        command=lambda ctx: {
            "create": f"{ctx.collection}_custom",
            "capped": True,
            "size": 4096,
            "idIndex": {"key": {"_id": 1}, "name": "_id_"},
        },
        expected={"ok": 1.0},
        msg="idIndex with capped collection should succeed",
    ),
]

CREATE_ID_INDEX_ACCEPTANCE_TESTS: list[CommandTestCase] = (
    CREATE_ID_INDEX_NULL_TESTS
    + CREATE_ID_INDEX_VALID_TESTS
    + CREATE_ID_INDEX_NAME_NORMALIZATION_TESTS
    + CREATE_ID_INDEX_COLLATION_TESTS
    + CREATE_ID_INDEX_COMPATIBILITY_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CREATE_ID_INDEX_ACCEPTANCE_TESTS))
def test_create_id_index_acceptance(database_client, collection, test):
    """Test create command idIndex acceptance behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
