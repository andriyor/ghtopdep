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
        return iter(["hit"])


def test_waits_and_retries_on_rate_limit():
    sleeps = []
    ghtopdep.time.sleep = sleeps.append
    reset = str(int(time.time()) + 30)
    gh = FakeGitHub([rate_limited_response({"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": reset}),
                     rate_limited_response({"Retry-After": "5"})])
    assert ghtopdep.search_code(gh, "q") == ["hit"]
    assert 29 <= sleeps[0] <= 31 and sleeps[1] == 5


def test_other_errors_are_raised():
    gh = FakeGitHub([rate_limited_response({})])  # 403 without rate limit headers
    try:
        ghtopdep.search_code(gh, "q")
    except github3.exceptions.ForbiddenError:
        return
    raise AssertionError("expected ForbiddenError")


if __name__ == "__main__":
    test_waits_and_retries_on_rate_limit()
    test_other_errors_are_raised()
    print("ok")
