"""Tests for $searchMeta operator/collector presence and index spec errors."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.searchMeta.utils.searchMeta_common import (  # noqa: E501
    open_search_collection,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNKNOWN_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ZERO

pytestmark = pytest.mark.requires(search=True)


@pytest.fixture(scope="module")
def search_collection(engine_client, worker_id) -> Iterator[Collection]:
    """Module-scoped metadata search collection (default + alt_idx indexes)."""
    with open_search_collection(engine_client, worker_id, f"{__name__}::search_collection") as coll:
        yield coll


# Property [Operator Value Not A Document]: a present operator-key value that is
# not a document is rejected.
SEARCHMETA_OPERATOR_VALUE_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"operator_value_{tid}",
        pipeline=[{"$searchMeta": {"text": val}}],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} operator value as not a document",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ZERO),
        ("bool", True),
        ("array", [1, 2]),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [No Operator Or Collector Present]: a spec that the server reads as
# having no recognized operator and no collector is rejected.
SEARCHMETA_NO_OPERATOR_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "no_operator_unknown_name",
        pipeline=[{"$searchMeta": {"unknownop": {"query": "quick", "path": "title"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject an unrecognized operator name as no operator present",
    ),
    StageTestCase(
        "no_operator_empty_spec",
        pipeline=[{"$searchMeta": {}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject an empty spec as no operator present",
    ),
    StageTestCase(
        "no_operator_modifier_only",
        pipeline=[{"$searchMeta": {"count": {"type": "total"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a spec with only modifiers as no operator present",
    ),
    StageTestCase(
        "no_operator_capitalized_key",
        pipeline=[{"$searchMeta": {"Text": {"query": "quick", "path": "title"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should treat a capitalized operator key as unrecognized, not present",
    ),
    StageTestCase(
        "no_operator_untrimmed_key",
        pipeline=[{"$searchMeta": {"text ": {"query": "quick", "path": "title"}}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should treat an untrimmed operator key as unrecognized, not present",
    ),
    StageTestCase(
        "no_operator_value_null",
        pipeline=[{"$searchMeta": {"text": None}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should treat a null operator value as field-absent, not present",
    ),
    StageTestCase(
        "no_operator_facet_null",
        pipeline=[{"$searchMeta": {"facet": None}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should treat a null facet value as field-absent, not present",
    ),
]

# Property [Conflicting Operators And Collector]: a spec carrying more than one
# query specifier (a top-level operator plus a facet collector, or two top-level
# operators) is rejected.
SEARCHMETA_OPERATOR_CONFLICT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "conflict_operator_and_collector",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "facet": {
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": [0, 25]}}
                    },
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a spec carrying both an operator and a facet collector",
    ),
    StageTestCase(
        "conflict_two_operators",
        pipeline=[
            {
                "$searchMeta": {
                    "text": {"query": "quick", "path": "title"},
                    "equals": {"path": "n", "value": 1},
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a spec carrying two top-level operators",
    ),
]

# Property [Index Not A String]: an index value that is not a string and not
# null is rejected.
SEARCHMETA_INDEX_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"index_not_string_{tid}",
        pipeline=[{"$searchMeta": {"text": {"query": "quick", "path": "title"}, "index": val}}],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} index value as not a string",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ZERO),
        ("bool", True),
        ("array", [1, 2]),
        ("object", {"a": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Index Empty String]: an empty-string index is rejected.
SEARCHMETA_INDEX_EMPTY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "index_empty_string",
        pipeline=[{"$searchMeta": {"text": {"query": "quick", "path": "title"}, "index": ""}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject an empty-string index value",
    ),
]

# Property [Unknown Top-Level Option]: a top-level field that is not a recognized
# option is rejected; matching is exact, case-sensitive, and not
# whitespace-trimmed. ($search output options like sort/highlight are accepted as
# no-ops, so they are not unrecognized and not asserted here.)
SEARCHMETA_UNKNOWN_OPTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"unknown_option_{suffix}",
        pipeline=[{"$searchMeta": {"text": {"query": "quick", "path": "title"}, name: value}}],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {suffix} top-level option as an unrecognized field",
    )
    for name, value, suffix in [
        ("bogus", 1, "garbage_name"),
        ("Index", "default", "capitalized_index"),
        ("index ", "default", "trailing_space_index"),
    ]
]

SEARCHMETA_SPEC_OPERATOR_ERROR_TESTS: list[StageTestCase] = (
    SEARCHMETA_OPERATOR_VALUE_TYPE_ERROR_TESTS
    + SEARCHMETA_NO_OPERATOR_ERROR_TESTS
    + SEARCHMETA_OPERATOR_CONFLICT_ERROR_TESTS
    + SEARCHMETA_INDEX_TYPE_ERROR_TESTS
    + SEARCHMETA_INDEX_EMPTY_ERROR_TESTS
    + SEARCHMETA_UNKNOWN_OPTION_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_SPEC_OPERATOR_ERROR_TESTS))
def test_searchMeta_spec_operator_errors(search_collection, test_case: StageTestCase):
    """Test $searchMeta operator/collector presence and index spec errors."""
    result = execute_command(
        search_collection,
        {
            "aggregate": search_collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
