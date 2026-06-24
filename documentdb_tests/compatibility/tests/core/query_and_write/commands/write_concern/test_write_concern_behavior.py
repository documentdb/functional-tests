"""
writeConcern behavioral tests.

Tests w:0 unacknowledged behavior, j:true overriding w:0, findAndModify return
semantics, and ordered/unordered interaction with writeConcern.
"""

from documentdb_tests.framework.assertions import assertNotError, assertResult, assertSuccessPartial
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command

# Property [w:0 Unacknowledged]: w:0 does not error and still performs the write.


def test_update_w0_does_not_error(collection):
    """Test update with w:0 does not produce an error."""
    collection.insert_one({"_id": 1, "a": 0})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 99}}}],
            "writeConcern": {"w": 0},
        },
    )
    assertNotError(result, msg="update with w:0 should not error.")


def test_update_w0_performs_write(collection):
    """Test update with w:0 still performs the write."""
    collection.insert_one({"_id": 1, "a": 0})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 99}}}],
            "writeConcern": {"w": 0},
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertResult(
        result,
        expected=[{"_id": 1, "a": 99}],
        msg="update with w:0 should still perform the write.",
    )


def test_delete_w0_does_not_error(collection):
    """Test delete with w:0 does not produce an error."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [{"q": {"_id": 1}, "limit": 1}],
            "writeConcern": {"w": 0},
        },
    )
    assertNotError(result, msg="delete with w:0 should not error.")


def test_delete_w0_performs_delete(collection):
    """Test delete with w:0 still performs the delete."""
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [{"q": {"_id": 1}, "limit": 1}],
            "writeConcern": {"w": 0},
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertResult(result, expected=[], msg="delete with w:0 should still perform the delete.")


def test_findAndModify_w0_does_not_error(collection):
    """Test findAndModify with w:0 does not produce an error."""
    collection.insert_one({"_id": 1, "a": 0})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$set": {"a": 99}},
            "writeConcern": {"w": 0},
        },
    )
    assertNotError(result, msg="findAndModify with w:0 should not error.")


# Property [j:true Overrides w:0]: j:true with w:0 produces an acknowledged response.


def test_update_j_true_overrides_w0(collection):
    """Test j:true overrides w:0 to produce acknowledgment on update."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "writeConcern": {"w": 0, "j": True},
        },
    )
    assertNotError(result, msg="update with j:true should override w:0.")


def test_delete_j_true_overrides_w0(collection):
    """Test j:true overrides w:0 to produce acknowledgment on delete."""
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [{"q": {"_id": 99}, "limit": 1}],
            "writeConcern": {"w": 0, "j": True},
        },
    )
    assertNotError(result, msg="delete with j:true should override w:0.")


def test_findAndModify_j_true_overrides_w0(collection):
    """Test j:true overrides w:0 to produce acknowledgment on findAndModify."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$set": {"a": 1}},
            "writeConcern": {"w": 0, "j": True},
        },
    )
    assertNotError(result, msg="findAndModify with j:true should override w:0.")


# Property [findAndModify Return Independence]: writeConcern does not affect return value.


def test_findAndModify_new_true_with_write_concern(collection):
    """Test findAndModify new:true returns modified doc regardless of writeConcern."""
    collection.insert_one({"_id": 1, "a": 0})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$set": {"a": 99}},
            "new": True,
            "writeConcern": {"w": 1},
        },
    )
    assertSuccessPartial(
        result,
        {"value": {"_id": 1, "a": 99}},
        msg="findAndModify new:true should return modified doc.",
    )


def test_findAndModify_new_false_with_write_concern(collection):
    """Test findAndModify new:false returns original doc regardless of writeConcern."""
    collection.insert_one({"_id": 1, "a": 0})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$set": {"a": 99}},
            "new": False,
            "writeConcern": {"w": 1},
        },
    )
    assertSuccessPartial(
        result,
        {"value": {"_id": 1, "a": 0}},
        msg="findAndModify new:false should return original doc.",
    )


def test_findAndModify_remove_with_write_concern(collection):
    """Test findAndModify remove:true returns removed doc regardless of writeConcern."""
    collection.insert_one({"_id": 1, "a": 0})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "remove": True,
            "writeConcern": {"w": 1},
        },
    )
    assertSuccessPartial(
        result,
        {"value": {"_id": 1, "a": 0}},
        msg="findAndModify remove:true should return removed doc.",
    )


# Property [Ordered Independence]: writeConcern works identically with ordered:true/false.


def test_update_write_concern_with_ordered_true(collection):
    """Test update writeConcern works with ordered:true."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "ordered": True,
            "writeConcern": {"w": 1},
        },
    )
    assertNotError(result, msg="update with ordered:true and writeConcern should succeed.")


def test_update_write_concern_with_ordered_false(collection):
    """Test update writeConcern works with ordered:false."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
            "ordered": False,
            "writeConcern": {"w": 1},
        },
    )
    assertNotError(result, msg="update with ordered:false and writeConcern should succeed.")


# Property [w:0 Error Suppression]: w:0 suppresses writeErrors that w:1 surfaces.


def test_update_w0_suppresses_write_errors(collection):
    """Test w:0 suppresses writeErrors for an invalid operation."""
    collection.insert_one({"_id": 1, "a": 1})
    # multi:true with replacement doc is invalid, produces error with w:1.
    result_w0 = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"a": 2}, "multi": True}],
            "writeConcern": {"w": 0},
        },
    )
    # w:0 should not surface the writeErrors.
    assertNotError(result_w0, msg="update with w:0 should suppress writeErrors.")


def test_update_w1_surfaces_write_errors(collection):
    """Test w:1 surfaces writeErrors for the same invalid operation."""
    collection.insert_one({"_id": 1, "a": 1})
    result_w1 = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"a": 2}, "multi": True}],
            "writeConcern": {"w": 1},
        },
    )
    # w:1 should return writeErrors.
    assertResult(
        result_w1,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="update with w:1 should surface writeErrors.",
    )
