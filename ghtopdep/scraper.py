import calendar
import datetime
from email.utils import formatdate, parsedate
from urllib.parse import parse_qs, urlencode, urlparse

import appdirs
import click
from cachecontrol.heuristics import BaseHeuristic
from selectolax.lexbor import LexborHTMLParser


PACKAGE_NAME = "ghtopdep"
CACHE_DIR = appdirs.user_cache_dir(PACKAGE_NAME)
NEXT_BUTTON_SELECTOR = "#dependents > div.paginate-container > div > a"
ITEM_SELECTOR = "#dependents > div.Box > div.flex-items-center"
REPO_SELECTOR = "span > a.text-bold"
STARS_SELECTOR = "div > span:nth-child(1)"
PACKAGE_SELECTOR = ".select-menu-item"
GITHUB_URL = "https://github.com"
REPOS_PER_PAGE = 30


class OneDayHeuristic(BaseHeuristic):
    cacheable_by_default_statuses = {
        200, 203, 204, 206, 300, 301, 404, 405, 410, 414, 501
    }

    def update_headers(self, response):
        if response.status not in self.cacheable_by_default_statuses:
            return {}

        date = parsedate(response.headers["date"])
        expires = datetime.datetime(*date[:6]) + datetime.timedelta(days=1)
        return {"expires": formatdate(calendar.timegm(expires.timetuple())), "cache-control": "public"}

    def warning(self, response):
        msg = "Automatically cached! Response is Stale."
        return "110 - {0}".format(msg)


def get_packages(sess, page_url):
    parsed_node = LexborHTMLParser(sess.get(page_url).text)

    # (name, package_id) pairs, names are not unique
    packages = []
    selected_package = None
    for package_item in parsed_node.css(PACKAGE_SELECTOR):
        query = parse_qs(urlparse(package_item.attributes.get("href", "")).query)
        if "package_id" in query:
            packages.append((package_item.text().strip(), query["package_id"][0]))
            if package_item.attributes.get("aria-checked") == "true":
                selected_package = package_item.text().strip()
    return packages, selected_package


def get_page_urls(sess, url, destination, all_packages, package_name=None):
    page_url = "{0}/network/dependents?dependent_type={1}".format(url, destination.upper())
    if not all_packages and not package_name:
        return [page_url]

    packages, _ = get_packages(sess, page_url)

    if package_name:
        selected = [(name, package_id) for name, package_id in packages if name == package_name]
        if not selected:
            raise click.BadParameter(
                "no package named '{0}', available packages: {1}".format(
                    package_name, ", ".join(name for name, _ in packages) or "none"),
                param_hint="--package-name")
        packages = selected

    if not packages:
        return [page_url]
    return ["{0}&{1}".format(page_url, urlencode({"package_id": package_id})) for _, package_id in packages]


def get_max_deps(sess, url):
    main_response = sess.get(url)
    parsed_node = LexborHTMLParser(main_response.text)

    deps_count_element = parsed_node.css_first('.table-list-header-toggle .btn-link.selected')
    if deps_count_element is None:
        if main_response.status_code == 404:
            raise click.ClickException("repository not found: {0}".format(url.split("/network/")[0]))
        raise click.ClickException("could not read dependents from {0} (HTTP {1})".format(url, main_response.status_code))
    max_deps = int(deps_count_element.text().strip().split()[0].replace(',', ''))
    return max_deps


def scrape_dependents(sess, page_urls, url, minstar, pbar):
    """Walk the dependents pages and return (repos, total_repos_count, more_than_zero_count)."""
    repos = []
    more_than_zero_count = 0
    total_repos_count = 0
    seen_repo_urls = set()

    for page_url in page_urls:
        while True:
            response = sess.get(page_url)
            parsed_node = LexborHTMLParser(response.text)
            dependents = parsed_node.css(ITEM_SELECTOR)
            for dep in dependents:
                repo_link = dep.css_first(REPO_SELECTOR)
                if repo_link:
                    if repo_link.attributes["href"] in seen_repo_urls:
                        continue
                    seen_repo_urls.add(repo_link.attributes["href"])
                total_repos_count += 1

                repo_stars_list = dep.css(STARS_SELECTOR)
                # only for ghost or private? packages
                if repo_stars_list:
                    repo_stars = repo_stars_list[0].text().strip()
                    repo_stars_num = int(repo_stars.replace(",", ""))
                else:
                    continue

                if repo_stars_num != 0:
                    more_than_zero_count += 1
                if repo_stars_num >= minstar:
                    relative_repo_url = dep.css(REPO_SELECTOR)[0].attributes["href"]
                    repo_url = "{0}{1}".format(GITHUB_URL, relative_repo_url)

                    if repo_url != url:
                        repos.append({
                            "url": repo_url,
                            "stars": repo_stars_num
                        })

            pagination_buttons = parsed_node.css(NEXT_BUTTON_SELECTOR)

            if len(pagination_buttons) == 2:
                page_url = pagination_buttons[1].attributes["href"]
            elif pagination_buttons and pagination_buttons[0].text() == "Next":
                page_url = pagination_buttons[0].attributes["href"]
            elif len(pagination_buttons) == 0 or pagination_buttons[0].text() == "Previous":
                break

            pbar.update(REPOS_PER_PAGE)

    return repos, total_repos_count, more_than_zero_count
