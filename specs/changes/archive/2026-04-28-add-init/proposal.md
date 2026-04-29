# Proposal: Add `shablon init` Command

## Why

A new user adopting shablon today has to read the docs, learn the `.shablon/`
convention, hand-create the directory, write a `config.toml` (or know it's
optional), set up an executable `vars.<ext>`, and create `templates/` with an
`_includes/` partial dir. That's enough friction to deter casual use. A single
`shablon init` that scaffolds the convention removes the guesswork.

## What Changes

- New `init` subcommand on the `shablon` CLI.
- `shablon init` creates a fresh `.shablon/` skeleton at the chosen project
  root containing `config.toml`, an executable starter `vars.sh`,
  `templates/`, and `templates/_includes/`.
- Refuses to clobber: if `.shablon/` already exists at the target, exits
  non-zero without modifying anything.
- Honors the existing `--cwd` flag for choosing where to scaffold (defaulting
  to the process cwd; **no upward walk** -- init creates a project root, it
  doesn't discover one).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli`: adds the `init` subcommand alongside `generate`. Reuses the existing
  `--cwd` flag with init-specific semantics (target directory, no upward
  walk).

## Impact

- `src/shablon/cli.py` — register the new subparser and dispatch.
- New module `src/shablon/init.py` (or similar) — implements the scaffolding.
- Embedded starter file contents (likely string constants in the new module).
- New tests covering: success scaffolding, refusal when `.shablon/` exists,
  `--cwd` targeting, executable bit on `vars.sh`.
- README and CHANGELOG mention the new command.

## Out of Scope

- Choosing among multiple `vars.<ext>` languages at init time (always
  scaffolds `vars.sh`; users can rename/replace).
- Populating `templates/` with example templates or `_includes/` with a
  starter partial. Init creates empty directories.
- Idempotent / merge-mode init that fills in missing pieces of an existing
  `.shablon/`.
- Rewriting an existing `.shablon/` (no `--force` flag in this change).
- A `--git-init` companion or `.gitignore` integration.

## Open Decisions (please confirm)

1. **Default vars language**: scaffold `vars.sh` (shell, universal) vs.
   `vars.py` (matches the project's own toolchain). Drafted as `vars.sh`.
2. **Empty-directory persistence**: `templates/` and `templates/_includes/`
   are empty after init. Git will not track empty dirs. Should init drop a
   `.gitkeep` in each? Drafted as **no** (keeps the layout minimal).
3. **Starter `config.toml` content**: empty file, or a file with the two
   recognised keys present as commented-out lines showing defaults? Drafted
   as **commented-out defaults** to act as inline documentation.
