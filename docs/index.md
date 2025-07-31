# mypy-eppy-builder

[![Release](https://img.shields.io/github/v/release/samuelduchesne/mypy-eppy-builder)](https://img.shields.io/github/v/release/samuelduchesne/mypy-eppy-builder)
[![Build status](https://img.shields.io/github/actions/workflow/status/samuelduchesne/mypy-eppy-builder/main.yml?branch=main)](https://github.com/samuelduchesne/mypy-eppy-builder/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/samuelduchesne/mypy-eppy-builder)](https://img.shields.io/github/commit-activity/m/samuelduchesne/mypy-eppy-builder)
[![License](https://img.shields.io/github/license/samuelduchesne/mypy-eppy-builder)](https://img.shields.io/github/license/samuelduchesne/mypy-eppy-builder)

Automated type stubs for Eppy, enabling static type checking and IDE autocompletion.

Numeric fields in the IDD may specify limits using `\minimum`, `\minimum>`, `\maximum`,
and `\maximum<`. These bounds are translated into `Annotated` type hints with
`pydantic.Field` metadata. When defaults are present, they appear in the generated
stub as `Field(default=..., ge=..., le=...)` alongside the annotation.

## Generating stub packages

Use `generate_package.py` to build stubs for one or more EnergyPlus versions. Pass
the desired versions and the path to the corresponding `Energy+.idd` file:

```bash
uv run python src/mypy_eppy_builder/generate_package.py \
    --versions 23.1 24.1 \
    --idd-file /path/to/Energy+.idd \
    --package-type eppy
```

If the `--idd-file` argument is omitted, the script reads the `EPPY_IDD_FILE`
environment variable or falls back to the default EnergyPlus installation
location. Use `--package-type archetypal` to generate the
`archetypal-stubs` package instead of `eppy-stubs`.

Pre-built distributions expose extras for each EnergyPlus version. Install the
matching stub like so:

```bash
pip install "archetypal-stubs[eplus23_1]"
```

Make sure the extra corresponds to the EnergyPlus version of your IDF files.

## Publishing to PyPI

The CI workflow builds stub packages for each supported EnergyPlus version and
publishes them to PyPI on release. This automatically uploads
`eppy-stubs` and `archetypal-stubs` so they can be installed with `pip`.
