# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue, email, or any other method with the owners of this repository before making a change.

Please note we have a code of conduct, please follow it in all your interactions with the project.

## Pull Request Process

1. Use [Conventional Commits](guides/commitizen.md) — commit messages are the source of truth for version bumps and the changelog.
2. Update the README and/or the docs with details of changes to the interface, including new environment variables, install extras, and API changes.
3. Add or update tests. Unit tests should prefer `moto`'s `@mock_aws` for AWS and mocked GCS clients; reserve the `e2e` marker for tests that must hit real buckets.
4. Keep provider parity in mind — if you add a method to the S3 `Bucket`, consider whether the GCS `Bucket` should get an equivalent, and vice versa. Document any intentional divergence.
5. The versioning scheme is [SemVer](http://semver.org/). Version bumps are produced by `commitizen` based on commit history, so scope each change correctly (`feat:` / `fix:` / `refactor:` / `build:` / `ci:` / `chore:` / `perf:`).
6. You may merge the Pull Request once you have the sign-off of a reviewer, or if you do not have merge rights, request a reviewer to merge for you.

## Development setup

This project uses [uv](https://docs.astral.sh/uv/). To sync a full dev environment:

```bash
uv sync --extra all --group dev
```

Run the tests:

```bash
uv run pytest -sv
```

Run only the mock-based tests (no real cloud credentials needed):

```bash
uv run pytest -m mock
```

Run only end-to-end tests (requires AWS and GCS credentials):

```bash
uv run pytest -m e2e
```

Run pre-commit hooks:

```bash
uv run pre-commit run --all-files
```

## Documentation

Docs are built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) + [mkdocstrings](https://mkdocstrings.github.io/).

Install the docs dependency group:

```bash
uv sync --group docs
```

Serve the docs locally with live reload:

```bash
uv run mkdocs serve
```

Build the static site:

```bash
uv run mkdocs build
```

## Code of Conduct

See the [Code of Conduct](CODE_OF_CONDUCT.md).
