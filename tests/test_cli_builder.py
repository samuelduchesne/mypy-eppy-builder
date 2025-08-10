from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

# Ensure package importable without installation
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))


class DummyIDF:
    def __init__(self) -> None:  # pragma: no cover - trivial
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
            ],
        ]


@pytest.fixture(autouse=True)
def _inject_modules(monkeypatch):
    archetypal = types.ModuleType("archetypal")
    idfclass = types.ModuleType("archetypal.idfclass")
    idfclass.IDF = DummyIDF  # type: ignore[attr-defined]
    archetypal.idfclass = idfclass  # type: ignore[attr-defined]

    class _EPV:  # minimal stand-in
        def __init__(self, version: str) -> None:  # pragma: no cover - trivial
            self.version = version

        @property
        def current_idd_path(self) -> str:  # pragma: no cover
            # Raised if production path resolution is unexpectedly invoked.
            raise RuntimeError

    archetypal.EnergyPlusVersion = _EPV  # type: ignore[attr-defined]
    sys.modules["archetypal"] = archetypal
    sys.modules["archetypal.idfclass"] = idfclass
    yield
    for mod in ["archetypal.idfclass", "archetypal"]:
        sys.modules.pop(mod, None)


def test_generate_shared_and_packages(tmp_path: Path, monkeypatch) -> None:
    # Create a fake IDD file (content not parsed by dummy, only hashed)
    idd_file = tmp_path / "Energy+.idd"
    idd_file.write_text("! dummy idd\n")

    monkeypatch.chdir(tmp_path)

    # Late import after stubbing
    from mypy_eppy_builder.cli import generate_shared_objects, write_package

    shared_dir, manifest = generate_shared_objects(idd_file, "23.1")
    assert shared_dir.exists()
    manifest_path = shared_dir.parent / "manifest.json"
    assert manifest_path.exists()
    data = json.loads((shared_dir.parent / "manifest.json").read_text())
    assert data["eplus_version"] == "23.1"
    assert sorted(manifest.classnames) == ["Material", "Zone"]

    pkg_dir = write_package("eppy", "23.1", 0, manifest.classnames, shared_dir)
    assert (pkg_dir / "pyproject.toml").is_file()
    idf_file = pkg_dir / "src" / "eppy_stubs" / "idf.pyi"
    assert "class IDF:" in idf_file.read_text()
    py_typed = (pkg_dir / "src" / "eppy_stubs" / "py.typed").read_text().strip()
    assert py_typed == "partial"
    # second package
    pkg_dir2 = write_package("archetypal", "23.1", 1, manifest.classnames, shared_dir)
    pyproj_lines = (pkg_dir2 / "pyproject.toml").read_text().splitlines()
    assert any(line.strip() == 'version = "23.1.1"' for line in pyproj_lines)
