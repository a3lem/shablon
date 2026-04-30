# Templates

## MODIFIED Requirements

### Requirement: Output Overwrites Existing File
WHEN an output file already exists at the target path, the system SHALL compare the newly rendered bytes and the intended mode bits against the file on disk. IF either differs, the system SHALL overwrite the file with the new content and apply the intended mode bits. IF both match, the system SHALL NOT write to the file (its mtime and inode are preserved).

The `cli` capability reports the outcome per file: `wrote` for create/overwrite, `unchanged` for skipped writes.

#### Scenario: Re-running generate after a template edit
  Given a previous `shablon generate` produced `/proj/skills/foo/SKILL.md`
  When the user edits the corresponding template and reruns `shablon generate`
  Then `/proj/skills/foo/SKILL.md` is overwritten with the new render
  And stdout contains `wrote skills/foo/SKILL.md`

#### Scenario: Re-running generate with no changes
  Given a previous `shablon generate` produced `/proj/skills/foo/SKILL.md`
  When the user reruns `shablon generate` without editing any template or variable
  Then `/proj/skills/foo/SKILL.md` is not rewritten
  And the file's mtime is unchanged
  And stdout contains `unchanged skills/foo/SKILL.md`

#### Scenario: Mode bits differ but content matches
  Given a previous render wrote `/proj/hooks/post-tool.sh` with mode `0755`
  And the user manually changed the file's mode to `0644`
  When the user reruns `shablon generate`
  Then the file's mode is restored to `0755`
  And stdout contains `wrote hooks/post-tool.sh`

#### Scenario: First write into a fresh project
  Given no output file exists at the target path
  When shablon renders the template
  Then the file is created with the rendered content and intended mode
  And stdout contains `wrote <path>`

### Requirement: Deterministic Render Order
The system SHALL process templates in ascending lexicographic order of their POSIX-form path relative to `.shablon/templates/`. The corresponding stdout line (`wrote` or `unchanged`) SHALL appear in that same order.

#### Scenario: Stable log lines
  Given templates `b/x.md` and `a/y.md` exist
  When shablon processes them
  Then the line for `a/y.md` precedes the line for `b/x.md` on stdout
  Regardless of whether each line is prefixed `wrote ` or `unchanged `
