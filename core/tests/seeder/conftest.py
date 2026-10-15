"""Conftest for seeder tests.

Ensure all seeder modules are imported so __init_subclass__
registers them in the global and fixture registries.
"""

import core.apps.configurations.fixtures.seeder  # noqa: F401
import core.apps.crm.fixtures.seeder  # noqa: F401
import core.apps.tenants.fixtures.seeder  # noqa: F401
import core.setup.crm.seeder  # noqa: F401
import core.setup.invoices.seeder  # noqa: F401
import core.setup.tenants.seeder  # noqa: F401
