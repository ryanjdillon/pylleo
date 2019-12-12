def test_posix_string():
    from pylleo import utils

    a = "Foo Bar-BAZ"
    b = "foo_bar_baz"
    assert utils.posix_string(a) == b
