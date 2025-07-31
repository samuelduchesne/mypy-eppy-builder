import argparse
import os
from pathlib import Path
from typing import cast

from archetypal import EnergyPlusVersion
from jinja2 import Environment, FileSystemLoader

from mypy_eppy_builder.eppy_stubs_generator import EppyStubGenerator, classname_to_key

# Set up paths
TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parents[2] / "generated_package"


# Jinja2 environment
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=True,
    keep_trailing_newline=True,
)


def render_templates(template_files: list[Path], context: dict | None = None) -> None:
    context = context or {}
    for template_path in template_files:
        template = env.get_template(str(template_path.relative_to(TEMPLATES_DIR)))
        output_content = cast(str, template.render(**context))
        # Remove .jinja2 extension for output
        output_rel_path = str(template_path).replace(".jinja2", "")
        output_path = OUTPUT_DIR / Path(output_rel_path).relative_to(TEMPLATES_DIR)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_content)
        print(f"Generated: {output_path}")


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

    eplus_version = args.version

    version_digits = "".join(ch for ch in eplus_version if ch.isdigit())
    package_slug = f"types_eppy_eplusV{version_digits}"
    version_slug = f"eplus{eplus_version.replace('.', '_')}"
    version_classname = f"IDF_{eplus_version.replace('.', '_')}"
    extras = [{"name": version_slug, "package": package_slug}]

    idd_file = args.idd_file or os.environ.get("EPPY_IDD_FILE") or EnergyPlusVersion(eplus_version).current_idd_path

    template_dir = TEMPLATES_DIR / f"types-{args.package_type}"
    template_files = list(template_dir.rglob("*.jinja2"))

    # --- 1. Generate Eppy stubs ---
    stubs_output_dir = OUTPUT_DIR / package_slug
    stubs_output_dir.mkdir(parents=True, exist_ok=True)

    generator = EppyStubGenerator(idd_file, str(stubs_output_dir))
    generator.generate_stubs()

    # --- 2. Collect classnames and overloads for template context ---
    classnames = []
    overloads = []
    for stub_file in sorted(stubs_output_dir.glob("*.pyi")):
        classname = stub_file.stem
        classnames.append(classname)
        ep_key = classname_to_key(classname)
        overloads.append((classname, ep_key))

    # --- 3. Prepare context for templates ---
    if args.package_type == "archetypal":
        package_ctx = {
            "epbunch_path": "geomeppy.patches",
            "package_slug": package_slug,
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
                "pypi_stubs_name": package_slug,
            },
        }
    else:
        package_ctx = {
            "epbunch_path": "eppy.modeledditor",
            "package_slug": package_slug,
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
                "pypi_stubs_name": package_slug,
            },
        }

    context = {
        "package": package_ctx,
        "builder_repo_url": "https://github.com/samuelduchesne/mypy-eppy-builder",
        "classnames": classnames,
        "overloads": overloads,
        "stubs_output_dir": str(stubs_output_dir),
        "builder_package_name": "mypy_eppy_builder",
        "builder_version": get_version(),
        "eplus_version": eplus_version,
        "version_classname": version_classname,
    }
    render_templates(template_files, context)


if __name__ == "__main__":
    main()
