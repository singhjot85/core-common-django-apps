#!/usr/bin/env python3
"""Static convention checker for a scaffolded Django app. Exit 1 on violations.

Usage: check_app.py <app_dir> [--profile project.profile.json] [--root .]
Checks are driven by the profile (swappable models, migrations mode, app_settings).
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

SKIP_CONCRETE_IMPORT_IN = {"models.py", "tests.py"}


def load_profile(path: str | None) -> dict:
    cands = [Path(path)] if path else [
        Path(__file__).resolve().parent.parent / "project.profile.json",
        Path.cwd() / "project.profile.json",
    ]
    for c in cands:
        if c.is_file():
            return json.loads(c.read_text())
    return {}


def py_files(app: Path):
    for f in app.rglob("*.py"):
        if "migrations" in f.parts or "__pycache__" in f.parts:
            continue
        yield f


def check(app: Path, prof: dict, root: Path) -> list[str]:
    errs: list[str] = []
    swap = prof.get("swappable_models", False)
    mig = prof.get("migrations", {"mode": "in_app"})
    label = None
    app_module = ".".join(app.resolve().relative_to(root).parts)

    # apps.py
    apps_py = app / "apps.py"
    if not apps_py.exists():
        errs.append("apps.py missing")
    else:
        src = apps_py.read_text()
        for attr in ("name", "label"):
            if not re.search(rf'^\s+{attr}\s*=\s*"[^"]+"', src, re.M):
                errs.append(f"apps.py: `{attr}` not set to a string literal")
        m = re.search(r'label\s*=\s*"([^"]+)"', src)
        label = m.group(1) if m else None
        nm = re.search(r'name\s*=\s*"([^"]+)"', src)
        if nm and nm.group(1).replace(".", "/") != str(app.resolve().relative_to(root)).replace("\\", "/"):
            errs.append(f"apps.py: name '{nm.group(1)}' does not match directory {app}")

    # migrations
    if mig.get("mode") == "external":
        if (app / "migrations").exists():
            errs.append("migrations/ must not exist inside the app (external migration routing)")
        if label and mig.get("root") and not (root / mig["root"] / label / "__init__.py").exists():
            errs.append(f"missing {mig['root']}/{label}/__init__.py")

    # app_settings
    s = app / "app_settings.py"
    if prof.get("app_settings") and s.exists():
        tree = ast.parse(s.read_text())
        classes = {n.name for n in tree.body if isinstance(n, ast.ClassDef) and n.name.endswith("Settings")}
        for n in tree.body:
            if isinstance(n, (ast.Assign, ast.AnnAssign)):
                v = n.value
                if isinstance(v, ast.Call) and getattr(v.func, "id", None) in classes:
                    errs.append("app_settings.py: settings class instantiated at module level; do it in __init__.py")
        for n in tree.body:
            if isinstance(n, ast.ClassDef) and n.name in classes:
                first = next((b for b in n.body if not isinstance(b, ast.Expr)), None)
                is_key = isinstance(first, ast.Assign) and getattr(first.targets[0], "id", "") == "SETTINGS_KEY"
                if not is_key:
                    errs.append(f"app_settings.py: SETTINGS_KEY must be first attribute of {n.name}")
        init = app / "__init__.py"
        if init.exists() and "Settings()" not in init.read_text():
            errs.append("__init__.py: app_settings singleton not instantiated")

    if swap:
        # concrete models: no fields, swappable set
        mp = app / "models.py"
        if mp.exists():
            tree = ast.parse(mp.read_text())
            for n in tree.body:
                if not isinstance(n, ast.ClassDef):
                    continue
                for b in n.body:
                    if isinstance(b, (ast.Assign, ast.AnnAssign)):
                        errs.append(f"models.py: {n.name} defines attributes/fields; move to abstract model")
                    if isinstance(b, ast.FunctionDef):
                        errs.append(f"models.py: {n.name}.{b.name}() defined; move to abstract model")
                meta = next((b for b in n.body if isinstance(b, ast.ClassDef) and b.name == "Meta"), None)
                has_swap = meta and any(
                    isinstance(x, ast.Assign) and getattr(x.targets[0], "id", "") == "swappable" for x in meta.body)
                if not has_swap:
                    errs.append(f"models.py: {n.name}.Meta.swappable not set")

        # no concrete imports elsewhere
        pat = re.compile(r"^\s*from\s+(\.|[\w.]+)\s*(?:\.models|import\s+models)\b|^\s*from\s+\.models\s+import", re.M)
        for f in py_files(app):
            if f.name in SKIP_CONCRETE_IMPORT_IN or "tests" in f.parts:
                continue
            for m in re.finditer(r"^\s*from\s+(\S+)\s+import\s+(.+)$", f.read_text(), re.M):
                mod = m.group(1)
                own = f"{app_module}.models" if app_module else None
                if mod == ".models" or (own and mod == own):
                    errs.append(f"{f.relative_to(app)}: imports concrete models from '{mod}'; use get_<model>_model()")

        # FK to class
        for f in py_files(app):
            try:
                tree = ast.parse(f.read_text())
            except SyntaxError as e:
                errs.append(f"{f.name}: syntax error {e}")
                continue
            for n in ast.walk(tree):
                if isinstance(n, ast.Call) and getattr(n.func, "attr", "") in ("ForeignKey", "OneToOneField", "ManyToManyField"):
                    target = n.args[0] if n.args else next((k.value for k in n.keywords if k.arg == "to"), None)
                    if isinstance(target, ast.Name):
                        errs.append(f"{f.relative_to(app)}:{n.lineno}: relation to class '{target.id}'; use a settings string")
    return errs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("app_dir")
    ap.add_argument("--profile")
    ap.add_argument("--root", default=".")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    app = (root / a.app_dir).resolve()
    if not app.is_dir():
        sys.exit(f"Not a directory: {app}")
    errs = check(app, load_profile(a.profile), root)
    if errs:
        print(f"{len(errs)} violation(s):")
        for e in errs:
            print(f"  x {e}")
        sys.exit(1)
    print("OK: no convention violations found.")


if __name__ == "__main__":
    main()
