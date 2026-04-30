# CLI

## Overview

The CLI is the user-facing entry point for shablon. It exposes subcommands for template rendering and project scaffolding, and provides consistent error reporting, project root discovery, and help output.

All subcommands operate relative to the process working directory. `generate` walks upward from the working directory to locate `.shablon/`; `init` scaffolds `.shablon/` directly in the working directory. There is no flag to override the working directory -- the user must `cd` to the desired location.

## Scenarios

### Requirement: Generate Subcommand
The system SHALL expose a `shablon generate` subcommand as the entry point for template rendering.

For each discovered template, shablon SHALL print exactly one line to stdout indicating the outcome:

- `wrote <relative-path>` -- the output file was created or its content/mode differed from the new render and was overwritten.
- `unchanged <relative-path>` -- the rendered bytes and mode bits already matched the file on disk; no write was performed.

Lines SHALL appear in the deterministic render order defined by the `templates` capability.

#### Scenario: Invoking generate from a configured project
  Given a project containing a valid `.shablon/templates/` directory
  When the user runs `shablon generate` from the project root
  Then shablon processes every template and exits with status 0
  And shablon prints one line per template to stdout, prefixed `wrote ` or `unchanged ` depending on whether the file changed

#### Scenario: First run writes everything
  Given a project where no rendered outputs exist yet
  When the user runs `shablon generate`
  Then every line on stdout is prefixed `wrote `
  And no line is prefixed `unchanged `

#### Scenario: Immediate re-run reports everything unchanged
  Given a project where `shablon generate` has just been run successfully
  When the user runs `shablon generate` a second time without modifying any template or variable
  Then every line on stdout is prefixed `unchanged `
  And no line is prefixed `wrote `

#### Scenario: Partial re-run reports per-file outcome
  Given a project where `shablon generate` has been run, then exactly one template was edited
  When the user runs `shablon generate` again
  Then the edited template's line is prefixed `wrote `
  And every other line is prefixed `unchanged `

#### Scenario: Help output
  Given the user runs `shablon --help`
  When the help text is printed
  Then `generate` is listed as an available subcommand

### Requirement: Bare Invocation Prints Help
WHEN the user runs `shablon` with no subcommand, the system SHALL print the help text to stderr and exit with status 1.

#### Scenario: No subcommand
  Given the user runs `shablon` with no arguments
  Then the help text is printed to stderr
  And shablon exits with status 1

### Requirement: Version Flag
The system SHALL expose a top-level `--version` flag that prints `shablon <version>` to stdout and exits with status 0, where `<version>` matches `shablon.__version__`.

The flag SHALL work without a subcommand and SHALL NOT require a configured project (no `.shablon/` lookup is performed).

#### Scenario: --version prints the installed version
  Given shablon is installed at version `X.Y.Z`
  When the user runs `shablon --version` from any directory
  Then stdout contains `shablon X.Y.Z`
  And shablon exits with status 0

#### Scenario: --version works outside a project
  Given the user runs `shablon --version` from a directory with no `.shablon/` on the path
  Then shablon exits with status 0
  And no error is printed to stderr

### Requirement: Project Root Discovery
The system SHALL locate the project root by searching for a `.shablon/` directory starting at the current working directory and walking upward through parent directories until one is found or the filesystem root is reached. The system SHALL stop at the first ancestor containing `.shablon/` and select that directory as the project root. The system SHALL NOT descend into subdirectories during this search.

The directory containing `.shablon/` is the **project root** for the run; outputs are written relative to it.

#### Scenario: Run from project root
  Given a project root `/proj` containing `.shablon/`
  When the user runs `shablon generate` from `/proj`
  Then `/proj` is selected as the project root
  And outputs are written under `/proj`

#### Scenario: Run from nested subdirectory
  Given a project root `/proj` containing `.shablon/`
  When the user runs `shablon generate` from `/proj/src/deep/nested`
  Then shablon walks upward and selects `/proj` as the project root
  And outputs are written under `/proj`

#### Scenario: Discovery stops at the nearest .shablon
  Given `/proj/.shablon/` and `/proj/sub/.shablon/` both exist
  When the user runs `shablon generate` from `/proj/sub/deeper`
  Then `/proj/sub` is selected as the project root
  And `/proj/.shablon/` is not consulted

#### Scenario: Sibling .shablon is not discovered
  Given `/proj/.shablon/` exists but the user runs from `/other/` (a sibling, not a descendant)
  When shablon walks upward from `/other/`
  Then `/proj/.shablon/` is not found
  And shablon exits non-zero

### Requirement: Missing Configuration Errors Cleanly
IF no `.shablon/` directory is found at the starting path or any of its ancestors up to the filesystem root, the system SHALL exit with a non-zero status and print a clear error to stderr naming the starting path.

#### Scenario: No .shablon anywhere on the path
  Given no `.shablon/` exists at the starting path or any ancestor
  When the user runs `shablon generate`
  Then shablon exits with status 1
  And stderr explains that no `.shablon/` was found, including the starting path

### Requirement: Missing Templates Directory Errors Cleanly
IF `.shablon/` exists but `.shablon/templates/` does not, the system SHALL exit with a non-zero status and print a clear error to stderr.

#### Scenario: Empty .shablon directory
  Given a `.shablon/` directory that contains no `templates/` subdirectory
  When the user runs `shablon generate`
  Then shablon exits with status 1
  And stderr explains that `.shablon/templates/` is required

### Requirement: Empty Templates Tree Is A No-Op
WHEN `.shablon/templates/` exists but contains no renderable templates, the system SHALL exit with status 0 without writing any files.

#### Scenario: Templates directory contains only `_includes/`
  Given `.shablon/templates/_includes/foo.md` exists and no other templates
  When the user runs `shablon generate`
  Then shablon writes nothing
  And shablon exits with status 0

### Requirement: Errors Halt Generation
IF rendering, variable resolution, or template discovery raises an error for any template, the system SHALL stop, leave any already-written files in place, print the failing template path and underlying error to stderr, and exit non-zero.

#### Scenario: Jinja syntax error in second template
  Given two templates where the second contains a Jinja syntax error
  When the user runs `shablon generate`
  Then the first template is written
  And the second template is reported on stderr with its path
  And shablon exits with a non-zero status

### Requirement: Init Subcommand
The system SHALL expose a `shablon init` subcommand that scaffolds a new `.shablon/` directory in the current working directory.

Unlike `generate`, `init` SHALL NOT walk upward; it operates only on the working directory.

#### Scenario: Default invocation
  Given an empty directory `/proj` with no `.shablon/`
  When the user runs `shablon init` from `/proj`
  Then `/proj/.shablon/` is created
  And `/proj/.shablon/config.toml` exists
  And `/proj/.shablon/vars.sh` exists and is executable
  And `/proj/.shablon/templates/` exists as a directory
  And `/proj/.shablon/templates/_includes/` exists as a directory
  And shablon exits with status 0

#### Scenario: Help output
  Given the user runs `shablon --help`
  When the help text is printed
  Then `init` is listed as an available subcommand alongside `generate`

### Requirement: Init Refuses Existing `.shablon/`
IF the target directory already contains a `.shablon/` entry (file, directory, or symlink), the system SHALL exit non-zero with an error naming the path and SHALL NOT modify any file inside it.

#### Scenario: Existing .shablon directory
  Given `/proj/.shablon/` already exists as a directory
  When the user runs `shablon init` from `/proj`
  Then shablon exits with status 1
  And stderr names `/proj/.shablon` and explains that it already exists
  And no file inside `/proj/.shablon/` is created or modified

#### Scenario: .shablon exists as a file
  Given `/proj/.shablon` exists as a regular file (not a directory)
  When the user runs `shablon init` from `/proj`
  Then shablon exits with status 1
  And the existing file is left untouched

### Requirement: Starter `config.toml`
The system SHALL create `.shablon/config.toml` containing the two recognised configuration keys as commented-out lines showing their default values, so the file documents the schema while leaving every field at its default.

#### Scenario: Generated config is valid and uses defaults
  Given a freshly run `shablon init`
  When the user runs `shablon generate` against the new project
  Then config loading succeeds
  And `partials_dir` resolves to `_includes`
  And `include` resolves to the empty list

### Requirement: Starter `vars.sh`
The system SHALL create `.shablon/vars.sh` as an executable script (mode `0755`) whose stdout is the JSON object `{}`, satisfying the `variables` capability's subprocess contract out of the box. The file SHALL begin with a POSIX shell shebang line (e.g., `#!/usr/bin/env sh`) so that direct invocation by absolute path -- as required by the `variables` subprocess contract -- succeeds without relying on the caller's shell.

#### Scenario: Generated vars.sh runs cleanly
  Given a freshly run `shablon init`
  When the user runs `shablon generate` against the new project
  Then variable resolution succeeds with an empty render context

#### Scenario: Generated vars.sh is executable
  Given a freshly run `shablon init`
  When the user inspects `.shablon/vars.sh`
  Then its mode bits include the owner-execute bit

### Requirement: Starter `templates/` Tree
The system SHALL create `.shablon/templates/` and `.shablon/templates/_includes/` as empty directories. The system SHALL NOT create any starter template or partial file inside them.

#### Scenario: Empty templates tree
  Given a freshly run `shablon init`
  When the user lists `.shablon/templates/`
  Then `_includes/` is the only entry
  And `_includes/` is empty
