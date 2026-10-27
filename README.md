# GHTOPDEP

[![image](https://img.shields.io/pypi/v/ghtopdep.svg)](https://pypi.org/project/ghtopdep/)
[![image](https://img.shields.io/pypi/l/ghtopdep.svg)](https://pypi.org/project/ghtopdep/)

CLI tool for sorting dependents repo by stars

## Requirements

- Python 3.11 and up

## Installation

### From PyPI

```sh
$ pip install ghtopdep
```

### From git repository

```sh
$ pip install git+https://github.com/andriyor/ghtopdep.git
```

### From source

```sh
$ git clone https://github.com/andriyor/ghtopdep
$ cd ghtopdep
$ pip install .
```

### Using docker (from source)

First `docker build` the image once:

```sh
$ git clone https://github.com/andriyor/ghtopdep
$ cd ghtopdep
$ docker build . -t ghtopdep
```

Then you can `docker run` it:

```sh
$ docker run --rm -it ghtopdep --help
```

## Version upgrade

```sh
➜ pip install --upgrade ghtopdep
```

## Usage

A token is needed only for `--description`, `--exclude-archived` and `--search`, which use the GitHub API.
Dependents themselves are scraped from GitHub pages and don't use the token.
For public repositories, [create a token](https://github.com/settings/tokens/new?scopes=public_repo&description=ghtopdep)
with the public_repo permission.

You can use token as environment variable `GHTOPDEP_TOKEN` at `~/.bashrc` or `~/.zshrc`

export GHTOPDEP_TOKEN="**\*\*\*\***\*\***\*\*\*\***\*\*\*\***\*\*\*\***\*\***\*\*\*\***"

or pass token as option --token

If you use [GitHub CLI](https://cli.github.com/), you can reuse its token:

```sh
export GHTOPDEP_TOKEN=$(gh auth token)
```

```sh
➜ ghtopdep --help
Usage: ghtopdep [OPTIONS] URL

Options:
  --repositories / --packages  Sort repositories or packages (default
                               repositories)
  --table / --json             View mode
  --description                Show description of packages or repositories
                               (performs additional request per shown
                               repository)
  --exclude-archived           Skip archived repositories (performs additional
                               request per checked repository)
  --rows INTEGER               Number of showing repositories (default=10)
  --minstar INTEGER            Minimum number of stars (default=5)
  --search TEXT                search code at top --rows dependents
                               (repositories/packages)
  --all-packages               Merge dependents of all packages listed for the
                               repository (default: only the package GitHub
                               selects)
  --package-name TEXT          Only scrape the package with this exact name
  --token TEXT
  --help                       Show this message and exit.
```

### Table view (by default)

```sh
➜ ghtopdep https://github.com/rob-balfre/svelte-select
| url                                              | stars   |
|--------------------------------------------------|---------|
| https://github.com/dbgate/dbgate                 | 7.4K    |
| https://github.com/workadventure/workadventure   | 5.9K    |
| https://github.com/libredirect/browser_extension | 4.1K    |
| https://github.com/xianfei/SysMocap              | 3.2K    |
| https://github.com/ananthakumaran/paisa          | 3.2K    |
| https://github.com/remult/remult                 | 3.2K    |
| https://github.com/goniszewski/grimoire          | 2.9K    |
| https://github.com/sparrowapp-dev/sparrow-app    | 2.5K    |
| https://github.com/rogchap/wombat                | 1.4K    |
| https://github.com/josdejong/svelte-jsoneditor   | 1.3K    |
found 1156 repositories others repositories are private
found 415 repositories with more than zero star
```

### JSON view

```sh
➜ ghtopdep https://github.com/rob-balfre/svelte-select --json
[{"url": "https://github.com/dbgate/dbgate", "stars": 7353}, {"url": "https://github.com/workadventure/workadventure", "stars": 5888}, {"url": "https://github.com/libredirect/browser_extension", "stars": 4096}, {"url": "https://github.com/xianfei/SysMocap", "stars": 3239}, {"url": "https://github.com/ananthakumaran/paisa", "stars": 3229}, {"url": "https://github.com/remult/remult", "stars": 3214}, {"url": "https://github.com/goniszewski/grimoire", "stars": 2877}, {"url": "https://github.com/sparrowapp-dev/sparrow-app", "stars": 2548}, {"url": "https://github.com/rogchap/wombat", "stars": 1429}, {"url": "https://github.com/josdejong/svelte-jsoneditor", "stars": 1271}]
```

you can sort packages and fetch their description

```sh
➜ ghtopdep https://github.com/rob-balfre/svelte-select --description --packages
| url                                                                    | stars   | description                                                  |
|------------------------------------------------------------------------|---------|--------------------------------------------------------------|
| https://github.com/dbgate/dbgate                                       | 7.4K    | Database manager for MySQL, PostgreSQL, SQL Server,...       |
| https://github.com/josdejong/svelte-jsoneditor                         | 1.3K    | A web-based tool to view, edit, format, repair, query,...    |
| https://github.com/Obsidian-TTRPG-Community/fantasy-statblocks         | 501     | Create Dungeons and Dragons style statblocks for Obsidian.md |
| https://github.com/insodoc/insomnia-documenter                         | 497     | Tool to create minimalist and beautiful API documentation... |
| https://github.com/pragmatic-engineering/svelte-form-builder-community | 74      | No-code Drag n Drop Form Builder for Svelte                  |
| https://github.com/sveltekit/ui                                        | 62      | Powerful, reliable & fully featured Svelte UI library        |
| https://github.com/EMPTYVOID-DEV/Altron                                | 23      | Rich text editor as a svelte component                       |
| https://github.com/BEXIS2/Core                                         | 16      | This is the public code repository of the BEXIS2 data...     |
| https://github.com/tilde-lab/optimade.science                          | 10      | A "sky-scanner" Optimade browser-only GUI                    |
| https://github.com/invopop/gobl.builder                                | 9       | GOBL Builder is an interactive, low code tool for...         |
found 69 packages others packages are private
found 22 packages with more than zero star
```

also ghtopdep support code searching at dependents (repositories/packages)

`--search` searches the top `--rows` dependents. GitHub allows about 10 code searches per minute,
so larger `--rows` values make ghtopdep pause and wait.

```sh
➜ ghtopdep https://github.com/rob-balfre/svelte-select --search=isMulti
https://github.com/dbgate/dbgate/blob/7aa44d13e44a715fb7235db47e047e1ac0c981fb/packages/web/src/forms/SelectField.svelte with 7353 stars
https://github.com/dbgate/dbgate/blob/7aa44d13e44a715fb7235db47e047e1ac0c981fb/packages/web/src/impexp/FormTablesSelect.svelte with 7353 stars
https://github.com/dbgate/dbgate/blob/7aa44d13e44a715fb7235db47e047e1ac0c981fb/packages/web/src/forms/FormArchiveFilesSelect.svelte with 7353 stars
https://github.com/dbgate/dbgate/blob/7aa44d13e44a715fb7235db47e047e1ac0c981fb/packages/web/src/formview/FormViewFilters.svelte with 7353 stars
https://github.com/dbgate/dbgate/blob/7aa44d13e44a715fb7235db47e047e1ac0c981fb/packages/web/src/designer/DesignerTable.svelte with 7353 stars
https://github.com/dbgate/dbgate/blob/7aa44d13e44a715fb7235db47e047e1ac0c981fb/packages/datalib/src/GridDisplay.ts with 7353 stars
...
```

## Development setup

Using [uv](https://docs.astral.sh/uv/)

```sh
$ uv sync
$ uv run ghtopdep https://github.com/rob-balfre/svelte-select
$ uv build
$ uv publish
```

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Alternatives

[Boshen/top-github-dependents-by-stars: CLI tool for sorting dependents repo by stars](https://github.com/Boshen/top-github-dependents-by-stars)

[dep-rank](https://github.com/j7an/dep-rank) - fork of ghtopdep, adds trust-based ranking and an MCP server for AI agents

[ghtracker](https://github.com/zer0yu/ghtracker) - not provide full result https://github.com/zer0yu/ghtracker/issues/2

[github-by-stars](https://github.com/hacker-DOM/github-by-stars) - complex setup


## References

[Allow dependents to be sorted by stars · Issue #1537 · isaacs/github](https://github.com/isaacs/github/issues/1537)

[Sorting the insights dependency graph lists · community · Discussion #5575](https://github.com/orgs/community/discussions/5575)
