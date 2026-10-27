from pathlib import Path
from types import SimpleNamespace

from ghtopdep.ghtopdep import scrape_dependents

# First dependents page of psf/requests, trimmed to #dependents; its "Next" link leads to LAST_PAGE
PAGE = (Path(__file__).parent / "fixtures" / "dependents_page.html").read_text()
LAST_PAGE = '<div id="dependents"></div>'
FIRST_URL = "https://github.com/psf/requests/network/dependents?dependent_type=REPOSITORY"


class FakeSession:
    def __init__(self):
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        return SimpleNamespace(text=PAGE if url == FIRST_URL else LAST_PAGE)


def scrape(page_urls, url="https://github.com/psf/requests", minstar=0):
    sess = FakeSession()
    pbar = SimpleNamespace(update=lambda n: None)
    return scrape_dependents(sess, page_urls, url, minstar, pbar), sess.urls


def test_parses_page_and_follows_next():
    (repos, total, more_than_zero), urls = scrape([FIRST_URL])
    assert (len(repos), total, more_than_zero) == (30, 30, 11)
    assert max(r["stars"] for r in repos) == 55
    assert all(r["url"].startswith("https://github.com/") for r in repos)
    assert len(urls) == 2 and "dependents_after=" in urls[1]


def test_minstar_and_self_exclusion():
    (repos, _, _), _ = scrape([FIRST_URL], minstar=5)
    assert sorted(r["stars"] for r in repos) == [5, 19, 20, 34, 55]
    top = max(repos, key=lambda r: r["stars"])["url"]
    (repos, _, _), _ = scrape([FIRST_URL], url=top, minstar=5)
    assert top not in [r["url"] for r in repos]


def test_dedup_across_packages():
    (repos, total, _), _ = scrape([FIRST_URL, FIRST_URL])
    assert (len(repos), total) == (30, 30)


if __name__ == "__main__":
    test_parses_page_and_follows_next()
    test_minstar_and_self_exclusion()
    test_dedup_across_packages()
    print("ok")
