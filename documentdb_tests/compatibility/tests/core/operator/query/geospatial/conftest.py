import pytest


@pytest.fixture
def geo_2dsphere(collection):
    """Create a 2dsphere index on loc."""
    collection.create_index([("loc", "2dsphere")])


@pytest.fixture
def geo_2d(collection):
    """Create a 2d index on loc."""
    collection.create_index([("loc", "2d")])
