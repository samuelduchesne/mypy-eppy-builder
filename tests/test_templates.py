from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def test_readme_template_renders(tmp_path: Path) -> None:
    env = Environment(
        loader=FileSystemLoader("src/mypy_eppy_builder/templates"),
        autoescape=False,
        keep_trailing_newline=True,
        lstrip_blocks=True,
        trim_blocks=True,
    )
    ctx = {"energyplus_version": "23.1", "idd_sha256": "deadbeef", "timestamp_utc": "2025-08-10T11:00:00Z"}
    text = env.get_template("README.md.j2").render(ctx)
    assert "eppy-stubs==23.1.*" in text


def test_init_pyi_template_renders(tmp_path: Path) -> None:
    env = Environment(loader=FileSystemLoader("src/mypy_eppy_builder/templates"), autoescape=False)
    ctx = {"energyplus_version": "23.1", "idd_sha256": "deadbeef", "timestamp_utc": "2025-08-10T11:00:00Z"}
    text = env.get_template("eppy/__init__.pyi.j2").render(ctx)
    assert "EnergyPlus 23.1" in text
