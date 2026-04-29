# Design: `shablon init`

## Context

The CLI currently exposes one subcommand, `generate`, dispatched from
`src/shablon/cli.py` via an `assert args.command == "generate"`. Adding a
second subcommand requires a real dispatch and a small new module that owns
the scaffolding logic. The existing code style (frozen dataclasses,
`ShablonError` raised from feature modules and caught in `cli.main`,
`stdlib logging` via the `shablon` logger) is the template to follow.

## Goals / Non-Goals

**Goals**

- Add `shablon init` as a peer to `shablon generate` with a clean dispatch
  in `cli.main`.
- Implement scaffolding in a single new module so it stays self-contained
  and easy to test.
- Keep starter file contents inline as string constants -- no package data,
  no `importlib.resources` machinery.

**Non-Goals**

- Pluggable templates / `--from <profile>` flags. Out of scope for the
  proposal.
- Atomic-on-IO-failure scaffolding (write-to-tempdir-then-rename). The only
  pre-existing-state we guard against is a pre-existing `.shablon/`; partial
  state from mid-write filesystem errors is acceptable (treat as system
  fault, surface via `ShablonError`).

## Decisions

### Dispatch via a small command map in `cli.main`

Replace the current `assert args.command == "generate"` with:

```py
COMMANDS: dict[str, T.Callable[[Path], None]] = {
    "generate": generate.run,
    "init": init.run,
}
```

Each subcommand entry takes the resolved target `Path` and returns `None`,
raising `ShablonError` on user-facing failures. `cli.main` looks up the
command and invokes it; the existing `try/except ShablonError` handler
continues to be the single error-reporting site.

**Alternatives considered:**

- `match args.command:` with explicit branches. Equivalent but encourages
  copy-paste as more commands are added. Map keeps the registration in one
  place.
- Sub-functions like `_run_generate(args)` / `_run_init(args)`. Adds a layer
  for no benefit at two commands.

### `--cwd` stays global, with neutral help text

`--cwd` is currently a top-level flag whose help text says it's the
"Starting directory for upward `.shablon/` discovery". That description
doesn't match init's semantics (target directory, no walk). Two options:

- (a) Keep `--cwd` global, rewrite the help text to be neutral.
- (b) Move `--cwd` to each subparser, with subcommand-specific help text.

Choose **(a)**. The flag means "where shablon does its work"; both
subcommands interpret that consistently within their own contracts. Option
(b) duplicates the flag definition for marginal help-text clarity.

New help text: `"Working directory: where to scaffold (init) or where to start
the upward .shablon/ discovery (generate). Default: cwd."`

**Alternatives considered:**

- Adding `--target` as an init-specific alias. Rejected: extra surface area
  for one command's wording preference.

### New module: `src/shablon/init.py`

Owns the scaffolding. Public API:

```py
def run(target: Path) -> None: ...
```

Behavior:

1. `assert target.is_absolute(), target` (defensive; cli always resolves).
2. `if not target.is_dir(): raise ShablonError(f"{target} is not a directory")`.
3. `shablon_dir = target / ".shablon"`.
4. `if shablon_dir.exists() or shablon_dir.is_symlink():`
   raise `ShablonError(f"{shablon_dir} already exists; refusing to overwrite")`.
   (Use `exists()` *or* `is_symlink()` to also reject a dangling symlink and a
   plain file at that path -- matches the spec's "file, directory, or
   symlink" wording.)
5. Create the tree:
   - `shablon_dir.mkdir()`
   - `(shablon_dir / "templates").mkdir()`
   - `(shablon_dir / "templates" / "_includes").mkdir()`
6. Write starter files:
   - `(shablon_dir / "config.toml").write_text(_CONFIG_TOML)`
   - `vars_path = shablon_dir / "vars.sh"`; `vars_path.write_text(_VARS_SH)`;
     `vars_path.chmod(0o755)`
7. `print(f"initialized {shablon_dir}")` to stdout (mirrors `generate`'s
   stdout convention of one line per durable artifact).

The `print` is intentional, not `logger.info`: it's program output, not a
log line. Same reasoning as `generate.run`'s `wrote <path>` lines.

### Starter content (string constants in `init.py`)

```py
_CONFIG_TOML = """\
# Shablon configuration. Uncomment to override defaults.
#
# include = []
# partials_dir = "_includes"
"""

_VARS_SH = """\
#!/usr/bin/env sh
# Print the render context as a JSON object on stdout.
echo '{}'
"""
```

Both use `"""\` to avoid a leading blank line and end with exactly one
trailing newline, matching the project's POSIX-text convention.

**Alternatives considered:**

- Ship starter files under `src/shablon/_starter/` and copy with
  `importlib.resources`. Rejected: two files of <10 lines each don't justify
  the extra packaging step. If starter content grows, revisit.

### Error path mirrors existing pattern

All user-facing errors raise `ShablonError(...)`; `cli.main` already catches
it, logs via `logger.error`, returns exit code 1. No new error machinery.

### `.change.json` for the change directory

The change dir was scaffolded by hand; a `.change.json` was added so
`spexl validate` is clean. No code impact -- noted here so the change
directory is reproducible if regenerated.

## Risks / Trade-offs / Limitations

- **Partial state on mid-write IO error** → acceptable; `ShablonError`
  surfaces to the user. Filesystem cleanup is the user's call. Documenting
  this in the apply-phase test plan, not adding code.
- **Hard-coded `vars.sh` extension** → users on systems without a POSIX
  shell would need to swap it for `vars.py` or similar. Acceptable for v1;
  flagged in the proposal's open decisions.
- **Empty `templates/_includes/`** → Git won't track empty dirs. Users who
  commit shablon scaffolds will see only `templates/` in their first
  commit. Documented behavior, not a defect.

## Open Questions

The three decisions flagged in `proposal.md` (vars language, `.gitkeep`,
`config.toml` content) remain open. This design assumes the proposal's
drafted defaults; revisit if the user chooses differently before apply.
