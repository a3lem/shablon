---
name: use-shablon
description: How to use the `shablon` CLI to render Jinja2 templates from a `.shablon/` directory into a project tree. Covers `shablon init` for first-time scaffolding, the `.shablon/` layout (templates/, vars.<ext>, config.toml, _includes/ partials), the executable variables-file contract, and `shablon generate` for rendering. Use this skill whenever the user mentions shablon, asks to scaffold or render templates from `.shablon/`, wants to set up project-wide file generation from a single source of truth, sees a `.shablon/` directory in their repo, hits an error from the `shablon` command, or asks how to template repeated files (agent assets, hook scripts, plugin manifests, doc stubs) across a project. Trigger even when the user does not name "shablon" explicitly but describes the task ("render these jinja templates into the repo from a manifest", "I have a vars.py that should drive a bunch of file generation").
---

# Using shablon

Shablon is a small CLI for projects that need to generate many files from
Jinja2 templates plus a single context object. It promotes the
"templates plus a vars script" pattern into a standalone tool. One
`.shablon/` directory contains everything; the CLI does the rest.

If you are setting up shablon for a new project, jump to **Bootstrap**.
If `.shablon/` already exists, jump to **Render** and the **Reference**
sections. If a command failed and you are debugging, jump to
**Troubleshooting**.

## Mental model

A shablon project has one directory at the project root:

```
.shablon/
├── config.toml          # optional, schema below
├── vars.<ext>           # optional, executable, prints JSON object on stdout
└── templates/           # required
    ├── _includes/       # partials (configurable name)
    └── …                # everything else here is rendered to <project>/<same path>
```

Running `shablon generate` from anywhere inside the project walks
upward and stops at the **nearest** ancestor containing `.shablon/`
(siblings are never discovered). It then executes `vars.<ext>` to
build a render context, parses `config.toml`, and renders every file
under `templates/` (skipping `_includes/` and dotfiles) to the
matching path under the project root. Output mode bits mirror the
template's, so an executable template produces an executable output.

There is no flag to override the working directory. To run shablon
against a project, `cd` into it (or any subdirectory) first.

The key insight: **the templates directory's layout is the output
layout**. There is no separate manifest of "render this to that". The
filesystem is the manifest.

## Bootstrap

For a brand-new project, scaffold the convention with one command:

```sh
shablon init
```

This creates `.shablon/` at the current working directory with a
starter `config.toml`, an executable `vars.sh` printing `{}`, and an
empty `templates/_includes/`. `shablon init` refuses to run if
`.shablon/` already exists -- it never overwrites.

To scaffold somewhere other than the current directory, `cd` there first:
`shablon` has no flag to override the working directory.

After `init`, the user typically:

1. Edits `vars.sh` (or replaces it with `vars.py`, `vars.ts`, etc.) so
   it prints the context the templates will need.
2. Drops Jinja2 templates under `.shablon/templates/`, mirroring the
   layout they want generated at the project root.
3. Runs `shablon generate` to render.

## Migrating an existing template setup

Many projects already have an ad-hoc "Jinja templates plus a build
script" arrangement (e.g., `templates/` rendered by
`scripts/generate.py`). The migration is mechanical:

| Old | New |
|---|---|
| `templates/` (template root) | `.shablon/templates/` |
| The build script's context-building logic | `.shablon/vars.py` (executable, prints JSON object) |
| A manifest of "render X to Y" | The filesystem layout under `.shablon/templates/` |
| `uv run scripts/generate.py` in justfile/Makefile | `shablon generate` |

Recommended sequence:

1. Snapshot the current output: `cp -r <output-dir> /tmp/baseline`.
2. Move templates: `mkdir -p .shablon && mv templates .shablon/templates`.
3. Translate the build script into `.shablon/vars.py` (or `vars.sh`,
   etc.). Make it executable. Use `SHABLON_PROJECT_ROOT` to locate
   project files.
4. Run `shablon generate`.
5. `diff -r /tmp/baseline <output-dir>` to confirm parity. Expect
   zero diff -- if there is one, fix it before deleting the old
   pipeline.
6. Delete the old build script and any now-empty source directories.
7. Replace the old invocation in the task runner with `shablon
   generate`.

Common gotcha: the old script may have rendered files that are not
templates (a hand-written `hooks.json`, say). Those belong outside
`.shablon/templates/` -- shablon never touches files it did not
render.

## Invoking shablon

Shablon is a tool you run *against* arbitrary projects, but those
projects rarely depend on it. Three ways to invoke it, in order of
preference:

1. **Globally installed** (`uv tool install shablon`, `pipx install
   shablon`, etc.): just run `shablon generate`. Best for routine use.
2. **`uvx shablon generate`**: ephemeral, no install. Good for one-off
   trials or CI.
3. **From a local checkout**: `uv --project /path/to/shablon-checkout
   run shablon generate`. Useful while developing shablon itself
   against a real consumer project.

The consumer project's own `pyproject.toml` does **not** need to
declare shablon as a dependency. Shablon reads `.shablon/` and writes
files; it doesn't import anything from the project.

## Render

From inside a configured project:

```sh
shablon generate
```

Outputs one `wrote <path>` line per rendered file on stdout, in
deterministic lexicographic order. Exit code 0 on success, 1 on any
error (with a clear stderr message naming the failing input).

`shablon generate` is idempotent: rerunning it overwrites previously
rendered files in place. Edit a template, rerun, see the change. Edit
`vars.<ext>`, rerun, see the change. There is no separate clean step.

### Wiring into a task runner

Most projects already have a `justfile`, `Makefile`, or similar.
Replace the existing render step with a one-liner:

```just
plugins:
    shablon generate
```

```make
plugins:
	shablon generate
```

## The variables file

`vars.<ext>` is the user's escape hatch. **It can be any executable
file** -- a shell script, a Python script, a Node script, a Deno
script, a Ruby script, a compiled Go/Rust binary, a thin wrapper that
shells out to a Makefile target. Shablon does not parse it, does not
import it, and does not care what language it is in. It just runs it
and reads the JSON object on its stdout.

The only requirements:

- The file lives directly in `.shablon/` (not nested).
- The basename starts with `vars.` -- the extension is purely for the
  human reader (`vars.sh`, `vars.py`, `vars.ts`, `vars.rb`, `vars.go`,
  even `vars.bin` for a compiled binary all work the same).
- It has the executable bit set (`chmod +x .shablon/vars.<ext>`).
- For interpreted scripts, it begins with a shebang
  (`#!/usr/bin/env python3`, `#!/usr/bin/env -S deno run --allow-all`,
  etc.) so the kernel knows how to launch it. Compiled binaries don't
  need one.
- It prints a JSON **object** to stdout. Other JSON types (array, string,
  number, boolean, null) are rejected.
- It exits with status 0.

Shablon invokes the file by absolute path with no positional arguments.
The subprocess sees:

- `cwd` set to the project root (the dir containing `.shablon/`).
- An additional environment variable `SHABLON_PROJECT_ROOT` with the
  absolute project root path.
- Inherited stderr (the user sees the script's errors directly).
- `stdin` closed.

The top-level keys of the printed object become Jinja variables.
Nested values pass through unchanged, so `{"project": {"name": "foo"}}`
makes `{{ project.name }}` resolve to `foo` in templates.

If no `vars.<ext>` exists, the render context is `{}` -- templates that
reference no variables still work. If multiple `vars.*` files exist,
shablon errors out; pick one.

### Example `vars.sh`

```sh
#!/usr/bin/env sh
echo '{"project": {"name": "myproj", "version": "0.1.0"}}'
```

### Example `vars.py`

Prefer `SHABLON_PROJECT_ROOT` over deriving the root from `__file__`:
shablon already located the root, the env var survives `vars.py`
moving inside `.shablon/`, and the script can shell out to project
tools without guessing where they live.

```python
#!/usr/bin/env python3
import json, os, pathlib, subprocess, tomllib

root = pathlib.Path(os.environ["SHABLON_PROJECT_ROOT"])
pyproject = tomllib.loads((root / "pyproject.toml").read_text())
help_text = subprocess.run(
    ["mytool", "--help"], capture_output=True, text=True, check=True,
).stdout

print(json.dumps({
    "project": pyproject["project"],
    "help_text": help_text,
}))
```

## Templates and partials

Anything under `.shablon/templates/` is a Jinja2 template root. Files
render to the matching path under the project root. Subdirectories are
created as needed.

Two kinds of files are skipped:

1. **Partials**: any directory named `_includes` (configurable; see
   **Config**) at any depth contains partials, available via
   `{% include "_includes/header.md" %}` but never rendered as
   standalone outputs. The exclusion is structural -- `include`
   patterns cannot resurrect a partial as an output.
2. **Dotfiles**: any path whose basename starts with `.` is skipped by
   default. Useful for `.DS_Store`, editor backups, etc. Re-enable
   specific dotfiles via the `include` config field.

Templates render with `keep_trailing_newline=True`, so files end with
the same single trailing newline as the source.

Symlinks under `templates/` are followed. The output is always a
regular file, never a symlink.

## Config

`.shablon/config.toml` is optional. Two recognised keys:

```toml
# basename patterns (fnmatch) that re-enable specific dotfiles.
include = [".gitignore", ".env*"]

# partials directory basename. Default: "_includes".
partials_dir = "_includes"
```

Constraints:

- `include` must be an array of strings.
- `partials_dir` must be a non-empty string with no path separators,
  not `.` or `..`.
- Unknown top-level keys are rejected (typo protection).

Missing or empty `config.toml` resolves to defaults (no extra includes,
`partials_dir = "_includes"`).

## End-to-end example

Goal: every plugin under `plugins/` should get an `AGENTS.md` and a
`hooks/prime.md` rendered from the same templates, parameterised by
project metadata.

```
.shablon/
├── vars.py                           # prints {"project": {...}}
└── templates/
    ├── _includes/
    │   └── header.md                 # shared header partial
    └── plugins/
        └── claude/
            ├── AGENTS.md             # uses {% include "_includes/header.md" %}
            └── hooks/
                └── prime.md
```

Running `shablon generate` from the project root produces:

```
plugins/claude/AGENTS.md
plugins/claude/hooks/prime.md
```

If `vars.py` later changes `project.version`, the next `shablon
generate` updates both files in place.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `error: no .shablon/ found at <path> or any ancestor` | Running from outside any shablon project, or `.shablon/` is misnamed (must be exactly `.shablon`). |
| `error: <…>/templates not found; .shablon/templates/ is required` | `.shablon/` exists but `templates/` is missing -- create it. |
| `error: <vars.x> is not executable; run \`chmod +x …\`` | Variables file lacks the executable bit. |
| `error: <vars.x> exited with status N` | The user's script failed. Its own stderr was already streamed; check it for the underlying error. |
| `error: <vars.x> produced invalid JSON on stdout` / `must print a JSON object` | Script printed non-JSON or a non-object (array, scalar). Wrap in `{ ... }`. |
| `error: more than one vars.<ext> file in .shablon/` | Two competing files (e.g., `vars.py` and `vars.sh`). Delete one. |
| `error: <config.toml>: unknown top-level key(s): …` | Typo or unrecognised key. Only `include` and `partials_dir` are accepted. |
| Template that should be rendered is missing from output | (a) basename starts with `.` and is not in `include`, or (b) it lives under `_includes/` (or whatever `partials_dir` is set to). |
| Rendered file has wrong newline / mode | Mode is copied from the source template. To make output executable, `chmod +x` the source template. |

## Things shablon does not do

Save the user time by not promising features that do not exist:

- No watch mode, no dry-run, no diff. Just `generate`.
- No per-template variables / front-matter. One context for all
  templates.
- No layered config. One `vars.<ext>`. One `config.toml`.
- No outputs outside the project root. Templates always render relative
  to the directory containing `.shablon/`.
- No `clean` command. Generated files are normal files; remove with
  whatever tool the user prefers.

If the user asks for these, suggest scripting around `shablon
generate` (e.g., `entr`, `make`, a pre-commit hook) rather than
inventing flags that do not exist.
