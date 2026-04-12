# Using Commitizen in this repository

This project is configured to use Commitizen with the "Conventional Commits" standard. Commitizen helps you:
- write consistent commit messages interactively,
- bump versions based on commit history,
- and update the changelog automatically.

Configuration lives in `pyproject.toml` under `[tool.commitizen]` and uses:
- version source: PEP 621 `[project].version`
- tag format: `$version` (e.g., `0.4.0`)
- changelog path: `docs/change-log.md`

Note: Commitizen is not currently part of the `dev` or `docs` dependency groups, so install it explicitly with `pipx install commitizen` or `uv tool install commitizen`.

## Making commits (interactive)
Use Commitizen's interactive prompt to standardize commit messages:

- `cz commit`
  - or shorthand: `cz c`

You will be asked for:
- type (feat, fix, docs, refactor, test, chore, build, ci, perf, style, etc.),
- optional scope (e.g., `aws`, `gcs`, `abstract`),
- short subject line,
- longer body (optional),
- breaking change note (if any),
- issue references (optional).

Examples of resulting commit messages:
- `feat(gcs): add Bucket.rename method`
- `fix(aws): handle missing credentials in create_client`
- `docs: expand authentication section in installation guide`

Tip: You can still use `git commit` directly, but `cz commit` helps you stay within the Conventional Commits spec.

## Bumping the version and updating the changelog
Commitizen can analyze commit history and pick the next version automatically (major/minor/patch) following semantic versioning.

- Dry run to see what would happen:
  - `cz bump --dry-run`

- Perform the bump (updates `[project].version` in `pyproject.toml`, creates a VCS tag, and updates the changelog):
  - `cz bump`

- Non-interactive (skip confirmations):
  - `cz bump --yes`

- Pre-releases:
  - `cz bump --pre alpha` (also supports `beta`, `rc`, etc.)

Notes:
- Tags use the configured format `$version` (no `v` prefix).
- The changelog is written to `docs/change-log.md`, which is included in the documentation site under About → Change-log.

## Typical release flow
In this repository, the `github-release` workflow runs `cz bump` for you when an admin dispatches it from the Actions tab. The manual flow below is for local use only:

1. Ensure your main branch is clean and all tests pass.
2. Use `cz commit` for all changes merged into main.
3. Run `cz bump` to update the version, changelog, and create a tag.
4. Push commits and tags:
   - `git push && git push --tags`
5. Cut a GitHub release from the created tag if desired, or let CI pick it up (the `pypi-release` workflow triggers off a successful `github-release` run).

## Troubleshooting
- Commitizen not found: ensure it is installed in your current environment (`pipx list` or `uv tool list`).
- Bump fails to determine type: verify that recent commit messages follow Conventional Commits.
- No tag created: confirm you have a clean Git status and that your repo has Git initialized.
- Changelog not updating: check `[tool.commitizen]` in `pyproject.toml` and that `docs/change-log.md` is writable.

## References
- Conventional Commits: https://www.conventionalcommits.org/
- Commitizen docs: https://commitizen-tools.github.io/commitizen/
