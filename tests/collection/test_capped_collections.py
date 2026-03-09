"""
Tests for capped collection operations.

NOTE: This test was added by design to demonstrate how the Result Analyzer
automatically detects and categorizes unsupported features (error code 115).
When run against DocumentDB, this test will fail with error code 115, which
the analyzer will correctly categorize as UNSUPPORTED rather than FAIL.
"""

import pytest
from pymongo.errors import OperationFailure


@pytest.mark.collection_mgmt
def test_create_capped_collection(database_client):
    """
    Test creating a capped collection.
    
    Capped collections are fixed-size collections that maintain insertion order.
    This feature is not supported in DocumentDB and should return error code 115.
    
    Expected behavior:
    - Creates a capped collection successfully
    """
    collection_name = "capped_test_collection"
    
    try:
        # Attempt to create capped collection
        database_client.create_collection(
            collection_name,
            capped=True,
            size=100000
        )
        
        # Verify it's actually capped
        collection_info = database_client[collection_name].options()
        assert collection_info.get("capped") is True, "Collection should be capped"
        
        # Cleanup
        database_client.drop_collection(collection_name)
        
    except OperationFailure as e:
        raise
