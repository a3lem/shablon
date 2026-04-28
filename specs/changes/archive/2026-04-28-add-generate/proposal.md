# Proposal: Add `shablon generate` Command

## Why

The tiquette project ships a one-off `scripts/generate-plugin-files.py` that walks
`plugin_src/templates/`, renders each Jinja2 template, and writes the result to a
mirrored path under the repo root. The pattern is useful beyond tiquette: any
project that needs to generate agent assets, configs, or scaffolding from
parameterised templates.

Shablon promotes that pattern into a reusable CLI. The first (and only) command
in this change is `shablon generate`. Compared to the tiquette script it adds
one capability: dynamic variable resolution via an executable `vars.<ext>` file
that prints a JSON object to stdout. This lets each consuming project decide
how its render context is built (read `pyproject.toml`, shell out to its own
CLI's `--help`, query git, etc.) without shablon needing to know.

## Scope

In scope:

- A CLI entry point `shablon` with subcommand `generate`.
- A convention-based input directory (`.shablon/`) containing `templates/`,
  an optional executable `vars.<ext>`, and an optional `config.toml`.
- Upward project-root discovery: shablon walks parents from `--cwd` (or the
  process cwd) to find the nearest `.shablon/`.
- Jinja2 rendering using the directory layout under `templates/` as the
  output layout, with `_includes/` reserved for partials and dotfiles
  skipped by default.
- A single `vars.<ext>` executable whose stdout (a JSON object) is unpacked
  as the render context.
- Output files mirror their template's mode bits (so an executable template
  produces an executable output).

Out of scope (deferred to later changes):

- Multiple commands beyond `generate` (e.g. `init`, `validate`, `clean`).
- Multiple `vars.*` files or layered context sources.
- Per-template front-matter / per-template context overrides.
- Output destinations outside the project root.
- Watch mode, dry-run, diff mode.

## Capabilities

| Capability | Purpose |
|------------|---------|
| `cli` | Command surface, project-root discovery, arguments, exit codes, stdout/stderr conventions. |
| `templates` | Discovering templates under `.shablon/templates/`, dotfile/`_includes/` filtering, deterministic ordering, symlink handling, output path + mode mirroring, rendering, writing. |
| `variables` | Discovering and executing `.shablon/vars.<ext>`, the subprocess contract (cwd, env, argv, streams), parsing its JSON output into the render context. |
| `config` | Optional `.shablon/config.toml`, its schema (currently `include`), strict validation, parse-error handling. |

## Non-Goals

Shablon does not opine on how `vars.<ext>` is implemented. It is an executable
contract: stdout is JSON, exit code is 0 on success. The user's project owns
the script and its language.
