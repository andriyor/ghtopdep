import contextlib
import io
import time
from types import SimpleNamespace

import github3

from ghtopdep import ghtopdep


def rate_limited_response(headers):
    return SimpleNamespace(status_code=403, headers=headers, json=lambda: {"message": "API rate limit exceeded"})


class FakeGitHub:
    def __init__(self, failures):
        self.failures = list(failures)

    def search_code(self, query):
        if self.failures:
            raise github3.exceptions.ForbiddenError(self.failures.pop(0))
        return FakeIterator()


HIT = SimpleNamespace(html_url="hit")


class FakeIterator:
    last_response = SimpleNamespace(json=lambda: {"incomplete_results": True})

    def __iter__(self):
        return iter([HIT])


def test_waits_and_retries_on_rate_limit():
    sleeps = []
    ghtopdep.time.sleep = sleeps.append
    reset = str(int(time.time()) + 30)
    gh = FakeGitHub([rate_limited_response({"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": reset}),
                     rate_limited_response({"Retry-After": "5"})])
    assert ghtopdep.search_code(gh, "q") == ([HIT], True)
    assert 29 <= sleeps[0] <= 31 and sleeps[1] == 5


def test_other_errors_are_raised():
    gh = FakeGitHub([rate_limited_response({})])  # 403 without rate limit headers
    try:
        ghtopdep.search_code(gh, "q")
    except github3.exceptions.ForbiddenError:
        return
    raise AssertionError("expected ForbiddenError")


def test_search_dependents_reports_failed_and_incomplete_repos():
    class PartlyFailingGitHub:
        def search_code(self, query):
            if query.endswith("o/bad"):
                raise github3.exceptions.UnprocessableEntity(
                    SimpleNamespace(status_code=422, headers={}, json=lambda: {"message": "Validation Failed"}))
            return FakeIterator()

    repos = [{"url": "https://github.com/o/good", "stars": 9}, {"url": "https://github.com/o/bad", "stars": 3}]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        ghtopdep.search_dependents(PartlyFailingGitHub(), repos, "q")
    assert out.getvalue() == "hit with 9 stars\n"
    assert "Could not search: o/bad" in err.getvalue()
    assert "Results may be incomplete for: o/good" in err.getvalue()


if __name__ == "__main__":
    test_waits_and_retries_on_rate_limit()
    test_other_errors_are_raised()
    test_search_dependents_reports_failed_and_incomplete_repos()
    print("ok")
