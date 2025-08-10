from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path
import os


def build_wheel(tmp_path: Path) -> Path:
    idd = tmp_path / "Energy+.idd"
    idd.write_text("! dummy idd")
    out_dir = tmp_path / "pkg"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy_eppy_builder.generate",
            "--energyplus-version",
            "23.1",
            "--idd-path",
            str(idd),
            "--out-dir",
            str(out_dir),
        ],
        check=True,
        env={**os.environ, "PYTHONPATH": str(Path.cwd() / "src")},
    )
    build_env = {
        **os.environ,
        "SETUPTOOLS_SCM_PRETEND_VERSION_FOR_EPPY_STUBS": "23.1.0",
        "SETUPTOOLS_SCM_PRETEND_VERSION": "23.1.0",
    }
    subprocess.run([sys.executable, "-m", "hatchling", "build", "-t", "wheel"], cwd=out_dir, check=True, env=build_env)
    return next((out_dir / "dist").glob("*.whl"))


def test_wheel_purity(tmp_path: Path) -> None:
    wheel_path = build_wheel(tmp_path)
    with zipfile.ZipFile(wheel_path) as zf:
        names = zf.namelist()
    assert "generated_by.json" in names
    assert "README.md" in names
    assert "eppy/__init__.pyi" in names
    assert all(name.endswith(".pyi") for name in names if name.startswith("eppy/"))
    assert all(not name.endswith(".py") for name in names if name.startswith("eppy/"))
    assert "py.typed" not in names
