import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Set up paths
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "generated_package")

# List of template files to render (relative to TEMPLATES_DIR)
TEMPLATE_FILES = Path(TEMPLATES_DIR).rglob("*.jinja2")

# Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), trim_blocks=True, lstrip_blocks=True, autoescape=True)


def render_templates(context=None):
    context = context or {}
    for template_path in TEMPLATE_FILES:
        template = env.get_template(str(template_path))
        output_content = template.render(**context)
        # Remove .jinja2 extension for output
        output_rel_path = template_path.replace(".jinja2", "")
        output_path = os.path.join(OUTPUT_DIR, output_rel_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_content)
        print(f"Generated: {output_path}")


def main():
    # You can customize the context here or load from a file
    context = {}
    render_templates(context)


if __name__ == "__main__":
    main()
