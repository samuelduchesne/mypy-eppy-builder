import sys
import types
from pathlib import Path

# Helper functions to emulate Jinja2 templates


def _render_class_stub(ctx: dict) -> str:
    lines = [
        "from typing import Annotated, Literal",
        "",
        "from pydantic import Field",
        "",
        "from geomeppy.patches import EpBunch",
        "",
        f"class {ctx['classname']}(EpBunch):",
    ]
    memo = ctx.get("class_memo")
    if memo:
        lines.append(f'    """{memo.strip()}"""')
    fields = ctx.get("fields", [])
    if fields:
        for field in fields:
            line = f"    {field['name']}: {field['type']}"
            field_call = field.get("field_call")
            if field_call:
                line += f" = {field_call}"
            lines.append(line)
            note = field.get("note")
            if note:
                lines.append(f'    """{note.strip()}"""')
    else:
        lines.append("    pass")
    return "\n".join(lines)


def _render_idf_template(ctx: dict) -> str:
    lines = [
        "from typing import Literal, TypedDict, overload",
        "",
        "from geomeppy.patches import EpBunch",
        "",
    ]
    for classname in ctx.get("classnames", []):
        lines.append(f"from eppy.{classname} import {classname}")
    lines.append("")
    lines.append("IDFObjectsDict = TypedDict('IDFObjectsDict', {")
    for overload in ctx.get("overloads", []):
        lines.append(f"    '{overload['key']}': list[{overload['classname']}],")
    lines.append("})")
    lines.append("")
    base_cls = ctx.get("base_class")
    if base_cls:
        lines.append(f"class IDF({base_cls}):")
    else:
        lines.append("class IDF:")
    version_cls = ctx.get("version_classname")
    ver = ctx.get("eplus_version")
    if version_cls and ver:
        lines.append("    @overload")
        lines.append(f"    def __init__(self: {version_cls}, *, as_version: Literal['{ver}'], **kwargs) -> None: ...")
        lines.append("    @overload")
        lines.append(f"    def __init__(self: {version_cls}, *, file_version: Literal['{ver}'], **kwargs) -> None: ...")
    lines.append("    def __init__(self, *args, **kwargs) -> None: ...")
    for overload in ctx.get("overloads", []):
        lines.append("")
        lines.append("    @overload")
        lines.append(
            f"    def newidfobject(self, key: Literal['{overload['key']}'], **kwargs) -> {overload['classname']}: ..."
        )
    lines.append("")
    lines.append("    def newidfobject(self, key: str, **kwargs) -> EpBunch: ...")
    lines.append("    @property")
    lines.append("    def idfobjects(self) -> IDFObjectsDict: ...")
    if version_cls:
        lines.append("")
        lines.append(f"class {version_cls}(IDF):")
        lines.append("    pass")
    return "\n".join(lines)


# Dummy Jinja2 substitute
class DummyTemplate:
    def __init__(self, name: str) -> None:
        self.name = name

    def render(self, **context: dict) -> str:
        if self.name.endswith("class_stub.pyi.jinja2"):
            return _render_class_stub(context)
        if self.name.endswith("idf.pyi.jinja2"):
            return _render_idf_template(context)
        return ""


class DummyEnv:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def get_template(self, name: str) -> DummyTemplate:
        return DummyTemplate(name)


# Dummy archetypal.idfclass.IDF implementation
class DummyIDF:
    def __init__(self) -> None:
        pass

    @property
    def idd_info(self):
        return [
            [],
            [
                {"idfobj": "Zone", "memo": ["Zone object"]},
                {"field": ["Name"], "type": ["alpha"], "note": ["Zone name"]},
                {"field": ["Multiplier"], "type": ["real"], "default": ["1.0"]},
            ],
            [
                {"idfobj": "Material", "memo": ["Material object"]},
                {"field": ["Name"], "type": ["alpha"]},
                {"field": ["Roughness"], "type": ["choice"], "key": ["Smooth", "Rough"]},
                {"field": ["Thickness"], "type": ["real"], "default": ["0.1"], "minimum>": ["0"], "maximum<": ["10"]},
            ],
        ]


def setup_module(module) -> None:
    """Insert dummy dependencies for tests."""
    # archetypal stub
    archetypal = types.ModuleType("archetypal")
    idfclass = types.ModuleType("archetypal.idfclass")
    idfclass.IDF = DummyIDF
    archetypal.idfclass = idfclass
    sys.modules["archetypal"] = archetypal
    sys.modules["archetypal.idfclass"] = idfclass

    # jinja2 stub
    class DummyLoader:
        def __init__(self, *args, **kwargs) -> None:
            pass

    jinja2_mod = types.ModuleType("jinja2")
    jinja2_mod.Environment = DummyEnv
    jinja2_mod.FileSystemLoader = DummyLoader
    sys.modules["jinja2"] = jinja2_mod


def teardown_module(module) -> None:
    for mod in ["archetypal.idfclass", "archetypal", "jinja2"]:
        sys.modules.pop(mod, None)


def test_generate_stubs_and_overloads(tmp_path: Path) -> None:
    from mypy_eppy_builder.eppy_stubs_generator import (
        EppyStubGenerator,
    )

    generator = EppyStubGenerator("dummy.idd", str(tmp_path))
    generator.env = DummyEnv()
    generator.generate_stubs()

    zone_stub = (tmp_path / "Zone.pyi").read_text()
    material_stub = (tmp_path / "Material.pyi").read_text()

    assert "class Zone(EpBunch)" in zone_stub
    assert "Name: Annotated[str, Field()]" in zone_stub
    assert "Multiplier: Annotated[float, Field(default=1.0)]" in zone_stub

    assert "class Material(EpBunch)" in material_stub
    assert "Roughness: Annotated[Literal['Smooth', 'Rough'], Field()]" in material_stub
    assert "Thickness: Annotated[float, Field(gt=0, lt=10, default=0.1)]" in material_stub

    context = {
        "classnames": ["Zone", "Material"],
        "overloads": [
            {"classname": "Zone", "key": "ZONE"},
            {"classname": "Material", "key": "MATERIAL"},
        ],
        "version_classname": "IDF_23_1",
        "eplus_version": "23.1",
    }
    overload_content = _render_idf_template(context)
    assert "def newidfobject(self, key: Literal['ZONE'], **kwargs) -> Zone" in overload_content
    assert "class IDF_23_1(IDF)" in overload_content


def test_normalize_classname_preserves_camel_case() -> None:
    from mypy_eppy_builder.eppy_stubs_generator import (
        EppyStubGenerator,
        classname_to_key,
    )

    generator = EppyStubGenerator("dummy.idd", "out")

    name = "BuildingSurface:Detailed"
    assert generator.normalize_classname(name) == "BuildingSurface_Detailed"
    assert classname_to_key("BuildingSurface_Detailed") == "BUILDINGSURFACE:DETAILED"
