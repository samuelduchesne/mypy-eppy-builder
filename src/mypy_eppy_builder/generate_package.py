from __future__ import annotations

import argparse
import os
from pathlib import Path

from archetypal import EnergyPlusVersion
from jinja2 import Environment, FileSystemLoader

from mypy_eppy_builder.eppy_stubs_generator import EppyStubGenerator, classname_to_key

# Set up paths
TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parents[2] / "generated_package"


def render_templates(
    template_files: list[Path],
    context: dict | None = None,
    *,
    output_base: Path = OUTPUT_DIR,
    template_base: Path = TEMPLATES_DIR,
) -> None:
    """Render Jinja templates to ``output_base`` preserving relative layout."""
    # Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(template_base),
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=True,
        keep_trailing_newline=True,
    )
    for template_file in template_files:
        # Compute relative path and destination
        rel_template_path = template_file.relative_to(template_base)
        rendered_rel_path = env.from_string(str(rel_template_path.parent)).render(context)

        # Render file name (remove '.jinja2' extension)
        rendered_file_name = env.from_string(template_file.name.replace(".jinja2", "")).render(context)

        output_path = Path(output_base) / rendered_rel_path / rendered_file_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Render and write file content
        template = env.get_template(str(rel_template_path))
        rendered_content = template.render(context)

        with open(output_path, "w") as f:
            f.write(rendered_content)


def get_version() -> str:
    import importlib.metadata

    try:
        return importlib.metadata.version("mypy_eppy_builder")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate typing package")
    parser.add_argument(
        "--version",
        default="23.1",
        help="EnergyPlus version (e.g. 23.1)",
    )
    parser.add_argument(
        "--idd-file",
        help="Path to Energy+.idd file to use",
    )
    parser.add_argument(
        "--package-type",
        choices=["archetypal", "eppy"],
        default="archetypal",
        help="Which package templates to render",
    )
    args = parser.parse_args()

    extras: list[dict[str, str]] = []

    classnames: list[str] = []
    overloads: list[tuple[str, str]] = []
    eplus_version = args.version
    version_classname = f"IDF_{eplus_version.replace('.', '_')}"
    last_package_slug = ""
    last_stubs_output_dir = Path()

    version_pkg_template_dir = TEMPLATES_DIR / "version-package"
    version_pkg_templates = list(version_pkg_template_dir.rglob("*.jinja2"))

    version_digits = "".join(ch for ch in eplus_version if ch.isdigit())
    package_name = f"types-eplus{version_digits}"
    package_slug = f"types_eplus{version_digits}"
    extras.append({
        "name": f"eplus{eplus_version.replace('.', '')}",
        "package": package_name,
        "path": f"../{package_name}",
    })

    idd_file = args.idd_file or os.environ.get("EPPY_IDD_FILE") or EnergyPlusVersion(eplus_version).current_idd_path

    pkg_root = OUTPUT_DIR / package_name
    stubs_output_dir = pkg_root / "src" / package_slug
    stubs_output_dir.mkdir(parents=True, exist_ok=True)

    generator = EppyStubGenerator(idd_file, str(stubs_output_dir))
    generator.generate_stubs()

    render_templates(
        version_pkg_templates,
        {
            "package_name": package_slug,
            "eplus_version": eplus_version,
            "builder_package_name": "mypy_eppy_builder",
            "builder_version": get_version(),
            "builder_repo_url": "https://github.com/samuelduchesne/mypy-eppy-builder",
        },
        output_base=pkg_root,
        template_base=version_pkg_template_dir,
    )

    last_package_slug = package_slug
    last_stubs_output_dir = stubs_output_dir
    for stub_file in sorted(stubs_output_dir.glob("*.pyi")):
        classname = stub_file.stem
        classnames.append(classname)
        ep_key = classname_to_key(classname)
        overloads.append((classname, ep_key))

    template_dir = TEMPLATES_DIR / f"types-{args.package_type}"
    template_files = list(template_dir.rglob("*.jinja2"))

    # --- 3. Prepare context for templates ---
    if args.package_type == "archetypal":
        package_ctx = {
            "epbunch_path": "eppy.bunch_subclass",
            "package_slug": last_package_slug,
            "extras": extras,
            "min_python_version": "3.9",
            "library_name": "archetypal",
            "library_version": eplus_version,
            "pypi_name": "types-archetypal",
            "version": "0.1.0",
            "description": "Eppy type stubs for the archetypal package",
            "setup_package_data": {
                "types-archetypal": ["*.pyi", "*.md"],
            },
            "url": {
                "pypi": "https://pypi.org/project/types-archetypal/",
                "github": "https://github.com/samueld/mypy-eppy-builder",
                "rtd_badge": "https://img.shields.io/badge/Material_for_MkDocs-526CFE?style=for-the-badge&logo=MaterialForMkDocs&logoColor=white",
                "docs": "https://types-archetypal.readthedocs.io/",
            },
            "data": {
                "pypi_name": "archetypal-stubs",
                "pypi_stubs_name": last_package_slug,
            },
        }
    else:
        package_ctx = {
            "epbunch_path": "eppy.bunch_subclass",
            "package_slug": last_package_slug,
            "extras": extras,
            "min_python_version": "3.9",
            "library_name": "eppy",
            "library_version": eplus_version,
            "pypi_name": "types-eppy",
            "version": "0.1.0",
            "description": "Eppy type stubs for the eppy package",
            "setup_package_data": {
                "types-eppy": ["*.pyi", "*.md"],
            },
            "url": {
                "pypi": "https://pypi.org/project/types-eppy/",
                "github": "https://github.com/samueld/mypy-eppy-builder",
                "rtd_badge": "https://img.shields.io/badge/Material_for_MkDocs-526CFE?style=for-the-badge&logo=MaterialForMkDocs&logoColor=white",
                "docs": "https://types-eppy.readthedocs.io/",
            },
            "data": {
                "pypi_name": "eppy-stubs",
                "pypi_stubs_name": last_package_slug,
            },
        }

    context = {
        "package": package_ctx,
        "builder_repo_url": "https://github.com/samuelduchesne/mypy-eppy-builder",
        "classnames": classnames,
        "overloads": overloads,
        "stubs_output_dir": str(last_stubs_output_dir),
        "builder_package_name": "mypy_eppy_builder",
        "builder_version": get_version(),
        "eplus_version": eplus_version,
        "version_classname": version_classname,
    }
    render_templates(template_files, context)

    # Lint/fix the generated packages (requires ruff installed)
    try:
        import subprocess

        # Apply auto-fixes, but do not error on remaining violations
        subprocess.run(["ruff", "check", str(pkg_root), "--fix-only"], check=True)  # noqa: S603, S607
        wrapper_dir = OUTPUT_DIR / package_ctx["pypi_name"]
        subprocess.run(["ruff", "check", str(wrapper_dir), "--fix-only"], check=True)  # noqa: S603, S607
    except FileNotFoundError:
        print("Warning: ruff not found; skipping lint on generated packages.")


if __name__ == "__main__":
    main()
