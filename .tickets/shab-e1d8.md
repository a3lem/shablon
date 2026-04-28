---
id: shab-e1d8
status: closed
type: task
priority: 2
assignee: claude
deps: [shab-e74f]
links: []
parent: shab-8f54
tags: []
resolution: completed
created: 2026-04-28T10:27:55.826029+00:00
---
# Variables module (variables.py)

## Description

Discover vars.<ext> in .shablon/ via regex ^vars\.[^./]+$; reject zero-or-multiple per spec; require executable bit; subprocess invocation with cwd=project root, env+SHABLON_PROJECT_ROOT, no argv, stdin=DEVNULL, stdout captured, stderr inherited; JSON-object parse with type assertion; format error on non-zero exit.

Spec: deltas/variables/spec.md (all six requirements).
