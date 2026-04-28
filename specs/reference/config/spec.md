# Config

## Overview

The config capability governs how shablon reads and validates `.shablon/config.toml`. All fields are optional; the file itself is optional. Validation errors halt execution before any templates are rendered or variables are resolved.

## Scenarios

### Requirement: Optional Config File
The system SHALL look for a file at `.shablon/config.toml`. WHEN it does not exist, the system SHALL behave as though every field were set to its default.

#### Scenario: No config file
  Given `.shablon/` contains no `config.toml`
  When shablon resolves configuration
  Then the resolved config has `include = []` and `partials_dir = "_includes"`

#### Scenario: Empty config file
  Given `.shablon/config.toml` exists and is empty
  When shablon resolves configuration
  Then the resolved config has `include = []` and `partials_dir = "_includes"`

### Requirement: Config Schema
The system SHALL recognise exactly two top-level fields in `config.toml`:

- `include` — an array of strings. Each string is an `fnmatch`-style pattern matched against the **basename** of a discovered template file. A file whose basename starts with `.` is re-included in rendering iff it matches at least one `include` pattern. Patterns SHALL NOT affect the structural partials-directory exclusion.
- `partials_dir` — a string naming the directory basename treated as the partials directory. Default: `"_includes"`. The value SHALL be a non-empty string with no path separators (`/` or `\`) and SHALL NOT be `"."` or `".."`.

#### Scenario: Re-include .gitignore everywhere
  Given `.shablon/config.toml` contains `include = [".gitignore"]`
  And templates `a/.gitignore` and `b/c/.gitignore` exist
  When shablon discovers templates
  Then both `.gitignore` files are rendered

#### Scenario: Pattern with wildcard
  Given `.shablon/config.toml` contains `include = [".env*"]`
  And templates `cfg/.env` and `cfg/.envrc` exist
  When shablon discovers templates
  Then both files are rendered

#### Scenario: Custom partials directory
  Given `.shablon/config.toml` contains `partials_dir = "_partials"`
  And `.shablon/templates/_partials/header.md` exists
  And `.shablon/templates/_includes/note.md` exists
  When shablon discovers templates
  Then `_partials/header.md` is not rendered
  And `_includes/note.md` is rendered to `<root>/_includes/note.md`

### Requirement: Strict Validation
IF `config.toml` contains any top-level key other than `include` or `partials_dir`, the system SHALL exit non-zero with an error naming the file path and every offending key.

IF the value of `include` is not an array of strings, the system SHALL exit non-zero with an error naming the file path and the offending field.

IF the value of `partials_dir` is not a string, is empty, contains a path separator, or equals `"."` or `".."`, the system SHALL exit non-zero with an error naming the file path and the offending value.

#### Scenario: Unknown key
  Given `.shablon/config.toml` contains `inculde = [".env"]` (typo)
  When shablon validates the config
  Then shablon exits non-zero
  And stderr names `config.toml` and the unknown key `inculde`

#### Scenario: Wrong type for include
  Given `.shablon/config.toml` contains `include = ".env"` (string, not array)
  When shablon validates the config
  Then shablon exits non-zero
  And stderr names `config.toml` and the field `include`

#### Scenario: partials_dir with path separator
  Given `.shablon/config.toml` contains `partials_dir = "shared/_partials"`
  When shablon validates the config
  Then shablon exits non-zero
  And stderr names `config.toml` and the offending value

### Requirement: Parse Errors Halt Early
IF `config.toml` is not valid TOML, the system SHALL exit non-zero before executing the variables file or rendering any templates, with an error naming the file and the parser's diagnostic.

#### Scenario: Malformed TOML
  Given `.shablon/config.toml` contains `include = [` (unterminated array)
  When shablon validates the config
  Then shablon exits non-zero
  And no `vars.<ext>` is executed
  And no templates are rendered
