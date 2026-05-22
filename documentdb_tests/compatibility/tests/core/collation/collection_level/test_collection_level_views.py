"""Tests for collation constraints on views and cross-view stage behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collation.utils.collation_view_mismatch import (
    SECONDARY,
    ViewMismatchTestCase,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import OPTION_NOT_SUPPORTED_ON_VIEW_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CollectionWithView,
    ViewCollection,
    ViewOnCustomCollection,
)

# Property [View Collation Constraints]: aggregating on a view with an explicit
# collation that differs from the view's default produces
# OPTION_NOT_SUPPORTED_ON_VIEW_ERROR; omitting collation uses the view's
# default; a view created without collation defaults to simple comparison.
COLLATION_VIEW_CONSTRAINT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_no_explicit_uses_default",
        target_collection=ViewCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        msg="aggregate on view with no explicit collation should use view default",
    ),
    CommandTestCase(
        "view_matching_collation_succeeds",
        target_collection=ViewCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        msg="aggregate on view with matching collation should succeed",
    ),
    CommandTestCase(
        "view_different_locale_rejected",
        target_collection=ViewCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}],
            "cursor": {},
            "collation": {"locale": "fr", "strength": 2},
        },
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="aggregate on view with different locale should be rejected",
    ),
    CommandTestCase(
        "view_same_locale_different_strength_rejected",
        target_collection=ViewCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="aggregate on view with same locale but different strength should be rejected",
    ),
    CommandTestCase(
        "view_no_collation_defaults_to_simple",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="view without collation should default to simple binary comparison",
    ),
    CommandTestCase(
        "view_no_collation_does_not_inherit_source",
        target_collection=ViewOnCustomCollection(
            source_options={"collation": {"locale": "en", "strength": 1}}
        ),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="view without collation should not inherit source collection's collation",
    ),
    CommandTestCase(
        "view_no_collation_explicit_simple_succeeds",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}],
            "cursor": {},
            "collation": {"locale": "simple"},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="aggregate on view without collation with explicit simple should succeed",
    ),
    CommandTestCase(
        "view_no_collation_explicit_nonsimple_rejected",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"x": "apple"}}],
            "cursor": {},
            "collation": {"locale": "en", "strength": 2},
        },
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="aggregate on view without collation with non-simple collation should be rejected",
    ),
    CommandTestCase(
        "view_collation_does_not_affect_source",
        target_collection=CollectionWithView(
            view_options={"collation": {"locale": "en", "strength": 1}}
        ),
        docs=[{"_id": 1, "name": "cafe"}, {"_id": 2, "name": "Cafe"}, {"_id": 3, "name": "CAFE"}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$match": {"name": "cafe"}}],
            "cursor": {},
        },
        expected=[{"_id": 1, "name": "cafe"}],
        msg="querying source collection should use binary comparison, unaffected by view collation",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_VIEW_CONSTRAINT_TESTS))
def test_collation_aggregate_views(database_client, collection, test):
    """Test collation constraints when aggregating on views."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )


# Property [GraphLookup View Collation Mismatch]: $graphLookup from a
# collection or view to a view with mismatched collation produces
# OPTION_NOT_SUPPORTED_ON_VIEW_ERROR, while matching collation succeeds.
COLLATION_GRAPHLOOKUP_VIEW_TESTS: list[ViewMismatchTestCase] = [
    ViewMismatchTestCase(
        "graphlookup_collection_to_view_mismatched",
        docs=[{"_id": 1, "start": "a"}],
        secondary_docs=[
            {"_id": 1, "val": "a", "next": "b"},
            {"_id": 2, "val": "b", "next": "c"},
        ],
        pipeline=[
            {
                "$graphLookup": {
                    "from": SECONDARY,
                    "startWith": "$start",
                    "connectFromField": "next",
                    "connectToField": "val",
                    "as": "connected",
                }
            },
        ],
        secondary_view_collation={"locale": "fr", "strength": 2},
        command_collation={"locale": "en", "strength": 1},
        ignore_order_in=["connected"],
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$graphLookup from collection to view with mismatched collation should error",
    ),
    ViewMismatchTestCase(
        "graphlookup_view_to_view_different_collation",
        docs=[{"_id": 1, "start": "a"}],
        secondary_docs=[
            {"_id": 1, "val": "a", "next": "b"},
            {"_id": 2, "val": "b", "next": "c"},
        ],
        pipeline=[
            {
                "$graphLookup": {
                    "from": SECONDARY,
                    "startWith": "$start",
                    "connectFromField": "next",
                    "connectToField": "val",
                    "as": "connected",
                }
            },
        ],
        secondary_view_collation={"locale": "fr", "strength": 2},
        source_view_collation={"locale": "en", "strength": 1},
        ignore_order_in=["connected"],
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$graphLookup from view to view with different collation should error",
    ),
    ViewMismatchTestCase(
        "graphlookup_collection_to_view_matching",
        docs=[{"_id": 1, "start": "a"}],
        secondary_docs=[
            {"_id": 1, "val": "a", "next": "b"},
            {"_id": 2, "val": "b", "next": "c"},
        ],
        pipeline=[
            {
                "$graphLookup": {
                    "from": SECONDARY,
                    "startWith": "$start",
                    "connectFromField": "next",
                    "connectToField": "val",
                    "as": "connected",
                }
            },
        ],
        secondary_view_collation={"locale": "en", "strength": 1},
        command_collation={"locale": "en", "strength": 1},
        ignore_order_in=["connected"],
        expected=[
            {
                "_id": 1,
                "start": "a",
                "connected": [
                    {"_id": 2, "val": "b", "next": "c"},
                    {"_id": 1, "val": "a", "next": "b"},
                ],
            }
        ],
        msg="$graphLookup from collection to view with matching collation should succeed",
    ),
]

# Property [UnionWith View Collation Mismatch]: $unionWith from a collection to
# a view with mismatched or absent collation produces
# OPTION_NOT_SUPPORTED_ON_VIEW_ERROR, while matching collation or unionWith from
# a view to a base collection succeeds.
COLLATION_UNIONWITH_TESTS: list[ViewMismatchTestCase] = [
    ViewMismatchTestCase(
        "unionwith_collection_to_view_mismatched",
        docs=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": "world"}],
        secondary_docs=[{"_id": 3, "x": "foo"}, {"_id": 4, "x": "bar"}],
        pipeline=[{"$unionWith": SECONDARY}],
        secondary_view_collation={"locale": "fr", "strength": 2},
        command_collation={"locale": "en", "strength": 1},
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$unionWith from collection to view with mismatched collation should error",
    ),
    ViewMismatchTestCase(
        "unionwith_subpipeline_to_view_mismatched",
        docs=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": "world"}],
        secondary_docs=[{"_id": 3, "x": "foo"}, {"_id": 4, "x": "bar"}],
        pipeline=[{"$unionWith": {"coll": SECONDARY, "pipeline": []}}],
        secondary_view_collation={"locale": "fr", "strength": 2},
        command_collation={"locale": "en", "strength": 1},
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$unionWith sub-pipeline form to view with mismatched collation should error",
    ),
    ViewMismatchTestCase(
        "unionwith_collection_to_view_matching",
        docs=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": "world"}],
        secondary_docs=[{"_id": 3, "x": "foo"}, {"_id": 4, "x": "bar"}],
        pipeline=[{"$unionWith": SECONDARY}],
        secondary_view_collation={"locale": "en", "strength": 1},
        command_collation={"locale": "en", "strength": 1},
        expected=[
            {"_id": 1, "x": "hello"},
            {"_id": 2, "x": "world"},
            {"_id": 3, "x": "foo"},
            {"_id": 4, "x": "bar"},
        ],
        msg="$unionWith from collection to view with matching collation should succeed",
    ),
    ViewMismatchTestCase(
        "unionwith_no_collation_to_view",
        docs=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": "world"}],
        secondary_docs=[{"_id": 3, "x": "foo"}, {"_id": 4, "x": "bar"}],
        pipeline=[{"$unionWith": SECONDARY}],
        secondary_view_collation={"locale": "fr", "strength": 2},
        error_code=OPTION_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="$unionWith with no explicit collation to view should error",
    ),
    ViewMismatchTestCase(
        "unionwith_view_to_base_collection",
        docs=[{"_id": 1, "x": "hello"}, {"_id": 2, "x": "world"}],
        secondary_docs=[{"_id": 3, "x": "foo"}, {"_id": 4, "x": "bar"}],
        pipeline=[{"$unionWith": SECONDARY}],
        source_view_collation={"locale": "en", "strength": 1},
        expected=[
            {"_id": 1, "x": "hello"},
            {"_id": 2, "x": "world"},
            {"_id": 3, "x": "foo"},
            {"_id": 4, "x": "bar"},
        ],
        msg="$unionWith from view to base collection should succeed",
    ),
]

COLLATION_VIEW_MISMATCH_TESTS: list[ViewMismatchTestCase] = (
    COLLATION_GRAPHLOOKUP_VIEW_TESTS + COLLATION_UNIONWITH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(COLLATION_VIEW_MISMATCH_TESTS))
def test_collation_aggregate_views_mismatch(database_client, collection, test_case):
    """Test collation view-mismatch behavior across stages."""
    collection = test_case.prepare(database_client, collection)
    result = execute_command(collection, test_case.build_command(collection))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_order_in=test_case.ignore_order_in,
    )
