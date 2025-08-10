from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_templates(out_dir: Path, ctx: dict[str, str]) -> None:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False,
        keep_trailing_newline=True,
        lstrip_blocks=True,
        trim_blocks=True,
    )
    (out_dir / "README.md").write_text(env.get_template("README.md.j2").render(ctx))
    eppy_dir = out_dir / "eppy"
    eppy_dir.mkdir(parents=True, exist_ok=True)
    (eppy_dir / "__init__.pyi").write_text(env.get_template("eppy/__init__.pyi.j2").render(ctx))
    # minimal stub to allow import in demo
    (eppy_dir / "modeleditor.pyi").write_text("...\n")


def write_generated_by(out_dir: Path, ctx: dict[str, str]) -> None:
    try:
        generator_version = metadata.version("mypy_eppy_builder")
    except metadata.PackageNotFoundError:
        generator_version = "0.0.0"
    data = {
        "energyplus_version": ctx["energyplus_version"] + ".0"
        if ctx["energyplus_version"].count(".") == 1
        else ctx["energyplus_version"],
        "idd_sha256": ctx["idd_sha256"],
        "generator_version": generator_version,
        "timestamp_utc": ctx["timestamp_utc"],
        "options": {"enum_style": "Literal", "docstrings": True},
    }
    (out_dir / "generated_by.json").write_text(json.dumps(data, indent=2))


def copy_pyproject(out_dir: Path) -> None:
    repo_pyproject = Path(__file__).parents[2] / "pyproject.toml"
    shutil.copy2(repo_pyproject, out_dir / "pyproject.toml")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--energyplus-version", required=True)
    parser.add_argument("--idd-path", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    idd_path = Path(args.idd_path)
    idd_sha256 = hashlib.sha256(idd_path.read_bytes()).hexdigest()
    timestamp_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    ctx = {
        "energyplus_version": args.energyplus_version,
        "idd_sha256": idd_sha256,
        "timestamp_utc": timestamp_utc,
    }
    render_templates(out_dir, ctx)
    write_generated_by(out_dir, ctx)
    copy_pyproject(out_dir)


if __name__ == "__main__":
    main()
