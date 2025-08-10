from pathlib import Path

import pytest

jinja2 = pytest.importorskip("jinja2")
Environment = jinja2.Environment
FileSystemLoader = jinja2.FileSystemLoader


def test_class_stub_template() -> None:
    templates_dir = Path("src/mypy_eppy_builder/templates")
    env = Environment(loader=FileSystemLoader(templates_dir))
    tmpl = env.get_template("common/class_stub.pyi.jinja2")
    rendered = tmpl.render(
        classname="Zone",
        class_memo="Zone object",
        fields=[{"name": "Name", "type": "Annotated[str, Field()]", "note": "Zone name"}],
    )
    assert "class Zone(EpBunch)" in rendered
    assert "Name: Annotated[str, Field()]" in rendered
