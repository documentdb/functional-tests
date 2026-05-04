# Smoke Test Notes

## Overview

Smoke test files: 456
Feature tree entries: 469
Missing: 13

## Missing Features (13)

These features are replication related and not covered by smoke tests yet.

- system > replication > commands > appendOplogNote
- system > replication > commands > applyOps
- system > replication > commands > hello
- system > replication > commands > replSetAbortPrimaryCatchUp
- system > replication > commands > replSetFreeze
- system > replication > commands > replSetGetConfig
- system > replication > commands > replSetGetStatus
- system > replication > commands > replSetInitiate
- system > replication > commands > replSetMaintenance
- system > replication > commands > replSetReconfig
- system > replication > commands > replSetResizeOplog
- system > replication > commands > replSetStepDown
- system > replication > commands > replSetSyncFrom

## Assert-on-Failure Tests (6)

These smoke tests verify that a command exists and is properly rejected with a specific
error. The command is recognized by the server but fails due to preconditions (no active
transaction, no encrypted collection, not permitted, etc.).

| Feature | Code | Error Message | Reason |
|---|---|---|---|
| core/sessions/commands/abortTransaction | 125 | abortTransaction must be run within a transaction | No active transaction to abort |
| core/sessions/commands/commitTransaction | 125 | commitTransaction must be run within a transaction | No active transaction to commit |
| system/administration/commands/compactStructuredEncryptionData | 6346807 | Target namespace is not an encrypted collection | No encrypted collection exists |
| system/administration/commands/setIndexCommitQuorum | 27 | Cannot find an index build on collection '...' with the provided index names | No active index build in progress |
| system/administration/commands/shutdown | 13 (Unauthorized) | shutdown must run from localhost when running db without auth | Shutdown requires localhost or auth |
| system/security/authentication/commands/authenticate | 18 (AuthenticationFailed) | Authentication failed. | Invalid credentials provided intentionally |

## Replica Set Tests — Standalone Errors (24)

These smoke tests are marked with `replica_set` and cannot run against a standalone MongoDB instance.
They are automatically skipped when the server is not a replica set member.
Below are the errors returned when running each against a standalone MongoDB instance.

### Change Streams (16)

All change stream tests fail with the same error:
- **Code**: 40573 (Location40573)
- **Message**: "The $changeStream stage is only supported on replica sets"

| Feature | Test File |
|---|---|
| changeStreams/create | test_smoke_changeStream_create.py |
| changeStreams/createIndexes | test_smoke_changeStream_createIndexes.py |
| changeStreams/delete | test_smoke_changeStream_delete.py |
| changeStreams/drop | test_smoke_changeStream_drop.py |
| changeStreams/dropDatabase | test_smoke_changeStream_dropDatabase.py |
| changeStreams/dropIndexes | test_smoke_changeStream_dropIndexes.py |
| changeStreams/insert | test_smoke_changeStream_insert.py |
| changeStreams/invalidate | test_smoke_changeStream_invalidate.py |
| changeStreams/modify | test_smoke_changeStream_modify.py |
| changeStreams/refineCollectionShardKey | test_smoke_changeStream_refineCollectionShardKey.py |
| changeStreams/rename | test_smoke_changeStream_rename.py |
| changeStreams/replace | test_smoke_changeStream_replace.py |
| changeStreams/reshardCollection | test_smoke_changeStream_reshardCollection.py |
| changeStreams/shardCollection | test_smoke_changeStream_shardCollection.py |
| changeStreams/update | test_smoke_changeStream_update.py |
| core/operator/system-stages/changeStream | test_smoke_changeStream.py |

### Stages (2)

| Feature | Code | Error Message |
|---|---|---|
| core/operator/stages/changeStreamSplitLargeEvent | 40573 | The $changeStream stage is only supported on replica sets |
| core/operator/stages/listSampledQueries | 20 | $listSampledQueries is not supported on a standalone mongod |

### Query Planning (2)

| Feature | Code | Error Message |
|---|---|---|
| core/query-planning/commands/removeQuerySettings | 20 | removeQuerySettings can only run on replica sets or sharded clusters |
| core/query-planning/commands/setQuerySettings | 20 | setQuerySettings can only run on replica sets or sharded clusters |

### Administration (3)

| Feature | Code | Error Message |
|---|---|---|
| system/administration/commands/getDefaultRWConcern | 51300 | 'getDefaultRWConcern' is not supported on standalone nodes. |
| system/administration/commands/setDefaultRWConcern | 51300 | 'setDefaultRWConcern' is not supported on standalone nodes. |
| system/administration/commands/setUserWriteBlockMode | 20 | setUserWriteBlockMode cannot be run on standalones |

### Security (1)

| Feature | Code | Error Message |
|---|---|---|
| system/security/encryption | 6346402 | Encrypted collections are not supported on standalone |

## Hardcoded-Skip Tests — Standalone Errors (8)

These smoke tests have `@pytest.mark.skip` decorators because they require infrastructure
not available on standard MongoDB (sharded cluster, Atlas Search, or MongoDB Enterprise).

### Auditing (1)

| Feature | Code | Error Message |
|---|---|---|
| auditing/commands/logApplicationMessage | 59 | no such command: 'logApplicationMessage' (requires auditing to be enabled via --auditLog) |

### Change Streams — Sharding (3)

All three require a sharded cluster. On standalone, `$changeStream` itself fails first.

| Feature | Code | Error Message |
|---|---|---|
| changeStreams/refineCollectionShardKey | 40573 | The $changeStream stage is only supported on replica sets |
| changeStreams/reshardCollection | 40573 | The $changeStream stage is only supported on replica sets |
| changeStreams/shardCollection | 40573 | The $changeStream stage is only supported on replica sets |

### Atlas Search Stages (4)

All four require Atlas Search, which is not available on standard MongoDB deployments.
- **Code**: 31082 (SearchNotEnabled)

| Feature | Code | Error Message |
|---|---|---|
| stages/listSearchIndexes | 31082 | Using Atlas Search Database Commands and the $listSearchIndexes aggregation stage requires additional configuration. |
| stages/search | 31082 | Using $search and $vectorSearch aggregation stages requires additional configuration. |
| stages/searchMeta | 31082 | Using $search and $vectorSearch aggregation stages requires additional configuration. |
| stages/vectorSearch | 31082 | Using $search and $vectorSearch aggregation stages requires additional configuration. |
