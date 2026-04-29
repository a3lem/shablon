# CLI

## ADDED Requirements

### Requirement: Init Subcommand
The system SHALL expose a `shablon init` subcommand that scaffolds a new `.shablon/` directory at the target location.

The target location is the directory passed via `--cwd` (or the process working directory when `--cwd` is omitted). Unlike `generate`, `init` SHALL NOT walk upward; it operates only on the target directory.

#### Scenario: Default invocation
  Given an empty directory `/proj` with no `.shablon/`
  When the user runs `shablon init` from `/proj`
  Then `/proj/.shablon/` is created
  And `/proj/.shablon/config.toml` exists
  And `/proj/.shablon/vars.sh` exists and is executable
  And `/proj/.shablon/templates/` exists as a directory
  And `/proj/.shablon/templates/_includes/` exists as a directory
  And shablon exits with status 0

#### Scenario: Explicit cwd
  Given an empty directory `/elsewhere`
  When the user runs `shablon init --cwd /elsewhere` from any directory
  Then `/elsewhere/.shablon/` is created
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

### Requirement: Init Refuses Missing Target Directory
IF the target directory passed via `--cwd` does not exist or is not a directory, the system SHALL exit non-zero with an error naming the path.

#### Scenario: Non-existent --cwd
  Given `/does/not/exist` is not a directory
  When the user runs `shablon init --cwd /does/not/exist`
  Then shablon exits with status 1
  And stderr names `/does/not/exist`

### Requirement: Starter `config.toml`
The system SHALL create `.shablon/config.toml` containing the two recognised configuration keys as commented-out lines showing their default values, so the file documents the schema while leaving every field at its default.

#### Scenario: Generated config is valid and uses defaults
  Given a freshly run `shablon init`
  When the user runs `shablon generate` against the new project
  Then config loading succeeds
  And `partials_dir` resolves to `_includes`
  And `include` resolves to the empty list

### Requirement: Starter `vars.sh`
The system SHALL create `.shablon/vars.sh` as an executable script (mode `0755`) whose stdout is the JSON object `{}`, satisfying the `variables` capability's subprocess contract out of the box.

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
