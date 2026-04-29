# shablon

A small CLI for generating project files from Jinja2 templates. Templates live under `.shablon/templates/`, and each one renders to the matching path under your project root -- `.shablon/templates/foo/bar.md` becomes `foo/bar.md`. 
Inspired by code generators like protobuf (one canonical source, many target outputs).

## Install

```sh
uv tool install git+https://github.com/a3lem/shablon       # global
# or
uvx --from git+https://github.com/a3lem/shablon shablon    # ephemeral
```

## Walkthrough

Scaffold a fresh project:

```sh
$ mkdir my-cli && cd my-cli
$ shablon init
initialized /.../my-cli/.shablon
```

State after `init`:

```
my-cli/
└── .shablon/
    ├── config.toml
    ├── vars.sh           # Executable, prints '{}'. Optional.
    └── templates/
        └── _includes/
```

Add a partial, a `vars.sh`, and two templates that share the partial:

```jinja
{# .shablon/templates/_includes/usage.md #}
Use `{{ cli.name }}` (v{{ cli.version }}) to track tickets in `.tickets/`.
```

```sh
# .shablon/vars.sh
#!/usr/bin/env sh
echo '{"cli": {"name": "tiquette", "version": "0.4.0"}}'
```

```jinja
{# .shablon/templates/plugins/claude/AGENTS.md #}
# {{ cli.name }} plugin (Claude Code)

{% include "_includes/usage.md" %}

Track work via the `Bash(tq ...)` tool.
```

```jinja
{# .shablon/templates/plugins/opencode/AGENTS.md #}
# {{ cli.name }} plugin (OpenCode)

{% include "_includes/usage.md" %}

Track work by running `tq` in a shell tool call.
```

Render. Each template's output path is its path relative to `.shablon/templates/`, written under the project root. The `_includes/` subtree is skipped -- partials only get pulled in by `{% include %}`.

```sh
$ shablon generate
wrote plugins/claude/AGENTS.md
wrote plugins/opencode/AGENTS.md
```

After:

```
my-cli/
├── .shablon/                         # unchanged
└── plugins/                          # generated
    ├── claude/
    │   └── AGENTS.md
    └── opencode/
        └── AGENTS.md
```

Both outputs share the usage paragraph (from the partial, parameterized by `vars.sh`) and differ only where the agent calling convention does. Re-run `shablon generate` after edits to update outputs in place.

## How it works

- **Path rule**: a template at `.shablon/templates/<path>` renders to `<project-root>/<path>`. Parent directories are created as needed; existing files are overwritten.
- **Partials**: any directory named `_includes` (configurable via `partials_dir` in `config.toml`) at any depth holds partials. Available to `{% include %}` and `{% extends %}`, never rendered as outputs.
- **Dotfiles**: paths whose basename starts with `.` are skipped by default. Re-enable specific ones via the `include` array in `config.toml` (basename `fnmatch` patterns).
- **Variables**: `.shablon/vars.<ext>` is any executable file (shell, Python, Node, a compiled binary). Shablon runs it with `cwd` set to the project root and `SHABLON_PROJECT_ROOT` injected; it must print a JSON object on stdout. Top-level keys become Jinja variables. If absent, the render context is `{}`.
- **Discovery**: `shablon generate` walks upward from the working directory and stops at the nearest ancestor containing `.shablon/`. Sibling directories are not searched. There is no flag to override the working directory -- `cd` to where you want to run.
- **File mode**: outputs inherit their template's mode bits; `chmod +x` the source to get an executable output.
- **Newlines**: shablon renders with `keep_trailing_newline=True`; outputs end with the same single trailing newline as the source.

## Why I built this

I maintain several CLIs designed for use by AI coding agents (e.g. [`tiquette`](github.com/a3lem/tiquette)). Each ships with a companion plugin: rules injected into the system prompt, plus one or more [skills](agentskills.io) that progressively disclose how to use the CLI.

I want each CLI to ship plugins for multiple coding agents (Claude Code, OpenCode, Pi, ...). Two sources of friction:

1. **The agents differ.** Plugin layouts, supported artifact types, and system-prompt injection mechanisms all vary.
2. **The prompts differ.** Wording often needs per-agent tweaks (tool names, file paths, conventions).

I need a way to manage these per-agent variants while keeping the shared content DRY: write a rule, a skill, or parts of a hook script once, and reuse it across every agent's plugin tree.

## Using shablon with AI coding agents

A `use-shablon` skill ships at `skills/use-shablon/`. Install it into your agent of choice.

### Claude Code

Add the marketplace.

```
claude plugin marketplace add a3lem/shablon
```

Then install the `shablon` plugin.

```
/plugin install shablon@shablon-marketplace
```

## Status

Pre-1.0. The CLI surface and `.shablon/` schema are still evolving; see [CHANGELOG.md](CHANGELOG.md).

## License

MIT

## AI usage notice

Unsurprisingly, the code in this project is written mostly by AI.
