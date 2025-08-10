from __future__ import annotations

import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

from mypy_eppy_builder.eppy_stubs_generator import EppyStubGenerator

pytest.importorskip("mypy")


def test_mypy_type_checks(tmp_path: Path):
    """Generate minimal stubs in-process and run mypy over a usage sample."""

    class DummyIDF:  # minimal idd_info for generator
        @property
        def idd_info(self):
            return [
                [],
                [
                    {"idfobj": "Zone", "memo": ["Zone object"]},
                    {"field": ["Name"], "type": ["alpha"], "note": ["Zone name"]},
                ],
            ]

    # Stub external modules required by generator
    archetypal = types.ModuleType("archetypal")
    idfclass = types.ModuleType("archetypal.idfclass")
    idfclass.IDF = DummyIDF  # type: ignore[attr-defined]
    archetypal.idfclass = idfclass  # type: ignore[attr-defined]
    sys.modules["archetypal"] = archetypal
    sys.modules["archetypal.idfclass"] = idfclass

    geomeppy = types.ModuleType("geomeppy")
    patches = types.ModuleType("geomeppy.patches")

    class EpBunch:  # placeholder
        pass

    patches.EpBunch = EpBunch  # type: ignore[attr-defined]
    geomeppy.patches = patches  # type: ignore[attr-defined]
    sys.modules["geomeppy"] = geomeppy
    sys.modules["geomeppy.patches"] = patches

    pkg_root = tmp_path / "eppy_stubs"
    objects_dir = pkg_root / "objects"
    objects_dir.mkdir(parents=True)

    gen = EppyStubGenerator("dummy.idd", str(objects_dir), idf_cls=DummyIDF)
    gen.generate_stubs()

    # Build minimal idf.pyi referencing Zone
    (pkg_root / "idf.pyi").write_text(
        "from typing import Literal, overload, TypedDict\n"
        "from geomeppy.patches import EpBunch\n"
        "from .objects.Zone import Zone\n\n"
        "IDFObjectsDict = TypedDict('IDFObjectsDict', {'ZONE': list[Zone]})\n\n"
        "class IDF:\n"
        "    @overload\n    def newidfobject(self, key: Literal['ZONE'], **kwargs) -> Zone: ...\n"
        "    def newidfobject(self, key: str, **kwargs) -> EpBunch: ...\n"
    )
    (pkg_root / "__init__.py").write_text("__all__=['IDF']\n")
    (pkg_root / "py.typed").write_text("partial\n")

    sample = tmp_path / "sample.py"
    sample.write_text("from eppy_stubs.idf import IDF\nidf = IDF()\nz = idf.newidfobject('ZONE')\nreveal_type(z)\n")

    env = {**os.environ, "PYTHONPATH": str(tmp_path)}
    # Invoke mypy via sys.executable -m to avoid relying on PATH lookup (S607) and
    # we control inputs here (trusted test sample) mitigating S603 concerns.
    result = subprocess.run(  # noqa: S603 - controlled test code; S607 not applicable using sys.executable
        [sys.executable, "-m", "mypy", str(sample)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        check=False,
    )
    out = result.stdout
    assert "error" not in out.lower(), out
    assert "Revealed type" in out and "Zone" in out, out
