import textwrap
import time
from urllib.parse import urlparse

import click
import github3
import requests


def shorten_description(description):
    if not description:
        return " "
    return textwrap.shorten(description, width=60, placeholder="...")


def rate_limit_wait(response):
    """Seconds to wait if the response is a GitHub rate limit error, otherwise None."""
    if response.status_code not in (403, 429):
        return None
    if "Retry-After" in response.headers:
        return int(response.headers["Retry-After"])
    if response.headers.get("X-RateLimit-Remaining") == "0":
        return max(int(response.headers["X-RateLimit-Reset"]) - time.time(), 0) + 1
    return None


def search_code(gh, query):
    """Return (results, incomplete). Code search allows only 10 requests per minute, so wait out the limit and retry."""
    while True:
        try:
            iterator = gh.search_code(query)
            results = list(iterator)
            incomplete = bool(iterator.last_response and iterator.last_response.json().get("incomplete_results"))
            return results, incomplete
        except github3.exceptions.GitHubError as e:
            wait = rate_limit_wait(e.response)
            if wait is None:
                raise
            click.echo("Code search rate limit reached, waiting {0:.0f}s".format(wait), err=True)
            time.sleep(wait)


def search_dependents(gh, repos, search):
    """Print code search hits in each repo, then list repos that failed or may be incomplete."""
    failed, incomplete = [], []
    for repo in repos:
        repo_path = urlparse(repo["url"]).path[1:]
        try:
            results, is_incomplete = search_code(gh, "{0} repo:{1}".format(search, repo_path))
        except (github3.exceptions.GitHubException, requests.RequestException) as e:
            failed.append("{0} ({1})".format(repo_path, e))
            continue
        if is_incomplete:
            incomplete.append(repo_path)
        for s in results:
            click.echo("{0} with {1} stars".format(s.html_url, repo["stars"]))
    if failed:
        click.echo("Could not search: {0}".format(", ".join(failed)), err=True)
    if incomplete:
        click.echo("Results may be incomplete for: {0}".format(", ".join(incomplete)), err=True)


def sort_repos(repos, rows):
    sorted_repos = sorted(repos, key=lambda i: i["stars"], reverse=True)
    return sorted_repos[:rows]


def top_repos(gh, repos, rows, description, exclude_archived):
    """Sort by stars and take `rows` repos, calling the API only for those."""
    if not (description or exclude_archived):
        return sort_repos(repos, rows)
    result = []
    for repo in sorted(repos, key=lambda i: i["stars"], reverse=True):
        if len(result) == rows:
            break
        _, owner, name = urlparse(repo["url"]).path.split("/")
        gh_repo = gh.repository(owner, name)
        if exclude_archived and gh_repo.archived:
            continue
        if description:
            repo["description"] = shorten_description(gh_repo.description)
        result.append(repo)
    return result
