fmt: ; uv run ruff format .
lint: ; uv run ruff check .
test: ; uv run pytest -q
type: ; uv run mypy --strict samples/demo.py
build:
	uv run python -m mypy_eppy_builder.generate --energyplus-version 23.1 --idd-path .cache/23.1/Energy+.idd --out-dir pkg
	(cd pkg && uv build)
