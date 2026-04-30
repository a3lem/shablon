---
id: shab-19dd
status: completed
type: task
priority: 2
assignee: claude
deps: [shab-e74f]
links: []
parent: shab-8f54
tags: []
created: 2026-04-28T10:28:12.144467+00:00
---
# Template discovery (discovery.find_templates)

## Description

Walk template_root with follow_symlinks=True; skip ancestor directories whose basename equals partials_dir or starts with .; skip dotfile leaves unless basename matches an include pattern via fnmatch.fnmatchcase; return absolute paths sorted by relative POSIX path.

Spec: deltas/templates/spec.md "Partials Directories Are Partials Only", "Dotfiles Skipped By Default", "Deterministic Render Order", "Symlinks Are Followed".
