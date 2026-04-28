# Design: `shablon generate`

## Overview

Shablon is a thin CLI wrapper around Jinja2. The implementation closely mirrors
tiquette's `scripts/generate-plugin-files.py` but generalises three things:

1. The template root and project root are derived from `.shablon/` instead of
   being hard-coded.
2. The render context is produced by an external executable contract
   (`vars.<ext>` printing a JSON object) rather than baked into the script.
3. The behaviour is exposed as a reusable subcommand on a stable CLI binary.

## Layout

```
src/shablon/
├── __init__.py        # exports `main`, the CLI entry point
├── cli.py             # argparse wiring, subcommand dispatch
├── generate.py        # the generate command: orchestration only
├── discovery.py       # find project root; walk `.shablon/templates/`
├── config.py          # parse + validate `.shablon/config.toml`
├── variables.py       # find + execute `vars.<ext>`, parse JSON
└── render.py          # Jinja2 environment, render + write
```

Each module is small and unit-testable. `generate.py` is a 20-line orchestrator
that calls discovery → variables → render. No module imports the CLI parser, so
each capability can be tested without going through argparse.

## Dependencies

- `jinja2` (runtime) -- the only mandatory third-party dep.
- Standard library for everything else: `argparse`, `subprocess`, `json`,
  `pathlib`, `os`, `stat`, `sys`.

`pyproject.toml` adds `jinja2` to `dependencies` and keeps the `shablon =
"shablon:main"` entry point. `requires-python` stays at `>=3.14`.

## CLI surface

```
shablon [--cwd PATH] generate
```

- `--cwd PATH` is a top-level option (parsed before the subcommand) so we can
  add future subcommands without re-declaring it. Default: `os.getcwd()`.
  This is the **starting point** for the upward search, not the project root.
- `generate` takes no positional arguments and no options in this change. Future
  changes may add `--dry-run`, `--only PATTERN`, etc.

Argparse layout:

```python
parser = argparse.ArgumentParser(prog="shablon")
parser.add_argument("--cwd", type=Path, default=Path.cwd())
sub = parser.add_subparsers(dest="command", required=True)
sub.add_parser("generate", help="Render templates from .shablon/templates/")
```

`main()` dispatches on `args.command`. Today the only branch calls
`generate.run(start=args.cwd)`.

## Project root discovery

`discovery.find_project_root(start: Path) -> Path` walks upward from
`start.resolve()` checking for a `.shablon/` directory:

```python
def find_project_root(start: Path) -> Path:
    current = start.resolve()
    while True:
        if (current / ".shablon").is_dir():
            return current
        if current.parent == current:  # filesystem root
            raise ShablonError(f"no .shablon/ found at {start} or any ancestor")
        current = current.parent
```

This mirrors how `git`, `pyproject`-aware tools, and similar locate their
config root. It never descends, so a sibling project's `.shablon/` is invisible.

## Discovery

`discovery.find_templates(template_root: Path, include_patterns: list[str], partials_dir: str) -> list[Path]`
walks `template_root` and returns every file path that satisfies all of:

1. No ancestor directory under `template_root` has a basename equal to
   `partials_dir` (structural, not overridable by `include` patterns).
2. No ancestor directory under `template_root` has a basename starting with `.`
   (skipped by default; not overridable -- a hidden directory is skipped wholesale).
3. The file's own basename either does not start with `.`, **or** matches at
   least one pattern in `include_patterns` via `fnmatch.fnmatchcase(basename, pattern)`.

The walk uses `Path.rglob("*", recurse_symlinks=True)` (3.13+; you have 3.14),
so symlinked subtrees are first-class. Symlink loops are not detected --
documented as a user limitation.

Returned paths are absolute and sorted ascending by their POSIX-form relative
path (`str(PurePosixPath(p.relative_to(template_root)))`). The caller derives
the relative path for both Jinja's `get_template` (slash-joined) and the output
path.

Why exclude `_includes/` by ancestor name rather than only at the top level:
tiquette nests `_includes/` only at the root today, but we want the convention
to hold at any depth so subtrees can carry their own partials without
exporting them. The same logic applies to dotfile directories.

## Config

`config.load(shablon_dir: Path) -> Config` where `Config` is a small dataclass:

```python
@dataclass(frozen=True)
class Config:
    include: list[str] = field(default_factory=list)
    partials_dir: str = "_includes"
```

1. If `shablon_dir / "config.toml"` does not exist, return `Config()`.
2. Parse with `tomllib.loads(path.read_text("utf-8"))`. On `TOMLDecodeError`,
   raise `ShablonError` with the file path and the parser message.
3. Compute `unknown = set(parsed) - {"include", "partials_dir"}`. Non-empty → raise.
4. `include = parsed.get("include", [])`. Reject if not `list[str]`. Strings
   are stored verbatim; fnmatch re-compiles cheaply per call.
5. `partials_dir = parsed.get("partials_dir", "_includes")`. Reject if not a
   non-empty string, contains `/` or `\`, or equals `"."` / `".."`.

Loading happens before `variables.resolve` so a malformed config halts before
any subprocess is spawned.

## Variables

`variables.resolve(shablon_dir: Path) -> dict[str, Any]`:

1. List entries in `shablon_dir` whose name matches `^vars\.[^./]+$` and which
   are regular files (after symlink resolution).
2. Zero matches → return `{}`.
3. More than one → raise `ShablonError` listing all matches.
4. One match: check `os.access(path, os.X_OK)`; if not executable, raise.
5. Run with:

   ```python
   env = {**os.environ, "SHABLON_PROJECT_ROOT": str(shablon_dir.parent)}
   subprocess.run(
       [str(path)],
       cwd=shablon_dir.parent,        # project root
       env=env,
       stdin=subprocess.DEVNULL,      # closed
       stdout=subprocess.PIPE,        # captured for JSON parse
       stderr=None,                   # inherited (live to user terminal)
       check=False,                   # we want to format our own error
   )
   ```

6. On non-zero exit, raise `ShablonError` with the script name and exit code.
   The script's stderr has already streamed live; we don't replay it.
7. `json.loads(result.stdout)`; if not `isinstance(parsed, dict)`, raise.
8. Return `parsed`.

`ShablonError` is a single internal exception type; `cli.main` catches it,
prints `error: <message>` to stderr, and exits 1.

### Why no allow-list of extensions

The user owns `vars.<ext>`. Python, bash, deno, a compiled binary -- all fine
as long as the OS can execute it directly. Restricting extensions adds nothing
and forecloses use cases.

## Rendering

`render.build_env(template_root: Path) -> Environment`:

```python
Environment(
    loader=FileSystemLoader(template_root),
    keep_trailing_newline=True,
)
```

The default `Undefined` is intentional: missing variables render as empty
strings rather than raising. Validating the rendered output is the user's
responsibility -- shablon does not second-guess what a template "should" have
referenced.

`render.render_to_file(env, template_rel: PurePosixPath, output_path: Path,
context: dict, source_path: Path)`: gets the template, renders with
`**context`, ensures the parent directory exists, writes the result, then
copies the **mode bits** from `source_path` to `output_path`:

```python
mode = source_path.stat().st_mode & 0o777
output_path.chmod(mode)
```

We use `stat()` (not `lstat()`) so symlinked templates take the mode of their
ultimate target, which matches the "follow symlinks transparently" rule. We
copy only the permission bits -- not ownership, not timestamps; those are not
the user's intent.

## Generate orchestration

```python
def run(start: Path) -> None:
    project_root = discovery.find_project_root(start)
    shablon_dir = project_root / ".shablon"
    template_root = shablon_dir / "templates"
    _require_dir(template_root, label=".shablon/templates")

    cfg = config.load(shablon_dir)              # may raise (parse / schema)
    context = variables.resolve(shablon_dir)    # may raise
    env = render.build_env(template_root)
    templates = discovery.find_templates(template_root, cfg.include, cfg.partials_dir)

    for template_path in templates:
        rel = PurePosixPath(template_path.relative_to(template_root).as_posix())
        output_path = project_root / rel
        render.render_to_file(env, rel, output_path, context, template_path)
        print(f"wrote {rel}")
```

Order is deliberate: config first (cheap; catches typos before any subprocess
or render work), variables next (catches user-script bugs before partial
output), templates last. Any exception aborts the loop with already-written
files left in place, matching the CLI delta's "Errors Halt Generation"
requirement.

Failure mode matches the spec: any exception aborts the loop with files written
so far left in place. The CLI layer turns `ShablonError` and `TemplateError`
into a clean stderr message; everything else propagates as a traceback (genuine
bugs in shablon).

## Testing strategy

- `tests/test_discovery.py` -- project-root upward walk (root, nested cwd,
  sibling invisibility, no `.shablon/` anywhere); template discovery
  (`_includes/` at top and nested, dotfile skip, `include` re-enable, sort
  order, symlinked subtree).
- `tests/test_config.py` -- missing file, empty file, valid include, valid
  custom `partials_dir`, unknown key, wrong type for `include`, invalid
  `partials_dir` (empty, separator, `.`, `..`), malformed TOML.
- `tests/test_variables.py` -- temp `vars.sh` scripts (shebang `#!/bin/sh`)
  covering: missing, multiple, non-executable, non-zero exit, non-object JSON,
  invalid JSON, happy path. Also: cwd is project root, `SHABLON_PROJECT_ROOT`
  is set, stdin is closed.
- `tests/test_render.py` -- in-memory env tests for `keep_trailing_newline`,
  default `Undefined` (missing variable renders as empty string), `_includes`
  resolution, mode-bit mirroring (chmod a fixture template `0755` and assert
  output mode).
- `tests/test_generate.py` -- end-to-end: tmp project with `.shablon/`, run
  `shablon.generate.run(start=tmp)`, assert files written and modes match.
- `tests/test_cli.py` -- subprocess-driven smoke test of the installed
  `shablon` entry point against a fixture project.

Each test annotates the spec it covers, e.g.
`# spec: variables requirement="Single Variables File" scenario="Two vars files"`.

## Migration: tiquette adopts shablon

After shablon ships, tiquette's `scripts/generate-plugin-files.py` becomes:

```
.shablon/
├── templates/        # moved from plugin_src/templates/
└── vars.py           # produces {"help_text": ..., "version": ...}
```

`scripts/generate-plugin-files.py` is replaced by `uv run shablon generate`.
This is out of scope for this change but informs the design: the CLI must be
expressive enough that tiquette no longer needs a custom script.

## Open questions

- **Output cleanup.** Should generate ever delete files that no longer have a
  template? Out of scope; we always write, never delete. Users can `git clean`
  if they need it.
