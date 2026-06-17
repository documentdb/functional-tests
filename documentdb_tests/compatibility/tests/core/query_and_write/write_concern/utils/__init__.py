"""Shared helpers for writeConcern tests."""


def build_cmd(cmd: str, ctx, wc) -> dict:
    """Build a command dict with the given writeConcern for any write command."""
    if cmd == "update":
        return {
            "update": ctx.collection,
            "updates": [{"q": {}, "u": {"$set": {"a": 1}}}],
            "writeConcern": wc,
        }
    elif cmd == "delete":
        return {
            "delete": ctx.collection,
            "deletes": [{"q": {"_id": 99}, "limit": 1}],
            "writeConcern": wc,
        }
    elif cmd == "findAndModify":
        return {
            "findAndModify": ctx.collection,
            "query": {"_id": 1},
            "update": {"$set": {"a": 1}},
            "writeConcern": wc,
        }
    elif cmd == "insert":
        return {
            "insert": ctx.collection,
            "documents": [{"_id": 100}],
            "writeConcern": wc,
        }
    raise ValueError(f"Unknown command: {cmd}")


# Commands to test exhaustively for writeConcern validation.
# insert excluded: already has dedicated tests at commands/insert/test_insert_write_concern.py.
# bulkWrite excluded: the MongoDB 8.0+ server-level bulkWrite command uses admin database
# with nsInfo/ops arrays, requiring fundamentally different command construction.
WRITE_COMMANDS = ["update", "delete", "findAndModify"]
