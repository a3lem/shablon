# CLI

## ADDED Requirements

### Requirement: Generate Subcommand
The system SHALL expose a `shablon generate` subcommand as the entry point for
template rendering.

#### Scenario: Invoking generate from a configured project
  Given a project containing a valid `.shablon/templates/` directory
  When the user runs `shablon generate` from the project root
  Then shablon renders every template and exits with status 0
  And shablon prints one line per rendered file in the form `wrote <relative-path>` to stdout

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

### Requirement: Project Root Discovery
The system SHALL locate the project root by searching for a `.shablon/` directory starting at the current working directory and walking upward through parent directories until one is found or the filesystem root is reached. The system SHALL NOT descend into subdirectories during this search.

The directory containing `.shablon/` is the **project root** for the run; outputs are written relative to it.

WHERE the user passes `--cwd <path>`, the system SHALL begin the upward walk at `<path>` instead of the current working directory.

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

#### Scenario: Explicit cwd
  Given a project root `/elsewhere` containing `.shablon/`
  When the user runs `shablon generate --cwd /elsewhere/src` from any directory
  Then shablon begins the upward walk at `/elsewhere/src`
  And selects `/elsewhere` as the project root

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
