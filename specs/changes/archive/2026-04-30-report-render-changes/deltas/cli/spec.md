# CLI

## MODIFIED Requirements

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
