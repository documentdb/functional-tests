"""Tests for createIndexes index type options.

Validates text index creation/weights, hashed index behavior,
geospatial (2dsphere, 2d) indexes, and wildcard index options including
wildcardProjection.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

TEXT_INDEX_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="text_basic",
        indexes=({"key": {"a": "text"}, "name": "a_text"},),
        msg="Basic text index succeeds",
    ),
    IndexTestCase(
        id="text_multiple_fields",
        indexes=({"key": {"a": "text", "b": "text"}, "name": "a_b_text"},),
        msg="Multi-field text index succeeds",
    ),
    IndexTestCase(
        id="text_wildcard",
        indexes=({"key": {"$**": "text"}, "name": "wildcard_text"},),
        msg="Wildcard text index succeeds",
    ),
    IndexTestCase(
        id="text_with_valid_weights",
        indexes=(
            {
                "key": {"a": "text", "b": "text"},
                "name": "ab_text_weights",
                "weights": {"a": 5, "b": 10},
            },
        ),
        msg="Text with weights succeeds",
    ),
    IndexTestCase(
        id="text_default_language_english",
        indexes=({"key": {"a": "text"}, "name": "a_text_en", "default_language": "english"},),
        msg="default_language english succeeds",
    ),
    IndexTestCase(
        id="text_default_language_none",
        indexes=({"key": {"a": "text"}, "name": "a_text_none", "default_language": "none"},),
        msg="default_language none succeeds",
    ),
]

HASHED_INDEX_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="hashed_basic",
        indexes=({"key": {"a": "hashed"}, "name": "a_hashed"},),
        msg="Basic hashed index succeeds",
    ),
    IndexTestCase(
        id="hashed_nested_field",
        indexes=({"key": {"a.b": "hashed"}, "name": "ab_hashed"},),
        msg="Hashed on nested field succeeds",
    ),
    IndexTestCase(
        id="compound_with_one_hashed",
        indexes=({"key": {"a": 1, "b": "hashed"}, "name": "a_1_b_hashed"},),
        msg="Compound with one hashed succeeds",
    ),
]

GEOSPATIAL_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="2dsphere_basic",
        indexes=({"key": {"loc": "2dsphere"}, "name": "loc_2dsphere"},),
        msg="2dsphere index succeeds",
    ),
    IndexTestCase(
        id="2dsphere_compound",
        indexes=({"key": {"loc": "2dsphere", "a": 1}, "name": "loc_2ds_a_1"},),
        msg="2dsphere compound succeeds",
    ),
    IndexTestCase(
        id="2d_basic",
        indexes=({"key": {"loc": "2d"}, "name": "loc_2d"},),
        msg="2d index succeeds",
    ),
    IndexTestCase(
        id="2d_with_bits",
        indexes=({"key": {"loc": "2d"}, "name": "loc_2d_bits", "bits": 26},),
        msg="2d with bits=26 succeeds",
    ),
    IndexTestCase(
        id="2d_with_min_max",
        indexes=({"key": {"loc": "2d"}, "name": "loc_2d_bounds", "min": -200, "max": 200},),
        msg="2d with min/max bounds succeeds",
    ),
]

WILDCARD_VALID_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="wildcard_basic",
        indexes=({"key": {"$**": 1}, "name": "wc_1"},),
        msg="Basic wildcard succeeds",
    ),
    IndexTestCase(
        id="wildcard_subpath",
        indexes=({"key": {"a.$**": 1}, "name": "a_wc_1"},),
        msg="Subpath wildcard succeeds",
    ),
    IndexTestCase(
        id="wildcard_with_partial_filter",
        indexes=(
            {
                "key": {"$**": 1},
                "name": "wc_partial",
                "partialFilterExpression": {"a": {"$exists": True}},
            },
        ),
        msg="Wildcard with partial filter succeeds",
    ),
    IndexTestCase(
        id="wildcard_with_collation",
        indexes=({"key": {"$**": 1}, "name": "wc_collation", "collation": {"locale": "en"}},),
        msg="Wildcard with collation succeeds",
    ),
    IndexTestCase(
        id="wildcard_inclusion_projection",
        indexes=(
            {
                "key": {"$**": 1},
                "name": "wc_incl",
                "wildcardProjection": {"a": 1, "b": 1},
            },
        ),
        msg="Inclusion wildcardProjection succeeds",
    ),
    IndexTestCase(
        id="wildcard_exclusion_projection",
        indexes=(
            {
                "key": {"$**": 1},
                "name": "wc_excl",
                "wildcardProjection": {"a": 0, "b": 0},
            },
        ),
        msg="Exclusion wildcardProjection succeeds",
    ),
    IndexTestCase(
        id="wildcard_id_in_exclusion",
        indexes=(
            {
                "key": {"$**": 1},
                "name": "wc_id_excl",
                "wildcardProjection": {"_id": 1, "a": 0},
            },
        ),
        msg="_id in exclusion projection succeeds",
    ),
    IndexTestCase(
        id="wildcard_direction_negative",
        indexes=({"key": {"$**": -1}, "name": "wc_neg1"},),
        msg="Wildcard direction -1 succeeds",
    ),
]

ALL_TESTS = TEXT_INDEX_TESTS + HASHED_INDEX_TESTS + GEOSPATIAL_TESTS + WILDCARD_VALID_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_createIndexes_index_types(collection, test):
    """Test createIndexes index type options."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": list(test.indexes),
        },
    )
    assertSuccessPartial(result, index_created_response(), test.msg)


def test_createIndexes_text_same_key_same_name_noop(collection):
    """Test creating same text index again is a noop."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": "text"}, "name": "a_text"}],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": "text"}, "name": "a_text"}],
        },
    )
    assertSuccessPartial(
        result,
        index_created_response(num_indexes_before=2, num_indexes_after=2),
        "Same text index again is no-op",
    )
