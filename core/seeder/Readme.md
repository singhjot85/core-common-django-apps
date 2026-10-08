## Identifying Field Types

```python
from django.db import models

for field in MyModel._meta.get_fields():
    if isinstance(field, models.ManyToManyField):
        # Many-to-Many
    elif isinstance(field, models.ForeignKey):
        # Foreign Key (Many-to-One)
    elif isinstance(field, models.OneToOneField):
        # One-to-One
    elif field.auto_created and not field.concrete:
        # Reverse relation (e.g. related_name)
        # field.one_to_many → reverse FK
        # field.one_to_one  → reverse O2O
        # field.many_to_many → reverse M2M
    else:
        # Normal field (CharField, IntegerField, etc.)
```

### Quick check attributes

| Attribute            | Meaning                      |
| -------------------- | ---------------------------- |
| `field.is_relation`  | True for any relation        |
| `field.many_to_one`  | FK                           |
| `field.one_to_many`  | Reverse FK                   |
| `field.one_to_one`   | O2O (forward or reverse)     |
| `field.many_to_many` | M2M (forward or reverse)     |
| `field.concrete`     | Real DB column (normal + FK) |
| `field.auto_created` | Reverse relations            |

## Working With Them

```python
# Normal
obj.name = "x"; obj.save()

# ForeignKey
child.parent = parent_obj
child.parent_id = parent_obj.id   # no DB hit
child.save()

# Reverse FK (parent → children)
parent.child_set.all()                 # read
parent.child_set.add(child)            # set FK + save (only if null=True)
parent.child_set.create(name="x")      # create
parent.child_set.remove(child)         # nulls FK (only if null=True)
parent.child_set.clear()

# Many-to-Many
obj.tags.add(t1, t2)      # insert
obj.tags.remove(t1)       # delete link
obj.tags.clear()          # remove all links
obj.tags.set([t1, t2])    # replace
obj.tags.all()            # read

# Reverse M2M
tag.mymodel_set.all()
```

**Rule of thumb:** `add/remove/clear/set` work on M2M and nullable reverse FK; forward FK is just assignment + `save()`.

## Working With Fields Generically (no `obj.tags`)

Use `getattr` / `setattr` with `field.name`, and the descriptor API.

```python
def inspect_and_use(obj, field_name):
    field = obj._meta.get_field(field_name)

    # --- Normal / FK (concrete) ---
    if field.concrete and not field.many_to_many:
        getattr(obj, field.name)          # value or related obj
        setattr(obj, field.name, value)   # for FK use instance, not id
        setattr(obj, field.attname, value)# for FK use raw id (no DB hit)
        obj.save()

    # --- Forward M2M ---
    elif field.many_to_many and not field.auto_created:
        manager = getattr(obj, field.name)   # RelatedManager
        manager.add(x); manager.remove(x)
        manager.clear(); manager.set([...])
        manager.all()

    # --- Reverse FK (one_to_many) ---
    elif field.one_to_many:
        manager = getattr(obj, field.get_accessor_name())  # child_set
        manager.all(); manager.add(c); manager.create(**kw)
        manager.remove(c); manager.clear()   # only if FK null=True

    # --- Reverse O2O (one_to_one, auto_created) ---
    elif field.one_to_one and field.auto_created:
        related = getattr(obj, field.get_accessor_name())  # may raise DoesNotExist
        related.delete()

    # --- Reverse M2M ---
    elif field.many_to_many and field.auto_created:
        manager = getattr(obj, field.get_accessor_name())
        manager.all()
```

Key: for **reverse** relations the attribute name is `field.get_accessor_name()`, **not** `field.name`.

## `field.name` vs `field.attname`

|                     | `name`     | `attname`                   |
| ------------------- | ---------- | --------------------------- |
| Normal field        | `"title"`  | `"title"` (same)            |
| ForeignKey `parent` | `"parent"` | `"parent_id"`               |
| O2O `user`          | `"user"`   | `"user_id"`                 |
| M2M / reverse       | exists     | **not present** (no column) |

- **`name`** → the Python attribute you use (`obj.parent` → returns the related **instance**).
- **`attname`** → the actual **DB column / raw value** attribute (`obj.parent_id` → returns the **id**, no query).
- Only **concrete** fields (`field.concrete == True`) have an `attname`. M2M and reverse relations don't (they're not columns).

```python
field = MyModel._meta.get_field("parent")
field.name      # 'parent'   → instance
field.attname   # 'parent_id' → raw id
field.concrete  # True
```

**Rule:** write/read FK by `attname` when you only have an id (fast, no fetch); use `name` when you have/need the instance. For generic code, pick `attname` for concrete FK writes, `name` for everything else.P
