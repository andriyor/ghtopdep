from types import SimpleNamespace

from ghtopdep.github_api import top_repos


class FakeGitHub:
    def __init__(self, archived):
        self.archived = archived
        self.calls = []

    def repository(self, owner, name):
        self.calls.append(name)
        return SimpleNamespace(archived=name in self.archived, description=name + " desc")


def make_repos():
    return [{"url": "https://github.com/o/" + name, "stars": stars}
            for name, stars in [("a", 30), ("b", 20), ("c", 10), ("d", 5)]]


def test_exclude_archived_fills_rows_with_next_repos():
    gh = FakeGitHub(archived={"a"})
    result = top_repos(gh, make_repos(), 2, description=False, exclude_archived=True)
    assert [r["url"][-1] for r in result] == ["b", "c"]
    assert gh.calls == ["a", "b", "c"]  # stops once rows are filled


def test_description_without_exclude_keeps_archived():
    gh = FakeGitHub(archived={"a"})
    result = top_repos(gh, make_repos(), 2, description=True, exclude_archived=False)
    assert [r["description"] for r in result] == ["a desc", "b desc"]


def test_no_api_flags_makes_no_calls():
    result = top_repos(None, make_repos(), 2, description=False, exclude_archived=False)
    assert [r["stars"] for r in result] == [30, 20]


if __name__ == "__main__":
    test_exclude_archived_fills_rows_with_next_repos()
    test_description_without_exclude_keeps_archived()
    test_no_api_flags_makes_no_calls()
    print("ok")
