"""Every test in this folder covers behavior added in spec 8.3."""

from documentdb_tests.framework.preconditions import spec_gate_folder

pytest_collection_modifyitems = spec_gate_folder(__file__, spec_since="8.3")
