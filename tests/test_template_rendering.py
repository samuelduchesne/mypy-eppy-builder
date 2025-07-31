from pathlib import Path

import pytest

jinja2 = pytest.importorskip("jinja2")
Environment = jinja2.Environment
FileSystemLoader = jinja2.FileSystemLoader

def test_pyproject_keywords(tmp_path: Path) -> None:
    templates_dir = Path("src/mypy_eppy_builder/templates")
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=True,
        keep_trailing_newline=True,
    )
    template = env.get_template("types-archetypal/pyproject.toml.jinja2")
    rendered = template.render(
        package={
            "data": {"pypi_name": "archetypal-stubs"},
            "version": "0.1.0",
            "description": "desc",
            "library_name": "archetypal",
        }
    )
    assert 'keywords = ["archetypal", "typing", "stubs"]' in rendered
