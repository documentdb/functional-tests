"""Tests for collMod behaviors unique to clustered collections."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.error_codes import (
    INDEX_NOT_FOUND_ERROR,
)
from documentdb_tests.framework.executor import execute_command

from .utils.clustered_utils import create_clustered


# Property [Add expireAfterSeconds]: clustered collections support collection-level
# TTL via collMod expireAfterSeconds.
@pytest.mark.collection_mgmt
def test_collmod_add_expire_after_seconds(collection):
    """Test adding expireAfterSeconds via collMod."""
    name = create_clustered(collection)
    result = execute_command(collection, {"collMod": name, "expireAfterSeconds": 3600})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="should add expireAfterSeconds to clustered collection"
    )


# Property [Modify expireAfterSeconds]: an existing expireAfterSeconds value can
# be changed via collMod.
@pytest.mark.collection_mgmt
def test_collmod_modify_expire_after_seconds(collection):
    """Test modifying expireAfterSeconds via collMod."""
    name = create_clustered(collection)
    execute_command(collection, {"collMod": name, "expireAfterSeconds": 3600})
    result = execute_command(collection, {"collMod": name, "expireAfterSeconds": 7200})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="should modify expireAfterSeconds on clustered collection"
    )


# Property [Remove expireAfterSeconds]: setting expireAfterSeconds to 'off'
# removes the TTL configuration.
@pytest.mark.collection_mgmt
def test_collmod_remove_expire_after_seconds(collection):
    """Test removing expireAfterSeconds via collMod with 'off'."""
    name = create_clustered(collection)
    execute_command(collection, {"collMod": name, "expireAfterSeconds": 3600})
    result = execute_command(collection, {"collMod": name, "expireAfterSeconds": "off"})
    assertSuccessPartial(result, {"ok": 1.0}, msg="should remove expireAfterSeconds with 'off'")


# Property [Remove expireAfterSeconds No-Op]: setting 'off' when no TTL exists
# is a no-op success.
@pytest.mark.collection_mgmt
def test_collmod_remove_expire_noop(collection):
    """Test removing expireAfterSeconds when none exists is no-op."""
    name = create_clustered(collection)
    result = execute_command(collection, {"collMod": name, "expireAfterSeconds": "off"})
    assertSuccessPartial(result, {"ok": 1.0}, msg="should succeed as no-op when no TTL exists")


# Property [collMod Index Option Cannot Find Clustered]: using collMod with
# index keyPattern {_id:1} cannot find the clustered index.
@pytest.mark.collection_mgmt
def test_collmod_index_option_cannot_find_clustered(collection):
    """Test collMod index option cannot target clustered index."""
    name = create_clustered(collection)
    result = execute_command(
        collection,
        {"collMod": name, "index": {"keyPattern": {"_id": 1}, "expireAfterSeconds": 3600}},
    )
    assertResult(
        result,
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="should not find clustered index via collMod index option",
    )


# Property [Secondary TTL Coexists With Clustered TTL]: a secondary TTL index
# can coexist with a collection-level expireAfterSeconds on a clustered
# collection.
@pytest.mark.collection_mgmt
def test_collmod_secondary_ttl_coexists(collection):
    """Test secondary TTL index coexists with clustered TTL."""
    name = create_clustered(collection)
    db = collection.database
    db[name].create_index([("created_at", 1)], expireAfterSeconds=86400)
    result = execute_command(collection, {"collMod": name, "expireAfterSeconds": 3600})
    assertSuccessPartial(
        result, {"ok": 1.0}, msg="should allow collection-level TTL alongside secondary TTL index"
    )
