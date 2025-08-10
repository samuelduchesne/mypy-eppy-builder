"""CLI entry point for simplified two-package stub build.

Generates shared IDF object stubs once per EnergyPlus version and wraps
into two packages: ``eppy-stubs`` and ``archetypal-stubs`` whose versions
follow ``<EPLUS_MAJOR>.<EPLUS_MINOR>.<PATCH>`` (patch is for stub tooling
updates that do not change the underlying EnergyPlus object set).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .eppy_stubs_generator import EppyStubGenerator, classname_to_key

SHARED_ROOT = Path("generated_package/shared")
PACKAGES_ROOT = Path("generated_package")


@dataclass
class Manifest:
    eplus_version: str
    patch: int
    idd_sha256: str
    classnames: list[str]
    file_count: int

    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=2, sort_keys=True)

    @classmethod
    def from_path(cls, path: Path) -> Manifest | None:
        if not path.is_file():
            return None
        return cls(**json.loads(path.read_text()))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_shared_objects(idd_file: Path, eplus_version: str) -> tuple[Path, Manifest]:
    version_dir = SHARED_ROOT / eplus_version
    objects_dir = version_dir / "objects"
    manifest_path = version_dir / "manifest.json"
    objects_dir.mkdir(parents=True, exist_ok=True)

    idd_hash = sha256_file(idd_file)
    existing = Manifest.from_path(manifest_path)
    if existing and existing.idd_sha256 == idd_hash:
        # Reuse existing
        return objects_dir, existing

    generator = EppyStubGenerator(str(idd_file), str(objects_dir))
    generator.generate_stubs()

    classnames = sorted(p.stem for p in objects_dir.glob("*.pyi"))
    manifest = Manifest(
        eplus_version=eplus_version,
        patch=0,  # placeholder, patch pertains to package versioning
        idd_sha256=idd_hash,
        classnames=classnames,
        file_count=len(classnames),
    )
    manifest_path.write_text(manifest.to_json())
    return objects_dir, manifest


def write_package(
    package_type: str,
    eplus_version: str,
    patch: int,
    classnames: Iterable[str],
    shared_objects_dir: Path,
) -> Path:
    if package_type not in {"eppy", "archetypal"}:
        raise ValueError
    version = f"{eplus_version}.{patch}"
    pkg_name = f"{package_type}-stubs"
    pkg_slug = package_type
    pkg_root = PACKAGES_ROOT / f"{pkg_name}-{version}"
    src_root = pkg_root / "src" / pkg_slug
    objects_dest = src_root / "objects"
    objects_dest.mkdir(parents=True, exist_ok=True)

    # Copy objects (could optimize by comparing hash, small overhead OK)
    for p in shared_objects_dir.glob("*.pyi"):
        shutil.copy2(p, objects_dest / p.name)

    # Build idf.pyi (simple inline rendering)
    overloads = [(c, classname_to_key(c)) for c in classnames]
    idf_lines: list[str] = [
        "from __future__ import annotations",
        "from typing import Literal, overload, TypedDict",
        "from geomeppy.patches import EpBunch",
        "",
    ]
    # relative imports
    for c in classnames:
        idf_lines.append(f"from .objects.{c} import {c}")
    idf_lines.append("")
    idf_lines.append("IDFObjectsDict = TypedDict('IDFObjectsDict', {")
    for c, k in overloads:
        idf_lines.append(f"    '{k}': list[{c}],")
    idf_lines.append("})\n")
    idf_lines.append("class IDF:")
    idf_lines.append("    def __init__(self, *args, **kwargs) -> None: ...")
    for c, k in overloads:
        idf_lines.append("    @overload")
        idf_lines.append(f"    def newidfobject(self, key: Literal['{k}'], **kwargs) -> {c}: ...")
    idf_lines.append("    def newidfobject(self, key: str, **kwargs) -> EpBunch: ...")
    idf_lines.append("    @property")
    idf_lines.append("    def idfobjects(self) -> IDFObjectsDict: ...")
    (src_root / "idf.pyi").write_text("\n".join(idf_lines) + "\n")
    (src_root / "__init__.py").write_text("__all__ = ['IDF', 'IDFObjectsDict']\n")
    # Mark as a partial stub package (PEP 561) since runtime modules are not fully covered
    (src_root / "py.typed").write_text("partial\n")

    # Minimal pyproject
    pyproject = f"""[project]\nname = \"{pkg_name}\"\nversion = \"{version}\"\ndescription = \"EnergyPlus {eplus_version} type stubs for {package_type}\"\nrequires-python = \">=3.9,<4.0\"\nclassifiers = [\n    'Typing :: Stubs Only',\n    'Programming Language :: Python :: 3',\n]\n[build-system]\nrequires = ['hatchling']\nbuild-backend = 'hatchling.build'\n[tool.hatch.build.targets.wheel]\npackages = ['src/{pkg_slug}']\n"""
    (pkg_root / "pyproject.toml").write_text(pyproject)
    (pkg_root / "README.md").write_text(
        f"# {pkg_name}\n\nGenerated stubs for EnergyPlus {eplus_version}. Shared IDF objects set.\n"
    )
    return pkg_root


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build eppy-stubs and archetypal-stubs packages")
    p.add_argument("--eplus-version", required=True, help="EnergyPlus version like 23.1")
    p.add_argument("--idd-file", help="Path to Energy+.idd; if omitted, auto-detect via archetypal")
    p.add_argument("--patch", type=int, default=0, help="Patch number for stub package version")
    p.add_argument(
        "--packages",
        nargs="+",
        choices=["eppy", "archetypal"],
        default=["eppy", "archetypal"],
        help="Subset of packages to build",
    )
    return p.parse_args()


def main() -> None:  # pragma: no cover - thin CLI wrapper
    args = parse_args()
    eplus_version: str = args.eplus_version
    if args.idd_file:
        idd_file = Path(args.idd_file)
    else:
        # Local import to avoid forcing archetypal dependency at module import time
        from archetypal import EnergyPlusVersion  # type: ignore[import-not-found]

        idd_file = Path(EnergyPlusVersion(eplus_version).current_idd_path)  # type: ignore[arg-type]
    shared_dir, manifest = generate_shared_objects(idd_file, eplus_version)
    for pkg in args.packages:
        write_package(pkg, eplus_version, args.patch, manifest.classnames, shared_dir)


if __name__ == "__main__":  # pragma: no cover
    main()
