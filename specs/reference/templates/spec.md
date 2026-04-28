# Templates

## Overview

The templates capability governs how shablon discovers, filters, renders, and writes template files. Templates live under `.shablon/templates/` and are rendered with Jinja2. Discovery rules control which files are treated as renderable outputs versus partials or excluded files.

## Scenarios

### Requirement: Template Root
The system SHALL treat `.shablon/templates/` as the Jinja2 template root for both discovery and `{% include %}` / `{% extends %}` resolution.

#### Scenario: Include from sibling partial
  Given `.shablon/templates/skills/foo/SKILL.md` contains `{% include "_includes/header.md" %}`
  And `.shablon/templates/_includes/header.md` exists
  When shablon renders `skills/foo/SKILL.md`
  Then the partial content is substituted at render time

### Requirement: Output Path Mirrors Template Path
The system SHALL write each rendered template to the path obtained by joining the project root (as defined by the `cli` capability) with the template's path relative to `.shablon/templates/`.

#### Scenario: Nested template
  Given a template at `.shablon/templates/plugins/claude/hooks/prime.md`
  When shablon renders it from cwd `/proj`
  Then the output is written to `/proj/plugins/claude/hooks/prime.md`

#### Scenario: Top-level template
  Given a template at `.shablon/templates/AGENTS.md`
  When shablon renders it from cwd `/proj`
  Then the output is written to `/proj/AGENTS.md`

### Requirement: Parent Directories Are Created
WHEN an output path's parent directory does not exist, the system SHALL create it (including intermediate directories) before writing the file.

#### Scenario: First render into a fresh project
  Given `/proj/plugins/` does not exist
  And a template at `.shablon/templates/plugins/claude/hooks/prime.md`
  When shablon renders it
  Then `/proj/plugins/claude/hooks/` is created
  And the rendered content is written into it

### Requirement: Partials Directories Are Partials Only
The system SHALL treat any directory whose basename equals the configured **partials directory name** (default `_includes`; configurable via `config.toml` `partials_dir`) at any depth under `.shablon/templates/` as containing partials, and SHALL NOT render its contents as standalone outputs. The exclusion is structural: `include` patterns cannot re-enable a partial as an output.

#### Scenario: Top-level partials directory
  Given `.shablon/templates/_includes/header.md` exists
  When shablon discovers templates
  Then `header.md` is not rendered to an output path
  And it remains available for `{% include "_includes/header.md" %}`

#### Scenario: Nested partials directory
  Given `.shablon/templates/plugins/claude/_includes/footer.md` exists
  When shablon discovers templates
  Then `footer.md` is not rendered to an output path

#### Scenario: Custom partials directory frees the default name
  Given `.shablon/config.toml` contains `partials_dir = "_partials"`
  And `.shablon/templates/_includes/note.md` exists
  When shablon discovers templates
  Then `_includes/note.md` is rendered to `<root>/_includes/note.md`

### Requirement: Dotfiles Skipped By Default
The system SHALL exclude any path whose basename starts with `.` from rendering, whether the path is a file or a directory. Excluded directories are not descended into.

WHERE the `config` capability declares an `include` pattern that matches the basename of an excluded file, the system SHALL re-include that file in rendering.

#### Scenario: Mac noise file
  Given `.shablon/templates/skills/foo/.DS_Store` exists
  When shablon discovers templates
  Then `.DS_Store` is not rendered

#### Scenario: Re-included via config
  Given `.shablon/templates/skills/foo/.gitignore` exists
  And `.shablon/config.toml` contains `include = [".gitignore"]`
  When shablon discovers templates
  Then `skills/foo/.gitignore` is rendered to `<root>/skills/foo/.gitignore`

#### Scenario: Dotfile inside the partials directory does not render even if matched by include
  Given `.shablon/templates/_includes/.partial.md` exists
  And `.shablon/config.toml` contains `include = [".partial.md"]`
  When shablon discovers templates
  Then `.partial.md` is not rendered to an output path
  Because the partials-directory exclusion is structural

### Requirement: Deterministic Render Order
The system SHALL render templates in ascending lexicographic order of their POSIX-form path relative to `.shablon/templates/`.

#### Scenario: Stable log lines
  Given templates `b/x.md` and `a/y.md` exist
  When shablon renders them
  Then the `wrote a/y.md` line precedes `wrote b/x.md` on stdout

### Requirement: Symlinks Are Followed
The system SHALL follow symbolic links during template discovery, both for individual template files and for directories within `.shablon/templates/`. Output files are written as regular files (never as symlinks). The system does not detect symlink loops; users are responsible for avoiding them.

#### Scenario: Symlinked subtree
  Given `.shablon/templates/shared` is a symlink to `/elsewhere/shared/`
  And `/elsewhere/shared/notes.md` exists
  When shablon discovers templates
  Then `shared/notes.md` is rendered to `<root>/shared/notes.md`

### Requirement: Output Mode Bits Mirror Template
The system SHALL set the mode bits of each rendered output to match the mode bits of its source template (after symlink resolution), so an executable template produces an executable output.

#### Scenario: Executable hook script
  Given `.shablon/templates/hooks/post-tool.sh` has mode `0755`
  When shablon renders it
  Then the output file has mode `0755`

#### Scenario: Plain markdown
  Given `.shablon/templates/skills/foo/SKILL.md` has mode `0644`
  When shablon renders it
  Then the output file has mode `0644`

### Requirement: Trailing Newline Preserved
The system SHALL configure the Jinja2 environment to keep the trailing newline of every template, so rendered files match POSIX text-file convention without manual padding.

#### Scenario: Template ending with newline
  Given a template whose source ends with a single trailing newline
  When shablon renders it
  Then the written file ends with a single trailing newline

### Requirement: Output Overwrites Existing File
WHEN an output file already exists at the target path, the system SHALL overwrite it with the newly rendered content.

#### Scenario: Re-running generate
  Given a previous `shablon generate` produced `/proj/skills/foo/SKILL.md`
  When the user edits the corresponding template and reruns `shablon generate`
  Then `/proj/skills/foo/SKILL.md` is overwritten with the new render

### Requirement: Render Context From Variables
The system SHALL pass the variables resolved by the `variables` capability as keyword arguments to every template render call.

#### Scenario: Top-level keys become Jinja variables
  Given variables `{"version": "1.2.0", "name": "foo"}`
  And a template containing `{{ version }}` and `{{ name }}`
  When shablon renders it
  Then the output contains `1.2.0` and `foo`

#### Scenario: No variables file
  Given no `vars.<ext>` exists in `.shablon/`
  When shablon renders a template that references no variables
  Then the render succeeds with an empty context
