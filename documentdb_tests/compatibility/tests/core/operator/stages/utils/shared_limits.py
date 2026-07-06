"""Limit constants shared between the $replaceRoot and $replaceWith limit tests."""

from __future__ import annotations

# The maximum sub-object nesting depth below a document root that insertion
# accepts; one level deeper overflows. This is an insert-time limit on stored
# documents and is independent of the promoting stage.
MAX_STORED_NESTING_DEPTH = 179

# The maximum BSON nesting depth a command document may reach before the server
# rejects it with an Overflow error. This is a global command-parse limit, not a
# stage behavior: find/distinct bottom out at this same depth. A stage's
# accepted literal depth is this ceiling minus the wrapper levels its command
# path consumes.
MAX_COMMAND_NESTING_DEPTH = 200

# The output document size limit, in bytes, that both stages enforce on their
# result: 16 MiB plus 16 KiB. It is higher than the 16 MiB standard insert
# limit, so a stored input can stay within the standard limit while the
# constructed output reaches this larger ceiling.
MAX_OUTPUT_DOC_SIZE = 16_793_600

# Both stages exercise the output-size boundary by building the output document
# {"s": <big>, "pad": <pad>} via $mergeObjects from a stored sub-document. The
# constants below describe that shared construction.

# Size in bytes of a stored string within the input-document limit that supplies
# the bulk of the size boundary output.
BIG_STORED_STRING_BYTES = 16_000_000

# Bytes the output document {"s": <big>, "pad": <pad>} adds on top of its two
# string payloads, used to solve for the pad length at a target size.
OUTPUT_FRAMING_BYTES = 23

# Pad payload sizes in bytes that bring the constructed output document
# {"s": <big>, "pad": <pad>} exactly to the maximum accepted size and one byte
# over it.
BOUNDARY_PAD_BYTES = MAX_OUTPUT_DOC_SIZE - OUTPUT_FRAMING_BYTES - BIG_STORED_STRING_BYTES
OVER_LIMIT_PAD_BYTES = MAX_OUTPUT_DOC_SIZE + 1 - OUTPUT_FRAMING_BYTES - BIG_STORED_STRING_BYTES
