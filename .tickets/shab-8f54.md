---
id: shab-8f54
status: closed
type: epic
priority: 2
assignee: claude
deps: []
links: []
tags: []
xref: add-generate
resolution: completed
created: 2026-04-28T10:27:36.482214+00:00
---
# Add shablon generate command

## Description

Bootstrap the shablon CLI with a single `generate` subcommand that walks .shablon/templates/, applies dotfile/_includes filters, runs an optional executable vars.<ext> for context, and renders Jinja2 templates to mirrored output paths under the project root.

Specs: specs/changes/add-generate/ (proposal, deltas/{cli,templates,variables,config}, design, tasks).
