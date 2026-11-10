import click
import pytest

from ghtopdep.ghtopdep import parse_repo_url


def test_parse_repo_url():
    expected = ("https://github.com/o/r", "o", "r")
    for url in ["https://github.com/o/r", "https://github.com/o/r/", "https://github.com/o/r.git", "https://github.com/o/r.git/"]:
        assert parse_repo_url(url) == expected, url


@pytest.mark.parametrize("url", [
    "https://github.com/onlyowner",
    "https://github.com/",
    "https://github.com",
    "not-a-url",
    "https://github.com/o/r/extra",
])
def test_parse_repo_url_rejects_malformed_urls(url):
    with pytest.raises(click.BadParameter):
        parse_repo_url(url)


if __name__ == "__main__":
    test_parse_repo_url()
    print("ok")
