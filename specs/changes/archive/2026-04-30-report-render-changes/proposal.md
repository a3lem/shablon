# Report Render Changes

## Why

Re-running `shablon generate` always logs `wrote <path>` for every template, regardless of whether the file on disk actually changed. After a small edit, the user can't tell which outputs were affected without diffing. The log should make the distinction explicit.

## What Changes

- `shablon generate` differentiates rendered files that were written from those left untouched because the new render matches what is already on disk.
- A file is treated as **unchanged** when both its content bytes and its mode bits already match what would be written; otherwise it is **written**.
- Stdout uses two prefixes: `wrote <path>` for written files and `unchanged <path>` for skipped writes. Render order remains deterministic, so the prefix is the only visual difference.
- Filesystem behavior: when content+mode already match, shablon does not re-open or re-write the file (no mtime churn).

## Capabilities

### Modified Capabilities

- `cli`: `generate` log format gains an `unchanged` line type alongside `wrote`.
- `templates`: writes are skipped when the rendered bytes and mode bits already match the file on disk.

## Impact

- `src/shablon/` rendering pipeline: introduce a compare-before-write step.
- Tests covering generate output and the overwrite scenario need updates for the new line format and skip behavior.
- Downstream tooling that greps `wrote ` lines will see fewer matches on no-op runs; documented in CHANGELOG.

## Out of Scope

- A `--verbose` / `--quiet` flag to suppress `unchanged` lines. Can be added later if the noise is a problem.
- Reporting deletions of stale outputs whose templates no longer exist.
