# Copilot Instructions for mypy-eppy-builder

## Project Overview
- **Purpose:** Automates generation of type stubs for the Eppy library, enabling static type checking and IDE autocompletion for EnergyPlus IDF workflows.
- **Key Components:**
  - `src/mypy_eppy_builder/eppy_stubs_generator.py`: Parses IDD files and generates `.pyi` stubs for Eppy objects. Also generates overloads for the `IDF` class.
  - `src/mypy_eppy_builder/generate_package.py`: Renders Jinja2 templates (including overloads for `IDF`) into the `generated_package/` directory, using context from generated stubs.
  - `src/mypy_eppy_builder/templates/`: Contains Jinja2 templates for all generated files, including `idf.pyi.jinja2` for overloads.
  - `generated_package/`: Output directory for all generated stubs and package files.

## Developer Workflows
- **Environment Setup:**
  - Use `make install` to set up the environment and pre-commit hooks (requires `uv`).
  - Use `make check` to run linting, mypy, and dependency checks.
  - Use `make test` to run tests with coverage.
  - Use `make build` and `make publish` for packaging and publishing.
- **Stub Generation:**
  - Run `eppy_stubs_generator.py` to generate `.pyi` stubs from an IDD file.
  - Run `generate_package.py` to render all templates, including overloads for the `IDF` class, using the generated stubs as context.
- **CI/CD:**
  - GitHub Actions run on PR, push, and release. Formatting and type checks are enforced via pre-commit and CI.

## Project Conventions & Patterns
- **Templates:**
  - All generated files are based on Jinja2 templates in `src/mypy_eppy_builder/templates/`.
  - The `idf.pyi.jinja2` template expects `classnames` and `overloads` context, derived from the generated stubs.
- **Naming:**
  - Classnames are normalized (non-alphanumeric replaced with `_`, title-cased) to match Eppy conventions.
  - Overload keys are colon-separated, uppercased versions of classnames (see `classname_to_key`).
- **Generated Code:**
  - All generated files are written to `generated_package/`.
  - Do not manually edit generated files; edit templates or source scripts instead.

## External Dependencies
- **archetypal**: Used for parsing IDD files and extracting object/field info.
- **jinja2**: Used for all code generation templates.
- **geomeppy**: Provides the `EpBunch` base class for stubs.
- **eppy**: Referenced in generated imports.

## Examples
- To add a new stub pattern, create a new Jinja2 template in `templates/` and update `generate_package.py` if new context is needed.
- To update overloads, ensure stubs are generated, then re-run `generate_package.py` to update `idf.pyi`.

## References
- See `README.md` and `CONTRIBUTING.md` for more on setup, testing, and contribution guidelines.
- See `Makefile` for all available developer commands.
