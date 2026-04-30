---
id: shab-1a4f
status: completed
type: task
priority: 2
assignee: claude
deps: [shab-e74f]
links: []
parent: shab-8f54
tags: []
created: 2026-04-28T10:28:18.069384+00:00
---
# Render module (render.py)

## Description

build_env(template_root) with FileSystemLoader + keep_trailing_newline=True (default Undefined). render_to_file renders with **context, mkdir parents, write, then chmod output to source_path.stat().st_mode & 0o777.

Spec: deltas/templates/spec.md "Template Root", "Output Path Mirrors Template Path", "Parent Directories Are Created", "Trailing Newline Preserved", "Output Overwrites Existing File", "Render Context From Variables", "Output Mode Bits Mirror Template".
