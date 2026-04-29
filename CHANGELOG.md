# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1] - 2026-04-29

### Added

- `shablon --version` flag that prints the installed version.
- `shablon init` subcommand that scaffolds a fresh `.shablon/` skeleton (`config.toml`, executable `vars.sh` printing `{}`, `templates/`, `templates/_includes/`) in the current working directory. Refuses to overwrite an existing `.shablon/`.
- `shablon` CLI with the `generate` subcommand for rendering Jinja2 templates from a project's `.shablon/templates/` tree.
- Upward project-root discovery: shablon walks parents from cwd until it finds a `.shablon/` directory.
- Output paths mirror the template path under `.shablon/templates/`, with parent directories created as needed and existing files overwritten.
- Output files inherit their template's mode bits, so executable templates produce executable outputs.
- Trailing newlines are preserved (`keep_trailing_newline=True`).
- Symlinked template files and directories are followed; outputs are written as regular files.
- Deterministic render order: templates are rendered in ascending POSIX-form lexicographic order, with one `wrote <relative-path>` line per file on stdout.
- Partials directories (default basename `_includes`, configurable) are excluded from rendering at any depth and remain available for `{% include %}` / `{% extends %}`. The exclusion is structural and cannot be overridden by `include` patterns.
- Dotfile filtering: paths whose basename starts with `.` are skipped by default; `include` patterns in `config.toml` can re-enable specific dotfiles by basename.
- Optional executable `.shablon/vars.<ext>` file whose JSON-object stdout becomes the render context. Subprocess contract: cwd is the project root, `SHABLON_PROJECT_ROOT` is injected, stdin is `/dev/null`, no positional args, exit 0 required, stderr inherited.
- Validation around `vars.<ext>`: exactly one allowed, must be executable, stdout must parse as a JSON object.
- Optional `.shablon/config.toml` with strict validation. Recognised fields: `include` (array of basename `fnmatch` patterns) and `partials_dir` (non-empty string, no path separators, not `.` or `..`). Unknown keys, wrong types, and TOML parse errors halt before any templates are rendered.
- Clear non-zero exits with stderr messages for: missing `.shablon/`, missing `.shablon/templates/`, multiple `vars.*` files, non-executable `vars.<ext>`, vars script failure, non-object/invalid JSON output, and config validation errors.

[0.1.0]: https://github.com/a3lem/shablon/releases/tag/v0.1.0
