---
id: shab-bf64
status: closed
type: task
priority: 2
assignee: claude
deps: [shab-6db2, shab-7389, shab-e1d8, shab-19dd, shab-1a4f]
links: []
parent: shab-8f54
tags: []
resolution: completed
created: 2026-04-28T10:28:23.374256+00:00
---
# Generate orchestration (generate.run)

## Description

Glue: find_project_root -> require templates/ -> config.load -> variables.resolve -> build_env -> find_templates -> loop render_to_file printing 'wrote <rel>'. Halt on first error; leave already-written files in place.

Spec: deltas/cli/spec.md "Empty Templates Tree Is A No-Op", "Missing Templates Directory Errors Cleanly", "Errors Halt Generation".
