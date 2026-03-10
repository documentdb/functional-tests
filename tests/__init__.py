"""
DocumentDB Functional Tests

End-to-end functional testing suite for DocumentDB.

This package provides test utilities and common assertions for testing
DocumentDB functionality.
"""

from framework.assertions import (
    assert_count,
    assert_document_match,
    assert_documents_match,
    assert_field_exists,
    assert_field_not_exists,
)

__all__ = [
    "assert_count",
    "assert_document_match",
    "assert_documents_match",
    "assert_field_exists",
    "assert_field_not_exists",
]
