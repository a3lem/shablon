# Design: Report Render Changes

## Context

`shablon generate` currently renders each template, unconditionally writes to the output path, sets mode bits, and prints `wrote <rel>`. The implementation lives in two modules:

- `src/shablon/generate.py::run` — orchestrates discovery, render loop, and prints log lines.
- `src/shablon/render.py::render_to_file` — renders, writes, chmods.

Re-running the command produces identical log output regardless of whether anything actually changed, which is the user pain point.

## Goals / Non-Goals

**Goals**

- Skip the write when the rendered bytes and intended mode match what is already on disk.
- Surface the per-file outcome on stdout with two stable line prefixes: `wrote ` and `unchanged `.
- Preserve mtime for unchanged files (so downstream tools that watch mtime aren't fooled).
- Keep render order deterministic and the log line order one-to-one with discovered templates.

**Non-Goals**

- No `--quiet` / `--verbose` flag in this change.
- No detection or reporting of stale outputs whose source templates were deleted.
- No content hashing cache across runs; comparison is always against the file currently on disk.

## Decisions

### Outcome enum returned by `render_to_file`

`render.render_to_file` returns a `RenderOutcome` enum with two values: `WROTE` and `UNCHANGED`. `generate.run` uses the return value to pick the log prefix. This keeps the write/skip decision colocated with the file I/O and keeps `generate.run` purely orchestrational.

```python
class RenderOutcome(enum.Enum):
    WROTE = "wrote"
    UNCHANGED = "unchanged"
```

The enum value strings double as the log prefix to keep `generate.run` trivial: `print(f"{outcome.value} {rel}")`.

**Alternatives considered:** Returning a bool (`wrote: bool`) — rejected because the call site would still need a mapping from bool to prefix string, and an enum documents intent at the call site. Doing the comparison in `generate.run` — rejected because it would duplicate path/mode handling already in `render_to_file`.

### Comparison procedure

Inside `render_to_file`, after producing `rendered: str` and computing the intended `mode: int`:

1. Encode `rendered` to bytes once (`rendered.encode("utf-8")`).
2. If `output_path` does not exist → create parents, write, chmod, return `WROTE`.
3. Else read existing bytes (`output_path.read_bytes()`) and existing mode (`output_path.stat().st_mode & 0o777`).
4. If both match the intended bytes and mode → return `UNCHANGED` without touching the file.
5. Else write bytes and chmod (only call `chmod` if mode differs, to avoid a redundant syscall), return `WROTE`.

Bytes comparison is exact; we do not normalize whitespace or line endings. The Jinja env already preserves trailing newlines, and templates are not transformed beyond rendering, so byte-equality is the right invariant.

**Alternatives considered:** Hashing (sha256) both sides — rejected, no benefit at the file sizes shablon handles (small text templates) and adds a dependency on hashlib for no measurable speedup. Comparing only content and always re-applying chmod — rejected because it would print `wrote` for files where nothing observable changed.

### `parents.mkdir` is conditional

Only call `output_path.parent.mkdir(parents=True, exist_ok=True)` when we are about to write. For the `UNCHANGED` path, the parent already exists (the file is there), so the call is unnecessary. Small win, but keeps the `UNCHANGED` branch a pure pair of reads.

### Log format

`generate.run` becomes:

```python
outcome = render.render_to_file(env, rel, output_path, context, template_path)
print(f"{outcome.value} {rel}")
```

Both prefixes are lowercase, single word, followed by a single space and the POSIX-form relative path. No trailing punctuation. This matches the existing `wrote ` convention and is the minimal diff for downstream parsers.

### Error handling unchanged

The `Errors Halt Generation` requirement is unaffected. If the comparison read or the write raises, the existing error path applies (stop, leave already-written files in place, exit non-zero). We do not catch `OSError` from the existence check — `Path.exists()` returns False for ENOENT and lets other errors propagate naturally on the subsequent `read_bytes`.

## Risks / Trade-offs / Limitations

- [Doubled stdout volume on no-op runs] → Acceptable: the log is still O(templates) and the user explicitly asked for the per-file status. Out-of-scope `--quiet` flag is the escape hatch if this becomes annoying.
- [Reading every existing output even when most are unchanged] → Acceptable for shablon's scale (tens of small text files). If projects ever grow large, a stat+size pre-check could short-circuit, but premature.
- [Race: file changes between read and write] → Not handled; shablon is a single-shot CLI, not a daemon. Concurrent edits during `generate` are user error.
- [Symlinks as outputs] → Outputs are always regular files (per existing `Symlinks Are Followed` requirement, only inputs may be symlinks). `read_bytes` on a regular file is correct; no special handling needed.

## Open Questions

None.
