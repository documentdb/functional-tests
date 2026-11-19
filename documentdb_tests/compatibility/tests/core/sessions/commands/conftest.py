"""Shared fixtures for session and transaction command tests."""

import pytest


@pytest.fixture(autouse=True)
def create_collection_up_front(request):
    """Create the test's ``collection`` before the test body runs.

    The root ``collection`` fixture does not create the collection, so a test's
    first write inside a transaction would also create it implicitly. Creating
    it here keeps these tests independent of implicit collection creation in a
    transaction, which is tested on its own in
    test_commitTransaction_supported_operations.py.
    """
    if "collection" in request.fixturenames:
        coll = request.getfixturevalue("collection")
        coll.database.create_collection(coll.name)
