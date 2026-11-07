#!/usr/bin/env python3
"""Profile-driven Django app scaffolder.

Reads a project profile (see references/project-profile.md) and generates a new app or nested
feature-app that follows that project's conventions. Safe by default: never overwrites files,
supports --dry-run, only removes an empty generated migrations/ package.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

DEFAULT_PROFILE: dict = {
    "apps_root": "apps",
    "nested_container_dirs": ["features", "providers"],
    "swappable_models": False,
    "base_model": "django.db.models.Model",
    "app_settings": None,
    "admin": {"private_site": None, "public_site": None},
    "tenancy": None,
    "migrations": {"mode": "in_app", "root": None},
    "settings_registry_file": None,
    "registry_lists": {"all": "INSTALLED_APPS", "tenant": None, "public": None},
    "tests_root": None,
    "commands": {
        "makemigrations": "python manage.py makemigrations {app_label}",
        "test": "python manage.py test {module_path}",
        "lint": None,
    },
}


# ---------- helpers ----------
def deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def pascal(val: str) -> str:
    parts = [p for p in re.split(r"[-_\s]+", val) if p]
    if len(parts) > 1:
        return "".join(p[:1].upper() + p[1:] for p in parts)
    return val[:1].upper() + val[1:]


def snake(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).replace("-", "_").lower()


def split_dotted(path: str) -> tuple[str, str]:
    mod, _, name = path.rpartition(".")
    return mod, name


def find_profile(explicit: str | None) -> tuple[dict, str | None]:
    candidates = [Path(explicit)] if explicit else [
        Path(__file__).resolve().parent.parent / "project.profile.json",
        Path.cwd() / "project.profile.json",
    ]
    for c in candidates:
        if c.is_file():
            return deep_merge(DEFAULT_PROFILE, json.loads(c.read_text())), str(c)
    if explicit:
        sys.exit(f"Profile not found: {explicit}")
    print("! No project.profile.json found; using plain-Django defaults. "
          "Run discovery (references/project-profile.md) for project-specific conventions.\n")
    return copy.deepcopy(DEFAULT_PROFILE), None


class Writer:
    def __init__(self, dry: bool, force: bool):
        self.dry, self.force = dry, force
        self.created: list[Path] = []
        self.skipped: list[Path] = []

    def write(self, path: Path, content: str) -> None:
        if path.exists() and not self.force:
            self.skipped.append(path)
            print(f"  - skip (exists): {path}")
            return
        print(f"  + {'would create' if self.dry else 'created'}: {path}")
        if not self.dry:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        self.created.append(path)


# ---------- generators ----------
def gen_apps(ctx) -> str:
    return f'''from django.apps import AppConfig


class {ctx["cls"]}Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "{ctx["module"]}"
    label = "{ctx["label"]}"
    verbose_name = "{ctx["verbose"]}"
'''


def gen_constants(ctx) -> str:
    return '''from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusChoices(models.TextChoices):
    DRAFT = "draft", _("Draft")
    ACTIVE = "active", _("Active")
    ARCHIVED = "archived", _("Archived")
'''


def model_body(ctx, name: str, abstract: bool) -> str:
    fields = '    name = models.CharField(max_length=255)\n'
    if ctx["with_status"]:
        fields += ('    status = models.CharField(\n        max_length=32,\n'
                   '        choices=StatusChoices.choices,\n        default=StatusChoices.DRAFT,\n    )\n')
    meta_abs = "        abstract = True\n" if abstract else ""
    prefix = "Abstract" if abstract else ""
    return f'''

class {prefix}{name}({ctx["base_cls"]}):
    """TODO: describe {name}. Replace placeholder fields."""

{fields}
    class Meta:
{meta_abs}        verbose_name = _("{name}")

    def __str__(self) -> str:
        return self.name or str(self.pk)
'''


def abstract_header(ctx) -> str:
    mod, cls = split_dotted(ctx["profile"]["base_model"])
    imp = "from django.db import models\nfrom django.utils.translation import gettext_lazy as _\n\n"
    if ctx["with_status"]:
        imp += f'from {ctx["module"]}.constants import StatusChoices\n'
    if cls != "Model" or mod != "django.db.models":
        imp += f"from {mod} import {cls}\n"
    return imp


def gen_models_abstract_file(ctx, name: str) -> str:
    return abstract_header(ctx) + model_body(ctx, name, True)


def gen_models_abstract_single(ctx) -> str:
    out = abstract_header(ctx)
    for m in ctx["models"]:
        out += model_body(ctx, m, True)
    return out


def gen_models_concrete(ctx) -> str:
    out = f'from {ctx["module"]} import models_abstract\n'
    for m in ctx["models"]:
        out += f'''

class {m}(models_abstract.Abstract{m}):
    """Concrete {m}; no fields here. Add them to Abstract{m}."""

    class Meta(models_abstract.Abstract{m}.Meta):
        swappable = "{ctx["swap_key"][m]}"
'''
    return out


def gen_models_plain(ctx) -> str:
    return abstract_header(ctx) + "".join(model_body(ctx, m, False) for m in ctx["models"])


def gen_app_settings(ctx) -> str:
    cfg = ctx["profile"]["app_settings"]
    bmod, bcls = split_dotted(cfg["base_class"])
    return f'''from {bmod} import {bcls}


class {ctx["cls"]}Settings({bcls}):
    """Settings for {ctx["verbose"]}. The singleton is created in __init__.py, never here."""

    SETTINGS_KEY = "{ctx["settings_key"]}"
'''


def gen_init(ctx) -> str:
    p = ctx["profile"]
    lines = ["import typing\n"]
    swap = p["swappable_models"]
    if swap:
        lines.append("from django.apps import apps as django_apps\nfrom django.conf import settings\n")
    if p["app_settings"]:
        lines.append(f'from {ctx["module"]}.app_settings import {ctx["cls"]}Settings\n')
    if swap:
        names = ", ".join(f"Abstract{m}" for m in ctx["models"])
        lines.append(f"if typing.TYPE_CHECKING:\n    from .models_abstract import {names}\n")
    if p["app_settings"]:
        lines.append(f'\napp_settings: {ctx["cls"]}Settings = {ctx["cls"]}Settings()\n')
    if swap:
        for m in ctx["models"]:
            lines.append(f'''
def get_{snake(m)}_model():
    """Return the configured {m} model."""
    return typing.cast(
        type["Abstract{m}"],
        django_apps.get_model(settings.{ctx["swap_key"][m]}, require_ready=False),
    )
''')
    return "\n".join(lines)


def gen_admin(ctx) -> str:
    p = ctx["profile"]
    site_path = p["admin"]["public_site" if ctx["public"] else "private_site"]
    swap = p["swappable_models"]
    head = "from django.contrib import admin\n\n"
    site_kw = ""
    if site_path:
        smod, sname = split_dotted(site_path)
        head += f"from {smod} import {sname}\n"
        site_kw = f", site={sname}"
    if swap:
        head += f'from {ctx["module"]} import ' + ", ".join(f"get_{snake(m)}_model" for m in ctx["models"]) + "\n\n"
        head += "\n".join(f"{m} = get_{snake(m)}_model()" for m in ctx["models"]) + "\n"
    else:
        head += f'from {ctx["module"]}.models import ' + ", ".join(ctx["models"]) + "\n"
    body = ""
    cols = '"id", "name", "status"' if ctx["with_status"] else '"id", "name"'
    for m in ctx["models"]:
        body += f'''

@admin.register({m}{site_kw})
class {m}Admin(admin.ModelAdmin):
    list_display = ({cols})
    search_fields = ("name",)
'''
    return head + body


def gen_readme(ctx) -> str:
    rows = "".join(f"| `{m}` | `{ctx['swap_key'][m]}` |\n" for m in ctx["models"]) if ctx["profile"]["swappable_models"] else ""
    table = f"\n| Model | Swappable key |\n| :-- | :-- |\n{rows}" if rows else ""
    return f"# {ctx['verbose']} (`{ctx['module']}`)\n\nTODO: purpose, models, settings, public API.\n{table}"


def gen_test(ctx) -> str:
    m = ctx["models"][0]
    if ctx["profile"]["swappable_models"]:
        return f'''import pytest

from {ctx["module"]} import get_{snake(m)}_model


@pytest.mark.django_db
def test_{snake(m)}_model_resolves_and_saves():
    model = get_{snake(m)}_model()
    assert model.__name__ == "{m}"
    obj = model.objects.create(name="example")
    assert str(obj) == "example"
'''
    return f'''import pytest

from {ctx["module"]}.models import {m}


@pytest.mark.django_db
def test_{snake(m)}_saves():
    assert str({m}.objects.create(name="example")) == "example"
'''


# ---------- main ----------
def main() -> None:
    ap = argparse.ArgumentParser(description="Scaffold a Django app from a project profile.")
    ap.add_argument("app_label")
    ap.add_argument("--profile")
    ap.add_argument("--path", help="Explicit app dir (feature-apps), relative to repo root")
    ap.add_argument("--label", help="Override derived app label")
    ap.add_argument("--models", nargs="+")
    ap.add_argument("--public", action="store_true", help="Public-schema app (requires tenancy in profile)")
    ap.add_argument("--abstract-dir", action="store_true")
    ap.add_argument("--with-status", action="store_true", help="Add a status field + constants")
    ap.add_argument("--verbose-name")
    ap.add_argument("--root", default=".", help="Repo root (default: cwd)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files")
    a = ap.parse_args()

    p, profile_path = find_profile(a.profile)
    root = Path(a.root).resolve()
    apps_root = Path(p["apps_root"])
    name = snake(a.app_label)

    target = (root / a.path) if a.path else (root / apps_root / name)
    rel = target.resolve().relative_to(root)
    module = ".".join(rel.parts)

    try:
        below = [x for x in rel.relative_to(apps_root).parts if x not in p["nested_container_dirs"]]
    except ValueError:
        below = [name]
    label = a.label or "_".join(below)
    cls = pascal(label)
    models = [pascal(m) for m in (a.models or [pascal(name)])]
    prefix = p["app_settings"].get("settings_key_prefix", "") if p["app_settings"] else ""
    settings_key = "_".join(x for x in (prefix, label.upper(), "SETTINGS") if x)

    if a.public and not p["tenancy"]:
        sys.exit("--public given but profile has no tenancy configured.")

    base_mod, base_cls = split_dotted(p["base_model"])
    ctx = {
        "profile": p, "module": module, "label": label, "cls": cls,
        "verbose": a.verbose_name or label.replace("_", " ").title(),
        "models": models, "public": a.public, "with_status": a.with_status,
        "base_cls": base_cls, "settings_key": settings_key,
        "swap_key": {m: f"{label.upper()}_{snake(m).upper()}_MODEL" for m in models},
    }

    print(f"Scaffolding '{label}' -> {rel}  (module {module}){'  [dry-run]' if a.dry_run else ''}")
    w = Writer(a.dry_run, a.force)

    w.write(target / "apps.py", gen_apps(ctx))
    if a.with_status:
        w.write(target / "constants.py", gen_constants(ctx))
    if p["app_settings"]:
        w.write(target / "app_settings.py", gen_app_settings(ctx))
    if p["swappable_models"]:
        if a.abstract_dir:
            for m in models:
                w.write(target / "models_abstract" / f"{snake(m)}.py", gen_models_abstract_file(ctx, m))
            init = "".join(f"from .{snake(m)} import Abstract{m}  # noqa: F401\n" for m in models)
            w.write(target / "models_abstract" / "__init__.py", init)
        else:
            w.write(target / "models_abstract.py", gen_models_abstract_single(ctx))
        w.write(target / "models.py", gen_models_concrete(ctx))
    else:
        w.write(target / "models.py", gen_models_plain(ctx))
    w.write(target / "__init__.py", gen_init(ctx))
    w.write(target / "admin.py", gen_admin(ctx))
    w.write(target / "Readme.md", gen_readme(ctx))

    # migrations routing
    mig = p["migrations"]
    if mig["mode"] == "external" and mig.get("root"):
        gen_dir = target / "migrations"
        if gen_dir.is_dir():
            contents = [f.name for f in gen_dir.iterdir() if f.name != "__pycache__"]
            if contents in ([], ["__init__.py"]):
                print(f"  - {'would remove' if a.dry_run else 'removed'} empty generated migrations/")
                if not a.dry_run:
                    import shutil
                    shutil.rmtree(gen_dir)
            else:
                print(f"  ! {gen_dir} has real migrations; NOT removed. Decide manually.")
        w.write(root / mig["root"] / label / "__init__.py", "")

    tests_dir = None
    if p["tests_root"]:
        tests_dir = f'{p["tests_root"]}/{label}'
        w.write(root / tests_dir / "__init__.py", "")
        w.write(root / tests_dir / "test_models.py", gen_test(ctx))

    # next steps
    print("\n== Next steps ==")
    reg = p["settings_registry_file"]
    lists = p["registry_lists"]
    print(f"1. Register in {reg or 'your settings (INSTALLED_APPS)'}:")
    const = f"{label.upper()}_APP"
    print(f'   {const} = "{module}"')
    if p["swappable_models"]:
        for m in models:
            print(f'   {ctx["swap_key"][m]} = "{label}.{m}"')
    print(f"   add {const} to {lists['all']}")
    if p["tenancy"]:
        lst = lists["public"] if a.public else lists["tenant"]
        if lst:
            print(f"   add {const} to {lst}")
    cmds = p["commands"]
    fmt = {"app_label": label, "module_path": module, "tests_dir": tests_dir or ""}
    print(f"2. Migrations: {cmds['makemigrations'].format(**fmt)}")
    if cmds.get("test"):
        print(f"3. Tests: {cmds['test'].format(**fmt)}")
    print(f"4. Validate: python {Path(__file__).parent / 'check_app.py'} {rel}"
          + (f" --profile {profile_path}" if profile_path else ""))
    print("5. Replace placeholder fields (name/status) in the abstract models.")
    if w.skipped:
        print(f"\n! {len(w.skipped)} existing file(s) left untouched. Use --force to overwrite.")


if __name__ == "__main__":
    main()
