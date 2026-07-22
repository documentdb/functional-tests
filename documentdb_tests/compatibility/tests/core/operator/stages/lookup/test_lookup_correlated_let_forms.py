"""Tests for $lookup correlated subquery — let variable forms and type preservation.

Covers comprehensive let variable value forms beyond what exists in
test_lookup_correlated_subquery.py: additional BSON types (ObjectId, Decimal128,
BinData, Timestamp, Regex, MinKey, MaxKey), field path traversal patterns,
complex aggregation expressions, and mixed multi-variable let specifications.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey

from documentdb_tests.compatibility.tests.core.operator.stages.lookup.utils.lookup_common import (
    FOREIGN,
    LookupTestCase,
    build_lookup_command,
    setup_lookup,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    BSON_TYPE_SAMPLES,
    DATE_Y2K,
    OID_EPOCH,
    TS_EPOCH,
    BsonType,
)

# Property [Correlated Subquery — Let Forms]: let variables accept any BSON
# type and aggregation expression as value; type and precision are preserved
# through the sub-pipeline.


LOOKUP_LET_CONSTANT_LITERAL_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_constant_int64",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": Int64(9999999999)},
                    "pipeline": [{"$addFields": {"val": "$$x", "t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "joined": [{"_id": 10, "val": Int64(9999999999), "t": "long"}],
            }
        ],
        msg="$lookup let with Int64 constant should preserve long type",
    ),
    LookupTestCase(
        "let_constant_decimal128",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": Decimal128("123.456")},
                    "pipeline": [{"$addFields": {"val": "$$x", "t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "joined": [{"_id": 10, "val": Decimal128("123.456"), "t": "decimal"}],
            }
        ],
        msg="$lookup let with Decimal128 constant should preserve decimal type",
    ),
    LookupTestCase(
        "let_constant_objectid",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": OID_EPOCH},
                    "pipeline": [{"$addFields": {"val": "$$x", "t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "joined": [{"_id": 10, "val": OID_EPOCH, "t": "objectId"}],
            }
        ],
        msg="$lookup let with ObjectId constant should preserve objectId type",
    ),
    LookupTestCase(
        "let_constant_date",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": DATE_Y2K},
                    "pipeline": [{"$addFields": {"val": "$$x", "t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "joined": [{"_id": 10, "val": DATE_Y2K, "t": "date"}],
            }
        ],
        msg="$lookup let with ISODate constant should preserve date type",
    ),
    LookupTestCase(
        "let_constant_binary",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": Binary(b"\x00\x01\x02", 128)},
                    "pipeline": [{"$addFields": {"val": "$$x", "t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "joined": [{"_id": 10, "val": Binary(b"\x00\x01\x02", 128), "t": "binData"}],
            }
        ],
        msg="$lookup let with BinData constant should preserve binData type",
    ),
    LookupTestCase(
        "let_constant_timestamp",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": TS_EPOCH},
                    "pipeline": [{"$addFields": {"val": "$$x", "t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "joined": [{"_id": 10, "val": TS_EPOCH, "t": "timestamp"}],
            }
        ],
        msg="$lookup let with Timestamp constant should preserve timestamp type",
    ),
    LookupTestCase(
        "let_constant_regex",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": BSON_TYPE_SAMPLES[BsonType.REGEX]},
                    "pipeline": [{"$addFields": {"t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "joined": [{"_id": 10, "t": "regex"}],
            }
        ],
        msg="$lookup let with Regex constant should preserve regex type",
    ),
    LookupTestCase(
        "let_constant_minkey",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": MinKey()},
                    "pipeline": [{"$addFields": {"t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "joined": [{"_id": 10, "t": "minKey"}],
            }
        ],
        msg="$lookup let with MinKey constant should preserve minKey type",
    ),
    LookupTestCase(
        "let_constant_maxkey",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": MaxKey()},
                    "pipeline": [{"$addFields": {"t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "joined": [{"_id": 10, "t": "maxKey"}],
            }
        ],
        msg="$lookup let with MaxKey constant should preserve maxKey type",
    ),
]


LOOKUP_LET_FIELD_REFERENCE_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_field_ref_nested_path",
        docs=[{"_id": 1, "nested": {"field": 42}}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$nested.field"},
                    "pipeline": [{"$addFields": {"val": "$$x"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "nested": {"field": 42}, "joined": [{"_id": 10, "val": 42}]}],
        msg="$lookup let with nested field path should resolve nested document field",
    ),
    LookupTestCase(
        "let_field_ref_deeply_nested",
        docs=[{"_id": 1, "a": {"b": {"c": {"d": "deep"}}}}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$a.b.c.d"},
                    "pipeline": [{"$addFields": {"val": "$$x"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "a": {"b": {"c": {"d": "deep"}}},
                "joined": [{"_id": 10, "val": "deep"}],
            }
        ],
        msg="$lookup let with deeply nested field path should resolve through multiple levels",
    ),
    LookupTestCase(
        "let_field_ref_array_field",
        docs=[{"_id": 1, "arr": [10, 20, 30]}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$arr"},
                    "pipeline": [{"$addFields": {"val": "$$x"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "arr": [10, 20, 30], "joined": [{"_id": 10, "val": [10, 20, 30]}]}],
        msg="$lookup let with field path to array should pass entire array as variable value",
    ),
    LookupTestCase(
        "let_field_ref_dotted_through_array_of_objects",
        docs=[{"_id": 1, "items": [{"name": "a"}, {"name": "b"}]}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$items.name"},
                    "pipeline": [{"$addFields": {"val": "$$x"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "items": [{"name": "a"}, {"name": "b"}],
                "joined": [{"_id": 10, "val": ["a", "b"]}],
            }
        ],
        msg=(
            "$lookup let with dotted path through array-of-objects should"
            " resolve to array of matched values"
        ),
    ),
    LookupTestCase(
        "let_field_ref_null_field",
        docs=[{"_id": 1, "nullField": None}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": "$nullField"},
                    "pipeline": [{"$addFields": {"val": "$$x", "t": {"$type": "$$x"}}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "nullField": None,
                "joined": [{"_id": 10, "val": None, "t": "null"}],
            }
        ],
        msg="$lookup let with field path to null field should resolve to null (not missing)",
    ),
    LookupTestCase(
        "let_field_ref_arrayElemAt_expression",
        docs=[{"_id": 1, "arr": [10, 20, 30]}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": {"$arrayElemAt": ["$arr", 0]}},
                    "pipeline": [{"$addFields": {"val": "$$x"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "arr": [10, 20, 30], "joined": [{"_id": 10, "val": 10}]}],
        msg="$lookup let with $arrayElemAt expression should extract single array element",
    ),
]


LOOKUP_LET_EXPRESSION_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_expr_cond_true_branch",
        docs=[{"_id": 1, "val": 10}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": {"$cond": [{"$gt": ["$val", 5]}, "high", "low"]}},
                    "pipeline": [{"$addFields": {"label": "$$x"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "val": 10, "joined": [{"_id": 10, "label": "high"}]}],
        msg="$lookup let with $cond expression should evaluate true branch correctly",
    ),
    LookupTestCase(
        "let_expr_cond_false_branch",
        docs=[{"_id": 1, "val": 2}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": {"$cond": [{"$gt": ["$val", 5]}, "high", "low"]}},
                    "pipeline": [{"$addFields": {"label": "$$x"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "val": 2, "joined": [{"_id": 10, "label": "low"}]}],
        msg="$lookup let with $cond expression should evaluate false branch correctly",
    ),
    LookupTestCase(
        "let_expr_ifNull_with_null_field",
        docs=[{"_id": 1, "maybe": None}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": {"$ifNull": ["$maybe", "default"]}},
                    "pipeline": [{"$addFields": {"val": "$$x"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "maybe": None, "joined": [{"_id": 10, "val": "default"}]}],
        msg="$lookup let with $ifNull should use default when field is null",
    ),
    LookupTestCase(
        "let_expr_size",
        docs=[{"_id": 1, "arr": [1, 2, 3]}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": {"$size": "$arr"}},
                    "pipeline": [{"$addFields": {"count": "$$x"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "arr": [1, 2, 3], "joined": [{"_id": 10, "count": 3}]}],
        msg="$lookup let with $size expression should compute array length",
    ),
    LookupTestCase(
        "let_expr_toUpper",
        docs=[{"_id": 1, "name": "hello"}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": {"$toUpper": "$name"}},
                    "pipeline": [{"$addFields": {"upper": "$$x"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "name": "hello", "joined": [{"_id": 10, "upper": "HELLO"}]}],
        msg="$lookup let with $toUpper expression should transform string to uppercase",
    ),
    LookupTestCase(
        "let_expr_nested_arithmetic",
        docs=[{"_id": 1, "a": 3, "b": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": {"$add": [{"$multiply": ["$a", 2]}, "$b"]}},
                    "pipeline": [{"$addFields": {"val": "$$x"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "a": 3, "b": 1, "joined": [{"_id": 10, "val": 7}]}],
        msg="$lookup let with nested arithmetic expression should compute correctly",
    ),
    LookupTestCase(
        "let_expr_type_operator",
        docs=[{"_id": 1, "field": 42}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": {"$type": "$field"}},
                    "pipeline": [{"$addFields": {"typename": "$$x"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "field": 42, "joined": [{"_id": 10, "typename": "int"}]}],
        msg="$lookup let with $type expression should produce type name string",
    ),
    LookupTestCase(
        "let_expr_dateToString",
        docs=[{"_id": 1, "d": DATE_Y2K}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"x": {"$dateToString": {"format": "%Y", "date": "$d"}}},
                    "pipeline": [{"$addFields": {"year": "$$x"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "d": DATE_Y2K, "joined": [{"_id": 10, "year": "2000"}]}],
        msg="$lookup let with $dateToString expression should format date",
    ),
]

#               multiple expressions referencing same source field

LOOKUP_LET_MIXED_FORMS_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "let_mixed_constant_field_expression",
        docs=[{"_id": 1, "score": 85}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {
                        "threshold": 70,
                        "val": "$score",
                        "doubled": {"$multiply": ["$score", 2]},
                    },
                    "pipeline": [
                        {
                            "$addFields": {
                                "t": "$$threshold",
                                "v": "$$val",
                                "d": "$$doubled",
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "score": 85,
                "joined": [{"_id": 10, "t": 70, "v": 85, "d": 170}],
            }
        ],
        msg=(
            "$lookup let with constant, field ref, and expression should"
            " resolve all three independently"
        ),
    ),
    LookupTestCase(
        "let_mixed_system_var_and_field_ref",
        docs=[{"_id": 1, "specific": "value"}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"doc": "$$ROOT", "field_val": "$specific"},
                    "pipeline": [
                        {
                            "$addFields": {
                                "full_doc": "$$doc",
                                "single_field": "$$field_val",
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "specific": "value",
                "joined": [
                    {
                        "_id": 10,
                        "full_doc": {"_id": 1, "specific": "value"},
                        "single_field": "value",
                    }
                ],
            }
        ],
        msg=(
            "$lookup let with $$ROOT and field ref should resolve"
            " system variable and field path independently"
        ),
    ),
    LookupTestCase(
        "let_mixed_multiple_expressions_same_source",
        docs=[{"_id": 1, "x": 10}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {
                        "doubled": {"$multiply": ["$x", 2]},
                        "halved": {"$divide": ["$x", 2]},
                        "original": "$x",
                    },
                    "pipeline": [
                        {
                            "$addFields": {
                                "d": "$$doubled",
                                "h": "$$halved",
                                "o": "$$original",
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "x": 10,
                "joined": [{"_id": 10, "d": 20, "h": 5.0, "o": 10}],
            }
        ],
        msg=(
            "$lookup let with multiple expressions referencing same source"
            " field should evaluate each independently"
        ),
    ),
    LookupTestCase(
        "let_many_variables",
        docs=[{"_id": 1, "a": 1, "b": 2, "c": 3, "d": 4, "e": 5}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {
                        "v1": "$a",
                        "v2": "$b",
                        "v3": "$c",
                        "v4": "$d",
                        "v5": "$e",
                        "s1": {"$add": ["$a", "$b"]},
                        "s2": {"$multiply": ["$c", "$d"]},
                        "const": "static",
                    },
                    "pipeline": [
                        {
                            "$addFields": {
                                "r1": "$$v1",
                                "r2": "$$v2",
                                "r3": "$$v3",
                                "r4": "$$v4",
                                "r5": "$$v5",
                                "rs1": "$$s1",
                                "rs2": "$$s2",
                                "rc": "$$const",
                            }
                        }
                    ],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "a": 1,
                "b": 2,
                "c": 3,
                "d": 4,
                "e": 5,
                "joined": [
                    {
                        "_id": 10,
                        "r1": 1,
                        "r2": 2,
                        "r3": 3,
                        "r4": 4,
                        "r5": 5,
                        "rs1": 3,
                        "rs2": 12,
                        "rc": "static",
                    }
                ],
            }
        ],
        msg="$lookup let with many variables (8) should all be accessible in sub-pipeline",
    ),
    LookupTestCase(
        "let_variable_with_underscore_name",
        docs=[{"_id": 1, "x": "val"}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"my_var": "$x"},
                    "pipeline": [{"$addFields": {"result": "$$my_var"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "x": "val", "joined": [{"_id": 10, "result": "val"}]}],
        msg="$lookup let variable with underscore in name should be valid and accessible",
    ),
    LookupTestCase(
        "let_variable_name_is_prefix_of_another",
        docs=[{"_id": 1, "a": "first", "b": "second"}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"item": "$a", "itemId": "$b"},
                    "pipeline": [{"$addFields": {"r1": "$$item", "r2": "$$itemId"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "a": "first",
                "b": "second",
                "joined": [{"_id": 10, "r1": "first", "r2": "second"}],
            }
        ],
        msg=(
            "$lookup let with variable name that is prefix of another"
            " should resolve both without ambiguity"
        ),
    ),
]


LOOKUP_LET_ADDITIONAL_FORMS_TESTS: list[LookupTestCase] = [
    LookupTestCase(
        "literal_array_constant",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"carr": [1, 2, 3]},
                    "pipeline": [{"$project": {"_id": 0, "ra": "$$carr"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "joined": [{"ra": [1, 2, 3]}]}],
        msg="$lookup let should accept a literal array of constants as a value",
    ),
    LookupTestCase(
        "literal_object_via_dollar_literal",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"cobj": {"$literal": {"k": 1}}},
                    "pipeline": [{"$project": {"_id": 0, "robj": "$$cobj"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "joined": [{"robj": {"k": 1}}]}],
        msg="$lookup let should accept an object forced via $literal as a value",
    ),
    LookupTestCase(
        "expr_date_add_value",
        docs=[{"_id": 1, "dt": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {
                        "d": {
                            "$dateAdd": {
                                "startDate": "$dt",
                                "unit": "day",
                                "amount": 1,
                            }
                        }
                    },
                    "pipeline": [{"$project": {"_id": 0, "rd": "$$d"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[
            {
                "_id": 1,
                "dt": datetime(2020, 1, 1, tzinfo=timezone.utc),
                "joined": [{"rd": datetime(2020, 1, 2, tzinfo=timezone.utc)}],
            }
        ],
        msg=(
            "$lookup let should accept a $dateAdd expression value"
            " evaluated against the input document"
        ),
    ),
    LookupTestCase(
        "expr_map_value",
        docs=[{"_id": 1, "vals": [1, 2, 3]}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {
                        "arr": {
                            "$map": {
                                "input": "$vals",
                                "as": "e",
                                "in": {"$multiply": ["$$e", 2]},
                            }
                        }
                    },
                    "pipeline": [{"$project": {"_id": 0, "ra": "$$arr"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "vals": [1, 2, 3], "joined": [{"ra": [2, 4, 6]}]}],
        msg=(
            "$lookup let should accept a $map expression value"
            " evaluated against the input document"
        ),
    ),
    LookupTestCase(
        "mixed_form_missing_field_and_literal_no_cross_contamination",
        docs=[{"_id": 1}],
        foreign_docs=[{"_id": 10}],
        pipeline=[
            {
                "$lookup": {
                    "from": FOREIGN,
                    "let": {"c": 42, "m": "$absent"},
                    "pipeline": [{"$project": {"_id": 0, "rc": "$$c", "rm": "$$m"}}],
                    "as": "joined",
                }
            }
        ],
        expected=[{"_id": 1, "joined": [{"rc": 42}]}],
        msg=(
            "$lookup mixed-form let with a missing field and a literal"
            " should keep the literal and omit the missing field"
        ),
    ),
]


# --- Combine all tests ---
LOOKUP_CORRELATED_LET_FORMS_ALL: list[LookupTestCase] = (
    LOOKUP_LET_CONSTANT_LITERAL_TESTS
    + LOOKUP_LET_FIELD_REFERENCE_TESTS
    + LOOKUP_LET_EXPRESSION_TESTS
    + LOOKUP_LET_MIXED_FORMS_TESTS
    + LOOKUP_LET_ADDITIONAL_FORMS_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LOOKUP_CORRELATED_LET_FORMS_ALL))
def test_lookup_correlated_let_forms(collection, test_case: LookupTestCase):
    """Test $lookup correlated subquery let variable forms and type preservation."""
    with setup_lookup(collection, test_case) as foreign_name:
        command = build_lookup_command(collection, test_case, foreign_name)
        result = execute_command(collection, command)
        assertResult(
            result,
            expected=test_case.expected,
            error_code=test_case.error_code,
            msg=test_case.msg,
        )
