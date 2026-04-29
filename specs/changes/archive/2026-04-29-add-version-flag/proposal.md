# Proposal: Add `--version` Flag

## Why

Users and tooling expect a CLI to report its installed version. Without
`shablon --version`, the only way to discover the running version is via the
package metadata (`uv pip show shablon`, `pip show shablon`), which is awkward
and not always available (e.g. when the binary is on `PATH` from a tool
installer).

## What Changes

- New top-level `--version` flag on `shablon` that prints `shablon <version>`
  and exits 0.
- Version string sourced from `shablon.__version__` so the package and CLI
  cannot drift.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli`: adds the `--version` flag at the top-level parser.

## Impact

- `src/shablon/__init__.py` — expose `__version__`.
- `src/shablon/cli.py` — register `--version` on the top-level parser.

## Out of Scope

- A `--version` flag on individual subcommands.
- Reading the version from package metadata at runtime; the source string is
  the single source of truth.
