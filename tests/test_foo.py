from mypy_eppy_builder.foo import foo


def test_foo():
    assert foo("foo") == "foo"
