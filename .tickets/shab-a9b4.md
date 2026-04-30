---
id: shab-a9b4
status: completed
type: task
priority: 2
assignee: claude
deps: [shab-bf64]
links: []
parent: shab-8f54
tags: []
created: 2026-04-28T10:28:27.442497+00:00
---
# CLI wiring (cli.py)

## Description

argparse with top-level --cwd PATH (default cwd) and required generate subcommand. main() dispatches; catches ShablonError and prints 'error: <msg>' to stderr with exit 1; lets unexpected exceptions propagate as tracebacks.

Spec: deltas/cli/spec.md "Generate Subcommand".
