---
id: shab-38f9
status: completed
type: task
priority: 2
deps: [shab-c0a7]
links: []
parent: shab-de64
tags: []
created: 2026-04-30T19:11:09.332653+00:00
---
# Wire outcome into generate.run log line

## Description

Modify src/shablon/generate.py: use the RenderOutcome returned by render.render_to_file to print 'f"{outcome.value} {rel}"' instead of the hardcoded 'wrote {rel}'. Order and one-line-per-template invariant unchanged.
