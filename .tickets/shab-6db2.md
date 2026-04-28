---
id: shab-6db2
status: closed
type: task
priority: 2
assignee: claude
deps: [shab-e74f]
links: []
parent: shab-8f54
tags: []
resolution: completed
created: 2026-04-28T10:27:45.232191+00:00
---
# Project-root upward discovery (discovery.find_project_root)

## Description

Walk upward from a start path checking each ancestor for a .shablon/ directory; return the project root or raise ShablonError at filesystem root.

Spec: deltas/cli/spec.md "Project Root Discovery", "Missing Configuration Errors Cleanly".
