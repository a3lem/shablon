---
id: shab-c0a7
status: completed
type: task
priority: 2
deps: []
links: []
parent: shab-de64
tags: []
created: 2026-04-30T19:11:04.570141+00:00
---
# RenderOutcome enum + compare-before-write in render.render_to_file

## Description

Modify src/shablon/render.py:

- Add RenderOutcome enum (WROTE, UNCHANGED) with values doubling as log prefixes ('wrote', 'unchanged').
- Change render_to_file to return RenderOutcome.
- Procedure: encode rendered string once; if output_path missing -> mkdir parents, write, chmod, return WROTE; else read existing bytes and mode; if both match -> return UNCHANGED without touching the file; else write and chmod (only chmod if mode differs), return WROTE.
- Do not normalize content; exact byte equality.
- Error semantics unchanged.
