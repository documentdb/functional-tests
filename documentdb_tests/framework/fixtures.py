"""
Fixture utilities for test isolation and database management.

Provides reusable functions for creating database clients, generating unique
names, and managing test isolation.
"""

import hashlib

from pymongo import MongoClient


def create_engine_client(connection_string: str, engine_name: str = "default"):
    """
    Create and verify a MongoDB client connection.

    Args:
        connection_string: MongoDB connection string
        engine_name: Optional engine identifier for error messages

    Returns:
        MongoClient: Connected MongoDB client

    Raises:
        ConnectionError: If unable to connect to the database
    """
    client = MongoClient(connection_string)

    # Verify connection
    try:
        client.admin.command("ping")
    except Exception as e:
        # Close the client before raising
        client.close()
        # Raise ConnectionError so analyzer categorizes as INFRA_ERROR
        raise ConnectionError(f"Cannot connect to {engine_name} at {connection_string}: {e}") from e

    return client


def generate_database_name(test_id: str, worker_id: str = "master") -> str:
    """
    Generate a unique database name for test isolation.

    Creates a collision-free name for parallel execution that includes
    worker ID, hash, and abbreviated test name.

    Args:
        test_id: Full test identifier (e.g., test file path + test name)
        worker_id: Worker ID from pytest-xdist (e.g., 'gw0', 'gw1', or 'master')

    Returns:
        str: Unique database name (max 63 characters for MongoDB compatibility)
    """
    # Create a short hash for uniqueness (first 8 chars of SHA256)
    name_hash = hashlib.sha256(test_id.encode()).hexdigest()[:8]

    # Get abbreviated test name for readability (sanitize and truncate)
    test_name = test_id.split("::")[-1] if "::" in test_id else test_id
    abbreviated = test_name.replace("[", "_").replace("]", "_")[:20]

    # Combine: test_{worker}_{hash}_{abbreviated}
    # Example: test_gw0_a1b2c3d4_find_all_documents
    db_name = f"test_{worker_id}_{name_hash}_{abbreviated}"[:63]  # MongoDB limit

    return db_name


def generate_collection_name(test_id: str, worker_id: str = "master") -> str:
    """
    Generate a unique collection name for test isolation.

    Creates a collision-free name for parallel execution that includes
    worker ID, hash, and abbreviated test name.

    Args:
        test_id: Full test identifier (e.g., test file path + test name)
        worker_id: Worker ID from pytest-xdist (e.g., 'gw0', 'gw1', or 'master')

    Returns:
        str: Unique collection name (max 100 characters)
    """
    # Create a short hash for uniqueness (first 8 chars of SHA256)
    name_hash = hashlib.sha256(test_id.encode()).hexdigest()[:8]

    # Get abbreviated test name for readability (sanitize and truncate)
    test_name = test_id.split("::")[-1] if "::" in test_id else test_id
    abbreviated = test_name.replace("[", "_").replace("]", "_")[:25]

    # Combine: coll_{worker}_{hash}_{abbreviated}
    # Example: coll_gw0_a1b2c3d4_find_all_documents
    collection_name = f"coll_{worker_id}_{name_hash}_{abbreviated}"[:100]  # Collection name limit

    return collection_name


def cleanup_database(client: MongoClient, database_name: str):
    """
    Drop a database, best effort.

    Args:
        client: MongoDB client
        database_name: Name of database to drop
    """
    try:
        client.drop_database(database_name)
    except Exception:
        pass  # Best effort cleanup


def cleanup_collection(database, collection_name: str):
    """
    Drop a collection, best effort.

    Args:
        database: MongoDB database object
        collection_name: Name of collection to drop
    """
    try:
        database[collection_name].drop()
    except Exception:
        pass  # Best effort cleanup
