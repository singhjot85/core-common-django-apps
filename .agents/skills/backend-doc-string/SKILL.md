---
name: backend-doc-string
description: Write or update docstrings for Python backend code (*.py), especially Django / DRF projects. Use right after finishing a function, class, model, serializer, viewset, task or module, or when the user asks to add, fix or complete docstrings in a file. Docstrings must be plain-language and help a reviewer or debugger understand behaviour, side effects and failure cases without reading the whole body.
---

# Backend Docstring Skill

## Goal

A docstring answers the questions a reviewer or a person debugging at 2 AM will ask:

1. What does this do, in one sentence?
2. Why does it exist / what rule does it enforce?
3. What goes in, what comes out?
4. What else does it touch (DB writes, signals, external calls, cache)?
5. How can it fail, and what does the caller see?

Write in simple, direct language. Short sentences. No jargon the next developer would have to look up.

## When to use

- After completing a function, class, model, serializer, viewset, task or module.
- When the user asks to add, fix or complete docstrings for a file.
- When you change behaviour: update the docstring in the same edit.

## Workflow

1. Read the code you are documenting. Document what it actually does, not what the name suggests.
2. Do not invent behaviour. If something is unclear, say so to the user instead of guessing.
3. Write or update the docstring using the templates below.
4. If an existing docstring is stale or wrong, fix it. Do not leave contradictions.
5. Do not change code logic while documenting.
6. Check afterwards: the file still parses (`python -m py_compile <file>`), and if the project uses `ruff` or `pydocstyle`, run it.

## Core rules

- Follow PEP 257, with one project rule on top: the opening and closing `"""` each go on their own line.
- Always use `"""` (triple double quotes). Use `r"""` if the docstring contains backslashes.
- Indent with 4 spaces.
- Every module, public class, public function and public method (including `__init__`) gets a docstring.
- Private helpers (`_name`) need one only when the logic is not obvious.
- A package may be documented in the `__init__.py` module docstring.
- The first line is a one-sentence summary in the imperative mood ("Return...", "Create...", "Validate..."), ending with a period.
- Leave one blank line between the summary and the rest.

## Writing style

Do:
- Explain **why** and **what rule** the code follows. The code already shows how.
- Name side effects explicitly: database writes, signals fired, Celery tasks queued, external API calls, cache changes, files written.
- State assumptions and constraints: "Caller must hold the transaction", "Expects a non-empty list".
- Mention important edge cases: empty input, None, duplicates, permission limits.
- Use the project's own words (model names, status names) so readers can search for them.

Don't:
- Restate the code line by line ("loops over items and appends to list").
- Write vague summaries ("Handles data", "Utility function").
- Copy the function name into a sentence ("Gets the user" for `get_user`).
- Document behaviour that does not exist, or leave TODOs inside docstrings.
- Use long paragraphs. Prefer 1-3 short sentences per idea, or a short list.

## Section names and order

Use these exact headers (Google style, compatible with Sphinx Napoleon), in this order, and include only the ones that apply:

1. Summary line
2. Extended description (behaviour, logic, constraints)
3. `Side effects:`
4. `Args:`
5. `Returns:` (or `Yields:` for generators)
6. `Raises:`
7. `Example:`

Rules for each section:
- `Args:` one line per argument: `name (type, optional): Description. Defaults to X.` Skip `self` and `cls`.
- `Returns:` `type: Description.` If the return shape is a dict or tuple, describe each key or position.
- `Raises:` one entry per exception type, with bullets for each case that triggers it.
- `Example:` optional. Use `>>>` lines. Only when usage is not obvious.

Use `Raises:`, not `Exceptions:` or `Exception:`. Keep the spelling identical across the whole codebase so tools and readers can rely on it.

## Templates

### Function / method

```python
def transfer_stock(source_id, target_id, quantity, *, dry_run=False):
    """
    Move stock from one warehouse to another.

    Checks that the source has enough stock, then reduces the source
    and increases the target in a single transaction. Both rows are
    locked with ``select_for_update`` to avoid double-spending stock.

    Constraints:
    - ``quantity`` must be greater than zero.
    - Source and target must be different warehouses.

    Side effects:
    - Writes two ``StockLevel`` rows.
    - Creates one ``StockMovement`` audit record.
    - Skipped entirely when ``dry_run`` is True.

    Args:
        source_id (int): ID of the warehouse losing stock.
        target_id (int): ID of the warehouse gaining stock.
        quantity (int): Units to move. Must be positive.
        dry_run (bool, optional): Validate only, do not write.
            Defaults to False.

    Returns:
        StockMovement: The audit record. None when ``dry_run`` is True.

    Raises:
		InsufficientStockError: Source has fewer units than ``quantity``.
        ValidationError:
        - ``quantity`` is zero or negative.
        - Source and target are the same warehouse.

    Example:
        >>> transfer_stock(1, 2, 10)
        ... <StockMovement: 1 -> 2 (10)>
    """
```

### Small or obvious helper

One line is enough. Still use the separate-line quotes.

```python
def is_expired(token):
    """
    Return True if the token's expiry time has passed.
    """
```

### Test function

Say what scenario is set up and what outcome is expected.

```python
def test_transfer_fails_when_stock_is_low(self):
    """
    Transfer raises InsufficientStockError when source has too little stock.
    """
```

### Class

```python
class StockService:
    """
    Handles stock movements between warehouses.

    All public methods run inside a transaction. Do not call them
    from inside another ``select_for_update`` block on the same rows.

    Attributes:
        default_batch_size (int): Rows processed per bulk operation.
    """
```

### Model

Describe what the model represents, then list relations, then the status flow if one exists.

```python
class Shipment(models.Model):
    """
    A parcel moving from a sender to a receiver on one route.

    Relations:
        sender (ForeignKey): User who created the shipment.
        route (ForeignKey): Route the shipment is assigned to.
        items (ReverseForeignKey): ``ShipmentItem`` rows in this shipment.
        tags (ManyToMany): Labels such as "fragile" or "urgent".
        invoice (OneToOne): Invoice created after delivery.

    Status flow:
        Created -> Assigned -> InTransit -> Delivered
                                  |-> Failed -> Assigned (retry)
        Created -> Cancelled

    Attributes:
        status (str): Current state. Changed only through ``advance_status``.
        weight_kg (Decimal): Total weight. Used for pricing.
    """
```

Notes for models:
- Keep the status flow as a plain indented block. Do not nest code fences inside a docstring.
- Only list fields that are not obvious from their name. Always list relations.
- Mention any custom manager, constraint or signal that changes behaviour.

### ViewSet / APIView

The docstring of a DRF view is often shown in generated API docs (Swagger / drf-spectacular), so write it for API consumers: what the endpoint does, who can call it, what it returns.

```python
class ShipmentViewSet(ModelViewSet):
    """
    Create, list and manage shipments for the logged-in user.

    Permissions: authenticated users. Users see only their own shipments;
    staff see all.

    API details:
    - GET ``/api/shipments/``
        - **200**: Paginated list of the user's shipments.
    - GET ``/api/shipments/{shipment_id}/``
        - **200**: Shipment details.
        - **404**: Shipment does not exist or belongs to another user.
    - POST ``/api/shipments/``
        - **201**: Shipment created.
        - **400**: Invalid payload (for example, weight is zero).
    """

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Cancel a shipment that has not been picked up yet.

        Sets the status to Cancelled and notifies the assigned driver.

        API details:
        - POST ``/api/shipments/{shipment_id}/cancel/``
            - **200**: Shipment cancelled.
            - **400**: Shipment is already InTransit or Delivered.
            - **403**: Caller does not own the shipment.
            - **404**: Shipment not found.

        Args:
            request (Request): DRF request. No body required.
            pk (str): Shipment ID from the URL.

        Returns:
            Response: Serialized shipment with the updated status.

        Raises:
            ValidationError:
            - Shipment status is not Created or Assigned.
        """
```

Rules for API details:
- One entry per HTTP method + URL. Write the real URL, with path params in `{braces}`.
- List every status code the endpoint can return, with the case that causes it. Use bold codes: `**200**`.
- Do not use triple backticks inside the docstring. Use double backticks for paths and names.

### Serializer

```python
class ShipmentSerializer(serializers.ModelSerializer):
    """
    Convert Shipment objects to and from JSON.

    Validation:
    - ``weight_kg`` must be positive.
    - ``route`` must be active.

    Read-only fields: ``status``, ``created_at``.
    """
```

### Service / business-logic function

Treat these as the most important to document. Include the business rule, the transaction behaviour and the side effects.

### Celery task / management command

State when it runs, whether it is safe to run twice (idempotent), and what happens on failure or retry.

```python
@shared_task(bind=True, max_retries=3)
def send_delivery_sms(self, shipment_id):
    """
    Send the "delivered" SMS to the receiver.

    Runs after a shipment reaches Delivered. Safe to retry: it skips
    shipments whose ``sms_sent_at`` is already set.

    Args:
        shipment_id (int): ID of the delivered shipment.

    Raises:
        SMSGatewayError:
        - Gateway is down. The task retries up to 3 times, then gives up.
    """
```

### Permission class, signal handler, manager / QuerySet method

- Permission: say who is allowed and who is denied.
- Signal handler: say which signal and sender it listens to, and what it does.
- QuerySet method: say what filter or annotation it applies, and that it returns a QuerySet (chainable).

### Property

One line describing the value. Mention if it triggers a query.

### Module

Top of file. Say what the module is for and what it exposes. Keep to 1-4 lines.

```python
"""
Stock movement services.

Business logic for moving stock between warehouses. Views should call
these functions instead of editing StockLevel rows directly.
"""
```

## Quick checklist before finishing

- [ ] Opening and closing `"""` are on their own lines.
- [ ] Summary is one imperative sentence ending in a period.
- [ ] Explains why or which rule applies, not just a restatement of the code.
- [ ] Side effects listed (DB, signals, tasks, external calls).
- [ ] Every argument, return value and raised exception is covered and matches the code.
- [ ] Section headers spelled exactly: `Args:`, `Returns:`, `Raises:`, `Side effects:`, `Example:`.
- [ ] No nested triple backticks, no tabs, no typos.
- [ ] No stale docstrings left in the same file.