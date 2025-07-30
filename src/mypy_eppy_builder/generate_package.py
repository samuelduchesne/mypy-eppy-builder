import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from mypy_eppy_builder.eppy_stubs_generator import EppyStubGenerator, classname_to_key

# Set up paths
TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parents[2] / "generated_package"

# List of template files to render (relative to TEMPLATES_DIR)
TEMPLATE_FILES = [path for path in TEMPLATES_DIR.rglob("*.jinja2") if "common" not in path.parts]

# Jinja2 environment
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=True,
    keep_trailing_newline=True,
)


def render_templates(context=None):
    context = context or {}
    for template_path in TEMPLATE_FILES:
        template = env.get_template(str(template_path.relative_to(TEMPLATES_DIR)))
        output_content = template.render(**context)
        # Remove .jinja2 extension for output
        output_rel_path = str(template_path).replace(".jinja2", "")
        output_path = OUTPUT_DIR / Path(output_rel_path).relative_to(TEMPLATES_DIR)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_content)
        print(f"Generated: {output_path}")


def get_version():
    import importlib.metadata

    try:
        return importlib.metadata.version("mypy_eppy_builder")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


def main():
    # --- 1. Generate Eppy stubs ---
    # These could be parameterized or loaded from config/CLI
    idd_file = os.environ.get("EPPY_IDD_FILE") or "/Applications/EnergyPlus-23-1-0/Energy+.idd"
    stubs_output_dir = OUTPUT_DIR / "types_eppy_eplusV231"
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
    context = {
        "package": {
            "epbunch_path": "geomeppy.patches",
            "package_slug": "types_eppy_eplusV231",
            "min_python_version": "3.9",
            "library_name": "archetypal",
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
                "pypi_stubs_name": "types_eppy_eplusV231",
            },
        },
        "builder_repo_url": "https://github.com/samuelduchesne/mypy-eppy-builder",
        "classnames": classnames,
        "overloads": overloads,
        "stubs_output_dir": str(stubs_output_dir),
        "builder_package_name": "mypy_eppy_builder",
        "builder_version": get_version(),
    }
    render_templates(context)


if __name__ == "__main__":
    main()
