import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Set up paths
TEMPLATES_DIR = Path(__file__).parent / "templates"
OUTPUT_DIR = Path(__file__).parents[2] / "generated_package"

# List of template files to render (relative to TEMPLATES_DIR)
TEMPLATE_FILES = [path for path in TEMPLATES_DIR.rglob("*.jinja2") if "common" not in path.parts]

# Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), trim_blocks=True, lstrip_blocks=True, autoescape=True)


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


def main():
    # You can customize the context here or load from a file
    context = {
        "package": {
            "pypi_name": "mypy-eppy-builder",
            "version": "0.1.0",
            "description": "A builder for mypy stubs for Eppy",
            "setup_package_data": {
                "mypy_eppy_builder": ["*.pyi", "*.md"],
            },
            "url": {
                "pypi": "https://pypi.org/project/mypy-eppy-builder/",
                "github": "https://github.com/samueld/mypy-eppy-builder",
                "docs": "https://mypy-eppy-builder.readthedocs.io/",
            },
            "data": {
                "pypi_stubs_name": "types-archetypal",
            },
        },
    }
    render_templates(context)


if __name__ == "__main__":
    main()
