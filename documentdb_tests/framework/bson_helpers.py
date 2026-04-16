"""Utilities for constructing raw BSON documents with features not
expressible through Python mappings (e.g. duplicate keys).
"""

from __future__ import annotations

from typing import Any

import bson
from bson.raw_bson import RawBSONDocument


def build_raw_bson_doc(fields: list[tuple[str, Any]]) -> RawBSONDocument:
    """Build a raw BSON document from a list of (key, value) pairs.

    Unlike Python dicts, this preserves duplicate keys, allowing tests to verify
    server behavior when the same field name appears more than once. Values can
    be any type that ``bson.encode`` accepts.

    Args:
        fields: Ordered (key, value) pairs.

    Returns:
        A RawBSONDocument containing the encoded fields.
    """
    elements = b""
    for name, value in fields:
        # Encode a single-key document and strip the wrapper to get
        # the raw element (type byte + key + value).
        encoded = bson.encode({name: value})
        # BSON layout: 4-byte length + elements + trailing \x00
        # Strip the 4-byte length prefix and the trailing \x00.
        elements += encoded[4:-1]
    doc_len = 4 + len(elements) + 1
    return RawBSONDocument(doc_len.to_bytes(4, "little") + elements + b"\x00")
