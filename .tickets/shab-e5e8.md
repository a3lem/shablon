---
id: shab-e5e8
status: completed
type: task
priority: 2
deps: [shab-38f9]
links: []
parent: shab-de64
tags: []
created: 2026-04-30T19:11:16.352666+00:00
---
# Tests for wrote/unchanged behavior

## Description

Add/update tests covering the new requirements:

cli capability:
- First run: every line prefixed 'wrote '.
- Immediate re-run: every line prefixed 'unchanged '.
- Edit one template, rerun: only that line is 'wrote ', others 'unchanged '.

templates capability:
- Re-running with no changes does not rewrite the file (mtime preserved).
- Mode bits differ but content matches -> file rewritten/chmod'd, prints 'wrote '.
- First write into fresh project prints 'wrote '.
- Deterministic order regardless of prefix.

Update any existing assertion that hardcodes 'wrote ' on a re-run.
