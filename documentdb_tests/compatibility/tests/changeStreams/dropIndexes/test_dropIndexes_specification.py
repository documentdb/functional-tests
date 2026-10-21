"""Verify dropIndexes events preserve each public index representation.

Storage-engine-specific index options are not applicable to compatibility
coverage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.changeStreams.dropIndexes.utils.drop_indexes import (
    drop_index_events,
    index_specification,
)
from documentdb_tests.compatibility.tests.changeStreams.utils.change_stream import (
    collect_until_marker,
    open_change_stream,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Len
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = [
    pytest.mark.requires(change_streams=True),
    pytest.mark.aggregate,
    pytest.mark.index,
]


@dataclass(frozen=True)
class DropIndexSpecificationTestCase(BaseTestCase):
    """An index whose complete definition must appear in its drop event."""

    index_name: str = ""
    key: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)
    document: dict[str, Any] = field(default_factory=dict)


# Property [Index specification]: Preserve the complete definition of each tested index type.
DROP_INDEX_SPECIFICATION_CASES: list[DropIndexSpecificationTestCase] = [
    DropIndexSpecificationTestCase(
        id="single_field",
        index_name="a_1",
        key={"a": 1},
        document={"_id": 1, "a": 1},
        msg="dropIndexes should preserve a plain single-field index specification",
    ),
    DropIndexSpecificationTestCase(
        id="hashed",
        index_name="account_hashed",
        key={"account": "hashed"},
        document={"_id": 1, "account": "A"},
        msg="dropIndexes should preserve a hashed index specification",
    ),
    DropIndexSpecificationTestCase(
        id="2d",
        index_name="location_2d",
        key={"location": "2d"},
        document={"_id": 1, "location": [40, 5]},
        msg="dropIndexes should preserve a 2d index specification",
    ),
    DropIndexSpecificationTestCase(
        id="hidden",
        index_name="hidden_a_1",
        key={"a": 1},
        options={"hidden": True},
        document={"_id": 1, "a": 1},
        msg="dropIndexes should preserve a hidden index specification",
    ),
    DropIndexSpecificationTestCase(
        id="ttl",
        index_name="expires_1",
        key={"expires": 1},
        options={"expireAfterSeconds": 3600},
        document={"_id": 1, "expires": datetime.now(timezone.utc)},
        msg="dropIndexes should preserve the TTL index specification",
    ),
    DropIndexSpecificationTestCase(
        id="ttl_zero",
        index_name="expires_immediately_1",
        key={"expiresImmediately": 1},
        options={"expireAfterSeconds": 0},
        document={
            "_id": 1,
            "expiresImmediately": datetime(2100, 1, 1, tzinfo=timezone.utc),
        },
        msg="dropIndexes should preserve a zero-second TTL index specification",
    ),
    DropIndexSpecificationTestCase(
        id="partial_filter",
        index_name="status_1",
        key={"status": 1},
        options={"partialFilterExpression": {"status": {"$eq": "ACTIVE"}}},
        document={"_id": 1, "status": "ACTIVE"},
        msg="dropIndexes should preserve the partial-filter index specification",
    ),
    DropIndexSpecificationTestCase(
        id="collation",
        index_name="name_1",
        key={"name": 1},
        options={"collation": {"locale": "en", "strength": 2}},
        document={"_id": 1, "name": "Book"},
        msg="dropIndexes should preserve the collation index specification",
    ),
    DropIndexSpecificationTestCase(
        id="text",
        index_name="description_text",
        key={"description": "text"},
        document={"_id": 1, "description": "database systems"},
        msg="dropIndexes should preserve the text index specification",
    ),
    DropIndexSpecificationTestCase(
        id="custom_text_weights",
        index_name="content_text",
        key={"title": "text", "body": "text"},
        options={"weights": {"title": 10, "body": 2}},
        document={"_id": 1, "title": "database", "body": "systems"},
        msg="dropIndexes should preserve custom text index weights",
    ),
    DropIndexSpecificationTestCase(
        id="2dsphere",
        index_name="location_2dsphere",
        key={"location": "2dsphere"},
        document={
            "_id": 1,
            "location": {"type": "Point", "coordinates": [1.0, 2.0]},
        },
        msg="dropIndexes should preserve the 2dsphere index specification",
    ),
    DropIndexSpecificationTestCase(
        id="compound_2dsphere",
        index_name="category_location",
        key={"category": 1, "location": "2dsphere"},
        document={
            "_id": 1,
            "category": "book",
            "location": {"type": "Point", "coordinates": [1.0, 2.0]},
        },
        msg="dropIndexes should preserve a compound 2dsphere index specification",
    ),
    DropIndexSpecificationTestCase(
        id="wildcard",
        index_name="all_fields",
        key={"$**": 1},
        document={"_id": 1, "nested": {"value": 1}},
        msg="dropIndexes should preserve the wildcard index specification",
    ),
    DropIndexSpecificationTestCase(
        id="wildcard_projection",
        index_name="projected_fields",
        key={"$**": 1},
        options={"wildcardProjection": {"included": 1}},
        document={"_id": 1, "included": 1, "excluded": 2},
        msg="dropIndexes should preserve a wildcard projection",
    ),
]


@pytest.mark.parametrize(
    "test",
    pytest_params(DROP_INDEX_SPECIFICATION_CASES),
)
def test_dropIndexes_event_preserves_specification(collection, test):
    """Compare the dropped index definition with listIndexes before deletion."""
    collection.insert_one(test.document)
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {
                    "key": test.key,
                    "name": test.index_name,
                    **test.options,
                }
            ],
        },
    )
    expected_specification = index_specification(collection, test.index_name)

    with open_change_stream(collection, scope="database") as stream:
        drop_result = execute_command(
            collection,
            {
                "dropIndexes": collection.name,
                "index": test.index_name,
            },
        )
        events = collect_until_marker(stream, collection)

    matching_events = drop_index_events(
        events,
        collection.database.name,
        collection.name,
    )
    observed = {
        "dropSucceeded": (not isinstance(drop_result, Exception) and drop_result.get("ok") == 1),
        "dropEvents": matching_events,
    }
    expected = {
        "dropSucceeded": Eq(True),
        "dropEvents": Len(1),
        "dropEvents.0.operationDescription.indexes.0": Eq(expected_specification),
    }
    assertProperties(
        observed,
        expected,
        msg=test.msg,
        raw_res=True,
    )
