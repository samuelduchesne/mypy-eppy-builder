# mypy-eppy-builder

[![Release](https://img.shields.io/github/v/release/samuelduchesne/mypy-eppy-builder)](https://img.shields.io/github/v/release/samuelduchesne/mypy-eppy-builder)
[![Build status](https://img.shields.io/github/actions/workflow/status/samuelduchesne/mypy-eppy-builder/main.yml?branch=main)](https://github.com/samuelduchesne/mypy-eppy-builder/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/samuelduchesne/mypy-eppy-builder/branch/main/graph/badge.svg)](https://codecov.io/gh/samuelduchesne/mypy-eppy-builder)
[![Commit activity](https://img.shields.io/github/commit-activity/m/samuelduchesne/mypy-eppy-builder)](https://img.shields.io/github/commit-activity/m/samuelduchesne/mypy-eppy-builder)
[![License](https://img.shields.io/github/license/samuelduchesne/mypy-eppy-builder)](https://img.shields.io/github/license/samuelduchesne/mypy-eppy-builder)

Automated type stubs for Eppy, enabling static type checking and IDE autocompletion.

- **Github repository**: <https://github.com/samuelduchesne/mypy-eppy-builder/>
- **Documentation** <https://samuelduchesne.github.io/mypy-eppy-builder/>

## Getting started with your project

### 1. Create a New Repository

First, create a repository on GitHub with the same name as this project, and then run the following commands:

```bash
git init -b main
git add .
git commit -m "init commit"
git remote add origin git@github.com:samuelduchesne/mypy-eppy-builder.git
git push -u origin main
```

### 2. Set Up Your Development Environment

Then, install the environment and the pre-commit hooks with

```bash
make install
```

This will also generate your `uv.lock` file

### 3. Run the pre-commit hooks

Initially, the CI/CD pipeline might be failing due to formatting issues. To resolve those run:

```bash
uv run pre-commit run -a
```

### 4. Commit the changes

Lastly, commit the changes made by the two steps above to your repository.

```bash
git add .
git commit -m 'Fix formatting issues'
git push origin main
```

You are now ready to start development on your project!
The CI/CD pipeline will be triggered when you open a pull request, merge to main, or when you create a new release.

### Generating stub packages

The `generate_package.py` script builds the `eppy-stubs` or
`archetypal-stubs` packages. Provide one or more EnergyPlus versions and
the IDD file to target:

```bash
uv run python src/mypy_eppy_builder/generate_package.py \
    --versions 23.1 24.1 \
    --idd-file /path/to/Energy+.idd \
    --package-type eppy
```

Each EnergyPlus version produces its own stub package under `generated_package/`.

If `--idd-file` is omitted, the script uses the `EPPY_IDD_FILE`
environment variable or searches the default EnergyPlus location. Use
`--package-type archetypal` to generate the corresponding archetypal
stubs.

For pre-built packages from PyPI install the wrapper with an extra matching
your EnergyPlus version, for example:

```bash
pip install "archetypal-stubs[eplus23_1]"
```

Ensure the stub version matches the EnergyPlus files you work with.

To finalize the set-up for publishing to PyPI, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/publishing/#set-up-for-pypi).
For activating the automatic documentation with MkDocs, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/mkdocs/#enabling-the-documentation-on-github).
To enable the code coverage reports, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/codecov/).

## Releasing a new version

- Create an API Token on [PyPI](https://pypi.org/).
- Add the API Token to your projects secrets with the name `PYPI_TOKEN` by visiting [this page](https://github.com/samuelduchesne/mypy-eppy-builder/settings/secrets/actions/new).
- Create a [new release](https://github.com/samuelduchesne/mypy-eppy-builder/releases/new) on Github.
- Create a new tag in the form `*.*.*`.

When a release is published, the CI workflow packages the generated
stubs for each supported EnergyPlus version and uploads the resulting
`eppy-stubs` and `archetypal-stubs` distributions to PyPI.

For more details, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/cicd/#how-to-trigger-a-release).

---

Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv).
