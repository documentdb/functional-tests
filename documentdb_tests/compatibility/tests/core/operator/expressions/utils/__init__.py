from dataclasses import dataclass
from typing import Any, Optional

from dataclasses import dataclass
from typing import Any, Optional

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import *
from documentdb_tests.framework.error_codes import *
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
    execute_expression_with_insert,
)
