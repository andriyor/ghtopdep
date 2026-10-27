import json
import os
import sys
from urllib.parse import urlparse

import click
import github3
import requests
from urllib3.util.retry import Retry
from cachecontrol.caches import FileCache
from cachecontrol import CacheControl, CacheControlAdapter
from tqdm import tqdm
from tabulate import tabulate

from ghtopdep.github_api import search_dependents, sort_repos, top_repos
from ghtopdep.scraper import CACHE_DIR, OneDayHeuristic, get_max_deps, get_packages, get_page_urls, scrape_dependents


def humanize(num):
    if num < 1_000:
        return num
    elif num < 10_000:
        return "{}K".format(round(num / 100) / 10)
    elif num < 1_000_000:
        return "{}K".format(round(num / 1_000))
    else:
        return num


def readable_stars(repos):
    for repo in repos:
        repo["stars"] = humanize(repo["stars"])
    return repos


def show_result(repos, total_repos_count, more_than_zero_count, destinations, table):
    if table:
        if repos:
            repos = readable_stars(repos)
            click.echo(tabulate(repos, headers="keys", tablefmt="github"))
            click.echo("found {0} {1} others {2} are private".format(total_repos_count, destinations, destinations))
            click.echo("found {0} {1} with more than zero star".format(more_than_zero_count, destinations))
        else:
            click.echo("Doesn't find any {0} that match search request".format(destinations))
    else:
        click.echo(json.dumps(repos))


def parse_repo_url(url):
    url = url.rstrip("/").removesuffix(".git")
    owner, repository = urlparse(url).path[1:].split("/")
    return url, owner, repository


@click.command()
@click.argument("url")
@click.option("--repositories/--packages", default=True, help="Sort repositories or packages (default repositories)")
@click.option("--table/--json", default=True, help="View mode")
@click.option("--report", is_flag=True, help="Report")
@click.option("--description", is_flag=True, help="Show description of packages or repositories (performs additional "
                                                  "request per shown repository)")
@click.option("--exclude-archived", is_flag=True, help="Skip archived repositories (performs additional request "
                                                       "per checked repository)")
@click.option("--rows", default=10, help="Number of showing repositories (default=10)")
@click.option("--minstar", default=5, help="Minimum number of stars (default=5)")
@click.option("--search", help="search code at top --rows dependents (repositories/packages)")
@click.option("--all-packages", is_flag=True, help="Merge dependents of all packages listed for the repository "
                                                  "(default: only the package GitHub selects)")
@click.option("--package-name", help="Only scrape the package with this exact name")
@click.option("--token", envvar="GHTOPDEP_TOKEN")
def cli(url, repositories, search, table, rows, minstar, report, description, exclude_archived, all_packages,
        package_name, token):
    if report and (all_packages or package_name or exclude_archived):
        raise click.UsageError("--report can't be combined with --all-packages, --package-name or --exclude-archived")
    if all_packages and package_name:
        raise click.UsageError("--package-name and --all-packages are mutually exclusive")

    MODE = os.environ.get("GHTOPDEP_ENV")
    BASE_URL = 'http://159.223.231.170'
    if MODE == "development":
        BASE_URL = 'http://127.0.0.1:3000'

    url, owner, repository = parse_repo_url(url)

    if report:
        try:
            result = requests.get('{}/repos/{}/{}'.format(BASE_URL, owner, repository))
            if result.status_code != 404:
                sorted_repos = sort_repos(result.json(), rows)
                repos = readable_stars(sorted_repos)
                click.echo(tabulate(repos, headers="keys", tablefmt="github"))
                sys.exit()
        except requests.exceptions.ConnectionError as e:
            click.echo(e)

    gh = None
    if (description or search or exclude_archived) and token:
        gh = github3.login(token=token)
        CacheControl(gh.session,
                     cache=FileCache(CACHE_DIR),
                     heuristic=OneDayHeuristic())
    elif (description or search or exclude_archived) and not token:
        raise click.UsageError("--description, --exclude-archived and --search need a token (--token or GHTOPDEP_TOKEN)")

    destination = "repository"
    destinations = "repositories"
    if not repositories:
        destination = "package"
        destinations = "packages"

    sess = requests.session()
    retries = Retry(
        total=15,
        backoff_factor=15,
        status_forcelist=[429, 500, 502, 503, 504])
    adapter = CacheControlAdapter(max_retries=retries,
                                  cache=FileCache(CACHE_DIR),
                                  heuristic=OneDayHeuristic())
    sess.mount("http://", adapter)
    sess.mount("https://", adapter)

    page_urls = get_page_urls(sess, url, destination, all_packages, package_name)

    max_deps = sum(get_max_deps(sess, page_url) for page_url in page_urls)

    pbar = tqdm(total=max_deps)
    repos, total_repos_count, more_than_zero_count = scrape_dependents(sess, page_urls, url, minstar, pbar)
    pbar.close()

    if report:
        try:
            requests.post('{}/repos'.format(BASE_URL), json={"url": url, "owner": owner, "repository": repository, "deps": repos})
        except requests.exceptions.ConnectionError as e:
            click.echo(e)

    sorted_repos = top_repos(gh, repos, rows, description, exclude_archived)

    if search:
        search_dependents(gh, sorted_repos, search)
    else:
        show_result(sorted_repos, total_repos_count, more_than_zero_count, destinations, table)

    if not all_packages and not package_name:
        packages, selected_package = get_packages(sess, page_urls[0])
        if len(packages) > 1:
            scraped = "package '{0}'".format(selected_package) if selected_package else "the package selected by GitHub"
            click.echo("Only {0} was scraped, but this repository lists {1} packages: {2}\n"
                       "Use --package-name NAME to scrape another package, or --all-packages to scrape all of them."
                       .format(scraped, len(packages), ", ".join(name for name, _ in packages)), err=True)
