"""
Global pytest fixtures for functional testing framework.

This module provides fixtures for:
- Engine parametrization
- Database connection management
- Test isolation
"""


import hashlib
import pytest
from pymongo import MongoClient


def pytest_addoption(parser):
    """Add custom command-line options for pytest."""
    parser.addoption(
        "--connection-string",
        action="store",
        default=None,
        help="Database connection string. "
        "Example: --connection-string mongodb://localhost:27017",
    )
    parser.addoption(
        "--engine-name",
        action="store",
        default="default",
        help="Optional engine identifier for metadata. "
        "Example: --engine-name documentdb",
    )


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Get connection string and engine name
    connection_string = config.getoption("--connection-string")
    engine_name = config.getoption("--engine-name")

    # Store in config for access by fixtures
    config.connection_string = connection_string
    config.engine_name = engine_name

    # If no connection string specified, default to localhost
    if not connection_string:
        config.connection_string = "mongodb://localhost:27017"


@pytest.fixture(scope="session")
def engine_client(request):
    """
    Create a MongoDB client for the configured engine.
    
    Session-scoped for performance - MongoClient is thread-safe and maintains
    an internal connection pool. This significantly improves test execution speed
    by eliminating redundant connection overhead.
    
    Per-test isolation is maintained through database_client and collection fixtures
    which create unique databases/collections for each test.

    Args:
        request: pytest request object

    Yields:
        MongoClient: Connected MongoDB client (shared across session)
        
    Raises:
        ConnectionError: If unable to connect to the database
    """
    connection_string = request.config.connection_string
    engine_name = request.config.engine_name

    client = MongoClient(connection_string)

    # Verify connection
    try:
        client.admin.command("ping")
    except Exception as e:
        # Close the client before raising
        client.close()
        # Raise ConnectionError so analyzer categorizes as INFRA_ERROR
        raise ConnectionError(
            f"Cannot connect to {engine_name} at {connection_string}: {e}"
        ) from e

    yield client

    # Cleanup: close connection
    client.close()


@pytest.fixture(scope="function")
def database_client(engine_client, request, worker_id):
    """
    Provide a database client with automatic cleanup.

    Creates a test database with a collision-free name for parallel execution.
    The name includes worker ID, hash, and abbreviated test name.
    Automatically drops the database after the test completes.

    Args:
        engine_client: MongoDB client from engine_client fixture
        request: pytest request object
        worker_id: Worker ID from pytest-xdist (e.g., 'gw0', 'gw1', or 'master')

    Yields:
        Database: MongoDB database object
    """
    # Get full test identifier (includes file path and test name)
    full_test_id = request.node.nodeid
    
    # Create a short hash for uniqueness (first 8 chars of SHA256)
    name_hash = hashlib.sha256(full_test_id.encode()).hexdigest()[:8]
    
    # Get abbreviated test name for readability (sanitize and truncate)
    test_name = request.node.name.replace("[", "_").replace("]", "_")
    abbreviated = test_name[:20]
    
    # Combine: test_{worker}_{hash}_{abbreviated}
    # Example: test_gw0_a1b2c3d4_find_all_documents
    db_name = f"test_{worker_id}_{name_hash}_{abbreviated}"[:63]  # MongoDB limit

    db = engine_client[db_name]

    yield db

    # Cleanup: drop test database
    try:
        engine_client.drop_database(db_name)
    except Exception:
        pass  # Best effort cleanup


@pytest.fixture(scope="function")
def collection(database_client, request, worker_id):
    """
    Provide an empty collection with automatic cleanup.

    Creates a collection with a collision-free name for parallel execution.
    Tests should directly insert any required test data.

    Args:
        database_client: Database from database_client fixture
        request: pytest request object
        worker_id: Worker ID from pytest-xdist (e.g., 'gw0', 'gw1', or 'master')

    Yields:
        Collection: Empty MongoDB collection object
    """
    # Get full test identifier
    full_test_id = request.node.nodeid
    
    # Create a short hash for uniqueness (first 8 chars of SHA256)
    name_hash = hashlib.sha256(full_test_id.encode()).hexdigest()[:8]
    
    # Get abbreviated test name for readability (sanitize and truncate)
    test_name = request.node.name.replace("[", "_").replace("]", "_")
    abbreviated = test_name[:25]
    
    # Combine: coll_{worker}_{hash}_{abbreviated}
    # Example: coll_gw0_a1b2c3d4_find_all_documents
    collection_name = f"coll_{worker_id}_{name_hash}_{abbreviated}"[:100]  # Collection name limit
    
    coll = database_client[collection_name]

    yield coll

    # Cleanup: drop collection
    try:
        coll.drop()
    except Exception:
        pass  # Best effort cleanup
