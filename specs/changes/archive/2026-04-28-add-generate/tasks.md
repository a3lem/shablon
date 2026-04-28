# Tasks: add-generate

## Project scaffolding

- [x] Add `jinja2` to `pyproject.toml` dependencies
- [x] Define `ShablonError` exception in `src/shablon/__init__.py`
- [x] Wire `shablon = "shablon:main"` entry point through to `cli.main`

## CLI (`cli.py`)

- [x] argparse with top-level `--cwd PATH` and `generate` subcommand
- [x] Subcommand dispatch in `main()`
- [x] Catch `ShablonError`, print `error: <msg>` to stderr, exit 1
- [x] Let unexpected exceptions propagate as tracebacks

## Project-root discovery (`discovery.py`)

- [x] `find_project_root(start: Path) -> Path` — walk upward, raise on filesystem root

## Config (`config.py`)

- [x] `Config` dataclass with `include: list[str]`, `partials_dir: str = "_includes"`
- [x] `load(shablon_dir)` — handle missing file, empty file, parse errors
- [x] Strict unknown-key check
- [x] Type/shape validation for `include`
- [x] Validation for `partials_dir` (non-empty, no separators, not `.` / `..`)

## Variables (`variables.py`)

- [x] `vars.<ext>` discovery: regex `^vars\.[^./]+$` against direct children of `.shablon/`
- [x] Reject zero-or-more-than-one match per requirement
- [x] Executable-bit check via `os.access(..., os.X_OK)`
- [x] Subprocess invocation: cwd = project root, env + `SHABLON_PROJECT_ROOT`, no argv, `stdin=DEVNULL`, captured stdout, inherited stderr
- [x] JSON parse with object-type assertion
- [x] Error formatting on non-zero exit (script name + exit code; stderr already streamed)

## Template discovery (`discovery.py`)

- [x] `find_templates(template_root, include_patterns, partials_dir)` walker
- [x] Skip ancestor dirs whose basename equals `partials_dir`
- [x] Skip ancestor dirs whose basename starts with `.`
- [x] Skip dotfile leaves unless basename matches an `include` pattern (`fnmatch.fnmatchcase`)
- [x] Follow symlinks via `Path.rglob("*", recurse_symlinks=True)`
- [x] Return absolute paths sorted by relative POSIX path

## Render (`render.py`)

- [x] `build_env(template_root)` with `FileSystemLoader` + `keep_trailing_newline=True` (default `Undefined`)
- [x] `render_to_file(env, rel, output_path, context, source_path)` — render, mkdir parents, write, copy mode bits via `source_path.stat().st_mode & 0o777`

## Generate orchestration (`generate.py`)

- [x] `run(start: Path)` glues discovery → config → variables → render in order
- [x] Print `wrote <rel>` per successful render
- [x] Halt on first error; leave already-written files in place

## Verification

### cli

- [x] Tests for requirement: Generate Subcommand
- [x] Tests for requirement: Project Root Discovery
- [x] Tests for requirement: Missing Configuration Errors Cleanly
- [x] Tests for requirement: Missing Templates Directory Errors Cleanly
- [x] Tests for requirement: Empty Templates Tree Is A No-Op
- [x] Tests for requirement: Errors Halt Generation

### templates

- [x] Tests for requirement: Template Root
- [x] Tests for requirement: Output Path Mirrors Template Path
- [x] Tests for requirement: Parent Directories Are Created
- [x] Tests for requirement: Partials Directories Are Partials Only
- [x] Tests for requirement: Trailing Newline Preserved
- [x] Tests for requirement: Output Overwrites Existing File
- [x] Tests for requirement: Render Context From Variables
- [x] Tests for requirement: Dotfiles Skipped By Default
- [x] Tests for requirement: Deterministic Render Order
- [x] Tests for requirement: Symlinks Are Followed
- [x] Tests for requirement: Output Mode Bits Mirror Template

### variables

- [x] Tests for requirement: Optional Variables File
- [x] Tests for requirement: Single Variables File
- [x] Tests for requirement: Variables File Must Be Executable
- [x] Tests for requirement: Subprocess Contract
- [x] Tests for requirement: Stdout Must Be A JSON Object
- [x] Tests for requirement: Top-Level Keys Become Render Variables

### config

- [x] Tests for requirement: Optional Config File
- [x] Tests for requirement: Config Schema
- [x] Tests for requirement: Strict Validation
- [x] Tests for requirement: Parse Errors Halt Early

## Notes

- Migration of tiquette from `scripts/generate-plugin-files.py` to `uv run shablon generate` is out of scope for this change. It is a useful smoke test once shablon is installable.
- Symlink loops inside the template tree are documented as a user limitation; no detection is implemented.
