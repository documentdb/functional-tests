"""Tests for $searchMeta facet collector and definition spec errors."""

from __future__ import annotations

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

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import UNKNOWN_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ZERO

pytestmark = pytest.mark.requires(search=True)


# Property [Facet Value Not A Document]: a present facet value that is not a
# document is rejected.
SEARCHMETA_FACET_VALUE_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"facet_not_document_{tid}",
        pipeline=[{"$searchMeta": {"facet": val}}],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} facet value as not a document",
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

# Property [Facet Facets Required]: a facet collector whose facets field is
# omitted or null is rejected.
SEARCHMETA_FACETS_REQUIRED_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "facets_omitted",
        pipeline=[{"$searchMeta": {"facet": {}}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a facet collector with facets omitted",
    ),
    StageTestCase(
        "facets_null",
        pipeline=[{"$searchMeta": {"facet": {"facets": None}}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should treat a null facets value as field-absent and require facets",
    ),
]

# Property [Facet Facets Not A Document]: a present facet.facets value that is
# not a document is rejected.
SEARCHMETA_FACETS_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"facets_not_document_{tid}",
        pipeline=[{"$searchMeta": {"facet": {"facets": val}}}],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} facet.facets value as not a document",
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

# Property [Facet Facets Empty]: an empty facet.facets document is rejected.
SEARCHMETA_FACETS_EMPTY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "facets_empty",
        pipeline=[{"$searchMeta": {"facet": {"facets": {}}}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject an empty facet.facets document",
    ),
]

# Property [Facet Operator Empty]: an empty facet.operator document is rejected.
SEARCHMETA_FACET_OPERATOR_EMPTY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "facet_operator_empty",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "operator": {},
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": [0, 25]}},
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject an empty facet operator by listing the valid operators",
    ),
]

# Property [Facet Definition Required Fields]: a facet definition missing its
# type or path is rejected.
SEARCHMETA_FACET_DEF_REQUIRED_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "facet_def_missing_type",
        pipeline=[
            {"$searchMeta": {"facet": {"facets": {"nf": {"path": "n", "boundaries": [0, 25]}}}}}
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a facet definition missing its type",
    ),
    StageTestCase(
        "facet_def_missing_path",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {"facets": {"nf": {"type": "number", "boundaries": [0, 25]}}}
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a facet definition missing its path",
    ),
    StageTestCase(
        "facet_def_missing_boundaries",
        pipeline=[{"$searchMeta": {"facet": {"facets": {"nf": {"type": "number", "path": "n"}}}}}],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a number facet definition missing its boundaries",
    ),
]

# Property [Facet Definition Type Value]: a facet definition type outside
# {date, number, string} is rejected.
SEARCHMETA_FACET_DEF_TYPE_VALUE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "facet_def_type_unknown",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {"facets": {"nf": {"type": "foo", "path": "n", "boundaries": [0, 25]}}}
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a facet definition type outside the allowed set",
    ),
]

# Property [Facet Definition Not A Document]: a facet definition value that is
# not a document is rejected.
SEARCHMETA_FACET_DEF_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"facet_def_not_document_{tid}",
        pipeline=[{"$searchMeta": {"facet": {"facets": {"nf": val}}}}],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} facet definition value as not a document",
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

# Property [Facet Path Type]: a facet definition path must be a string, so a
# non-string path is rejected. A null path is treated as missing, so it is
# excluded.
SEARCHMETA_FACET_PATH_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"facet_path_type_{tid}",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "number", "path": val, "boundaries": [0, 25]}}
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} facet path as not a string",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ZERO),
        ("bool", True),
        ("object", {"a": 1}),
        ("array", ["n"]),
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

# Property [Facet Boundaries Type]: a number-facet boundaries value must be an
# array, so a non-array boundaries value is rejected. A null boundaries is
# treated as missing, so it is excluded.
SEARCHMETA_FACET_BOUNDARIES_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"facet_boundaries_type_{tid}",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {"facets": {"nf": {"type": "number", "path": "n", "boundaries": val}}}
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} boundaries value as not an array",
    )
    for tid, val in [
        ("string", "x"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ZERO),
        ("bool", True),
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

# Property [Facet Default Type]: a number-facet default overflow bucket name
# must be a string, so a non-string default is rejected. A null default is
# treated as no default, so it is excluded.
SEARCHMETA_FACET_DEFAULT_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"facet_default_type_{tid}",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {
                            "nf": {
                                "type": "number",
                                "path": "n",
                                "boundaries": [0, 5],
                                "default": val,
                            }
                        }
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg=f"$searchMeta should reject a {tid} facet default as not a string",
    )
    for tid, val in [
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", DECIMAL128_ZERO),
        ("bool", True),
        ("object", {"a": 1}),
        ("array", ["over"]),
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

# Property [Facet Unrecognized Field]: an unrecognized field at the facet
# definition or collector level, including a count modifier placed inside the
# collector, is rejected.
SEARCHMETA_FACET_UNKNOWN_FIELD_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "facet_def_unknown_field",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {
                            "nf": {
                                "type": "number",
                                "path": "n",
                                "boundaries": [0, 25],
                                "bogus": 1,
                            }
                        }
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject an unrecognized field in a facet definition",
    ),
    StageTestCase(
        "facet_collector_unknown_field",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": [0, 25]}},
                        "bogus": 1,
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject an unrecognized field at the facet collector level",
    ),
    StageTestCase(
        "facet_collector_count_inside",
        pipeline=[
            {
                "$searchMeta": {
                    "facet": {
                        "facets": {"nf": {"type": "number", "path": "n", "boundaries": [0, 25]}},
                        "count": {"type": "total"},
                    }
                }
            }
        ],
        error_code=UNKNOWN_ERROR,
        msg="$searchMeta should reject a count modifier placed inside the facet collector",
    ),
]

SEARCHMETA_SPEC_FACET_ERROR_TESTS: list[StageTestCase] = (
    SEARCHMETA_FACET_VALUE_TYPE_ERROR_TESTS
    + SEARCHMETA_FACETS_REQUIRED_ERROR_TESTS
    + SEARCHMETA_FACETS_TYPE_ERROR_TESTS
    + SEARCHMETA_FACETS_EMPTY_ERROR_TESTS
    + SEARCHMETA_FACET_OPERATOR_EMPTY_ERROR_TESTS
    + SEARCHMETA_FACET_DEF_REQUIRED_ERROR_TESTS
    + SEARCHMETA_FACET_DEF_TYPE_VALUE_ERROR_TESTS
    + SEARCHMETA_FACET_DEF_TYPE_ERROR_TESTS
    + SEARCHMETA_FACET_PATH_TYPE_ERROR_TESTS
    + SEARCHMETA_FACET_BOUNDARIES_TYPE_ERROR_TESTS
    + SEARCHMETA_FACET_DEFAULT_TYPE_ERROR_TESTS
    + SEARCHMETA_FACET_UNKNOWN_FIELD_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SEARCHMETA_SPEC_FACET_ERROR_TESTS))
def test_searchMeta_spec_facet_errors(search_collection, test_case: StageTestCase):
    """Test $searchMeta facet collector and definition spec errors."""
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
