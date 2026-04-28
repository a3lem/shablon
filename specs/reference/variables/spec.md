# Variables

## Overview

The variables capability governs how shablon resolves the render context passed to every Jinja2 template. Variables come from an optional executable file (`vars.<ext>`) inside `.shablon/`. The file is run as a subprocess; its stdout must be a JSON object whose top-level keys become template variables.

## Scenarios

### Requirement: Optional Variables File
The system SHALL look for an executable file named `vars.<ext>` directly inside `.shablon/`, where `<ext>` is any non-empty extension.

WHEN no such file exists, the system SHALL use an empty render context (`{}`).

#### Scenario: No vars file
  Given `.shablon/` contains no file matching `vars.*`
  When shablon resolves variables
  Then the resolved context is `{}`

#### Scenario: vars.py present
  Given `.shablon/vars.py` exists and is executable
  When shablon resolves variables
  Then shablon executes `.shablon/vars.py`

### Requirement: Single Variables File
IF more than one file matching `vars.*` exists directly in `.shablon/`, the system SHALL exit non-zero with an error naming every matching file.

#### Scenario: Two vars files
  Given `.shablon/vars.py` and `.shablon/vars.sh` both exist
  When shablon resolves variables
  Then shablon exits non-zero
  And stderr names both `vars.py` and `vars.sh`

### Requirement: Variables File Must Be Executable
IF a `vars.<ext>` file exists but is not marked executable, the system SHALL exit non-zero with an error naming the file and instructing the user to make it executable.

#### Scenario: Non-executable vars.py
  Given `.shablon/vars.py` exists with mode `0644`
  When shablon resolves variables
  Then shablon exits non-zero
  And stderr names `vars.py` and mentions the executable bit

### Requirement: Subprocess Contract
WHEN shablon executes the variables file, the system SHALL:

- Invoke it directly by absolute path (relying on the file's shebang or executable format).
- Set the subprocess working directory to the project root (the directory containing `.shablon/`).
- Inherit the parent process environment, plus inject `SHABLON_PROJECT_ROOT` set to the absolute project root path.
- Pass no positional arguments.
- Connect stdin to `/dev/null`.
- Capture stdout for JSON parsing.
- Inherit stderr (the script's stderr streams live to the user's terminal); shablon does not buffer or rewrite it.
- Require exit code 0.

#### Scenario: Successful run
  Given `.shablon/vars.py` is executable, prints `{"version": "1.0"}` to stdout, and exits 0
  When shablon resolves variables
  Then the resolved context is `{"version": "1.0"}`

#### Scenario: Non-zero exit
  Given `.shablon/vars.py` is executable and exits with status 2
  When shablon resolves variables
  Then shablon exits non-zero
  And stderr from `vars.py` has already been streamed to the terminal
  And shablon prints a one-line wrapper naming the failed script and its exit code

#### Scenario: Project root visible to script
  Given `.shablon/` lives at `/proj/.shablon/`
  When shablon executes `vars.py`
  Then the subprocess sees `cwd == /proj`
  And the subprocess sees `SHABLON_PROJECT_ROOT == /proj`
  And the subprocess receives no positional arguments
  And the subprocess's stdin is closed

### Requirement: Stdout Must Be A JSON Object
The system SHALL parse the captured stdout as JSON and require the parsed value to be a JSON object (mapping). Other JSON types (array, string, number, boolean, null) SHALL cause an error.

#### Scenario: Non-object JSON
  Given `vars.py` prints `[1, 2, 3]` to stdout and exits 0
  When shablon parses the output
  Then shablon exits non-zero
  And stderr explains that the variables file must print a JSON object

#### Scenario: Invalid JSON
  Given `vars.py` prints `not json` to stdout and exits 0
  When shablon parses the output
  Then shablon exits non-zero
  And shablon's own stderr names the file and includes the JSON parser error

### Requirement: Top-Level Keys Become Render Variables
The system SHALL pass each top-level key/value pair from the parsed object to every Jinja render as a keyword argument. Nested values are passed through unchanged.

#### Scenario: Nested values preserved
  Given `vars.py` prints `{"project": {"name": "foo", "version": "1.0"}}`
  When shablon renders a template containing `{{ project.name }}`
  Then the output contains `foo`
