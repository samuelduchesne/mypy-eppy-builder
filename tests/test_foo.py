import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mypy_eppy_builder.foo import foo


def test_foo():
    assert foo("foo") == "foo"
