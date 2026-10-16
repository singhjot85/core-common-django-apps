---
name: backend-pytest
description: Write or extend pytest test coverage for Python backend code (Django / DRF). Use after finishing a model, view, serializer, util, service or task, when the user asks for tests or more coverage, or when fixing a bug that needs a regression test. Covers file layout, fixtures, factories, what to mock, test patterns and how to run tests with make targets.
---

# Backend Pytest Skill

## Goal

Tests should prove real behaviour through real workflows, fail for one clear reason, and be easy to read when they break. Prefer fewer, realistic tests over many tests that only check mocks.

## Workflow

1. Read the code under test. Know its inputs, outputs, side effects, permissions and failure cases.
2. Look at existing tests first: the app's `conftest.py`, existing fixtures and factories. Reuse them. Do not duplicate setup that already exists.
3. Decide the cases (see "What to cover").
4. Write the tests in the right file (see "Layout").
5. Run only the new tests, fix failures, then run the whole app folder to check nothing else broke (see "Running tests").
6. If a test fails because the code is wrong, tell the user. Do not bend the test to pass a bug.

## Layout

Tests live under `backend/tests/`, in one folder per app, mirroring the source file they cover.

```
backend
  |- tests
      |- app_name
      |   |- test_models.py
      |   |- test_views.py
      |   |- test_utils.py
      |- crm
          |- conftest.py
          |- test_models.py
          |- test_views.py
          |- test_utils.py
          |- test_serializers.py
```

Rules:
- The shared-fixtures file is named exactly `conftest.py`. Pytest ignores any other spelling (such as `conftests.py`), so fixtures in it silently will not load.
- Name files `test_<source_module>.py`: `test_models.py`, `test_views.py`, `test_serializers.py`, `test_utils.py`, `test_tasks.py`, `test_services.py`, `test_permissions.py`.
- Put fixtures used by several files of one app in that app's `conftest.py`. Put fixtures used across apps in `tests/conftest.py`. Keep fixtures used by one file in that file.
- Several folders contain a file with the same name (`test_models.py`). Pytest needs each test folder to be a package (add an empty `__init__.py`) or the project to use `--import-mode=importlib`. Check which the project uses before adding a new app folder, otherwise you get "import file mismatch" errors.

## Structure and naming

- Group related tests in a class named `Test<Thing>` (for example `TestShipmentCancel`). No `__init__` method on test classes.
- Name tests `test_<action>_<condition>_<expected result>`: `test_cancel_after_pickup_returns_400`.
- One behaviour per test. A test that checks five unrelated things is five tests.
- Write each test in Arrange / Act / Assert order, with a blank line between the parts.
- Add a one-line docstring saying what scenario and result the test covers (see the `backend-doc-string` skill).
- Tests must not depend on each other or on run order. Each test builds its own data.
- Tests must be deterministic. No real clock, randomness or network. Freeze time (for example `freezegun` or `time_machine`, whichever the project already uses) and seed randomness where the result depends on them.

## Setup: fixtures, factories, database

- Prefer pytest fixtures over `setup_method`. Use `setup_method` only when it is clearly simpler and the project already does it.
- Create database objects with factories (for example `factory_boy`, or the factories already in the project). Factories create real rows. That is the right way, and it is not mocking.
- Never mock the ORM, models, querysets or serializers. Use the real test database.
- Mark any test that touches the database with `@pytest.mark.django_db` (on the class when every test needs it).
- Make a factory or fixture return the minimum valid object. Override only the fields the test cares about, so the test shows what matters:

```python
shipment = ShipmentFactory(status=Shipment.Status.IN_TRANSIT)
```

- Put sensible defaults in the factory, not in every test.

## What to mock (and what not to)

Mock only things outside your process:
- External HTTP APIs and third-party services (payment, SMS, email gateways).
- Other network I/O.
- Disk I/O (file writes, uploads) and storage backends.

Do not mock:
- Your own utils, services, serializers, models or managers. Run the real workflow, even when it feels redundant. Mocking them hides integration bugs.
- The database.

When you do mock:
- Patch where the name is used, not where it is defined: `patch("crm.services.sms.send")`, not `patch("sms_client.send")`.
- Prefer a fake response from the boundary (a stub that returns data) over asserting that a function was called.
- Also assert the visible result: the response, the DB state, the status change. A test that only asserts `mock.assert_called_once()` proves little.
- Run Celery tasks eagerly or call the task function directly. Do not mock the task body.

## What to cover

For each unit, pick the cases that apply:

- Happy path.
- Validation failures (bad, missing or boundary input).
- Permissions: anonymous user, wrong user, correct user, staff.
- Not-found and wrong-state cases (for example cancelling an already delivered shipment).
- Edge cases: empty list, None, duplicates, maximum sizes.
- Side effects: DB rows created or changed, status transitions, tasks queued.
- Regression test for every bug fixed.

Do not test Django or DRF themselves (for example, that `CharField(max_length=10)` rejects 11 characters). Test your rules.

## Patterns per file type

### Models (`test_models.py`)
- Custom methods, properties, constraints, `save` / `clean` logic, managers and status transitions.
- Test invalid transitions raise errors, and valid ones update the right fields.

### Views (`test_views.py`)
- Use DRF's `APIClient` with a fixture for each user type, and authenticate with `force_authenticate` unless you are testing auth itself.
- Assert the status code, the response body shape and the database state.
- Cover every status code listed in the view's `API details` docstring.

```python
@pytest.mark.django_db
class TestShipmentCancel:
    def test_owner_can_cancel_created_shipment(self, api_client, user):
        """
        Owner cancelling a Created shipment gets 200 and status becomes Cancelled.
        """
        shipment = ShipmentFactory(sender=user, status=Shipment.Status.CREATED)
        api_client.force_authenticate(user)

        response = api_client.post(f"/api/shipments/{shipment.id}/cancel/")

        assert response.status_code == 200
        shipment.refresh_from_db()
        assert shipment.status == Shipment.Status.CANCELLED
```

### Serializers (`test_serializers.py`)
- Valid data passes. Each validation rule has one failing case. Check the error key and message. Check read-only fields are ignored on input.

### Utils and services (`test_utils.py`, `test_services.py`)
- Test input and output directly. Use `pytest.mark.parametrize` for many input and output pairs.
- For services, also check transaction behaviour: when it fails halfway, nothing is saved.

### Tasks (`test_tasks.py`)
- Test the effect, that it is safe to run twice (idempotent) if it should be, and the retry or failure path using a mocked external call.

### Permissions (`test_permissions.py`)
- One test per role per allowed and denied outcome.

## Parametrize instead of copy-paste

```python
@pytest.mark.parametrize(
    "weight, expected_price",
    [(1, 50), (10, 200), (0, None)],
)
def test_price_for_weight(weight, expected_price):
    """
    Price grows with weight, and zero weight has no price.
    """
    assert calculate_price(weight) == expected_price
```

Use it when only the data changes. If the logic changes between cases, write separate tests.

## Running tests

Always use the make targets, not raw `pytest`:

- `make t`: run the whole suite.
- `make t DIR=<path>`: run one folder, for example `make t DIR=tests/crm`.
- `make tf TEST_FILTER=<expression>`: run tests matching a filter, for example `make tf TEST_FILTER=test_cancel`.

Run the narrowest target while writing (`tf` or `DIR`), then the app folder before finishing. If a make target is missing or fails to start, tell the user instead of falling back silently.

## Quick checklist before finishing

- [ ] Files are in `tests/<app>/` and named `test_<module>.py`. Shared fixtures are in `conftest.py`.
- [ ] Related tests are grouped in a class, with clear `test_<action>_<condition>_<result>` names.
- [ ] DB tests have `django_db`. Objects come from factories or fixtures.
- [ ] Only external APIs and I/O are mocked, and the visible result is also asserted.
- [ ] Happy path, validation, permission and edge cases are covered where they apply.
- [ ] Tests do not depend on order, real time or network.
- [ ] New tests pass with the make targets, and the surrounding folder still passes.
