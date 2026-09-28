"""Shared utilities for setUserWriteBlockMode tests."""


def force_disable_write_block(collection):
    """Force-disable write block regardless of current reason.

    Disabling requires the same ``reason`` that was used to enable the block:
    a no-reason disable fails with IllegalOperation ("Cannot release user
    writes critical section with different reason than the already-set
    reason") when the block was enabled with an explicit reason. So we first
    try the no-reason disable (works when enabled with no reason or when
    already disabled) and then fall back to each known reason until one
    matches the reason the block was enabled with.
    """
    admin = collection.database.client.admin
    try:
        admin.command({"setUserWriteBlockMode": 1, "global": False})
        return
    except Exception:
        pass
    for reason in [
        "Unspecified",
        "ClusterToClusterMigrationInProgress",
        "DiskUseThresholdExceeded",
    ]:
        try:
            admin.command({"setUserWriteBlockMode": 1, "global": False, "reason": reason})
            return
        except Exception:
            continue
