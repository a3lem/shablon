# CLI

## ADDED Requirements

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
