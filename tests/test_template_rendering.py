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


def test_pyproject_extras(tmp_path: Path) -> None:
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
            "extras": [{"name": "eplus23_1", "package": "types_archetypal_eplusV231"}],
        }
    )
    assert 'eplus23_1 = ["types_archetypal_eplusV231"]' in rendered


def _env() -> Environment:
    templates_dir = Path("src/mypy_eppy_builder/templates")
    return Environment(
        loader=FileSystemLoader(templates_dir),
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=True,
        keep_trailing_newline=True,
    )


def test_modeleditor_template() -> None:
    env = _env()
    template = env.get_template(
        "common/modeleditor.pyi.jinja2",
    )
    rendered = template.render(
        package={"epbunch_path": "geomeppy.patches", "data": {"pypi_stubs_name": "pkg"}},
        classnames=["Zone"],
        overloads=[("Zone", "ZONE")],
    )
    assert 'def popidfobject(self, key: Literal["ZONE"], index: int) -> Zone' in rendered


def test_geomeppy_idf_template() -> None:
    env = _env()
    template = env.get_template("common/geomeppy/idf.pyi.jinja2")
    rendered = template.render(package={"epbunch_path": "geomeppy.patches"})
    assert "def getsurfaces" in rendered


def test_archetypal_idf_extra_methods() -> None:
    env = _env()
    template = env.get_template(
        "types-archetypal/src/archetypal-stubs/idfclass/idf.pyi.jinja2",
    )
    rendered = template.render(
        package={"epbunch_path": "geomeppy.patches", "data": {"pypi_stubs_name": "pkg"}},
        classnames=["Zone"],
        overloads=[("Zone", "ZONE")],
    )
    assert "def addidfobject" in rendered


def test_versioned_idf_overloads() -> None:
    env = _env()
    template = env.get_template(
        "types-eppy/src/eppy-stubs/idfclass/idf.pyi.jinja2",
    )
    rendered = template.render(
        package={"epbunch_path": "geomeppy.patches", "data": {"pypi_stubs_name": "pkg"}},
        classnames=[],
        overloads=[],
        version_classname="IDF_23_1",
        eplus_version="23.1",
    )
    assert "class IDF_23_1(IDF)" in rendered
    assert 'def __init__(self: IDF_23_1, *, as_version: Literal["23.1"]' in rendered
