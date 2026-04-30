---
id: shab-e68b
status: completed
type: task
priority: 2
deps: [shab-e5e8]
links: []
parent: shab-de64
tags: []
created: 2026-04-30T19:11:20.571183+00:00
---
# Update CHANGELOG for wrote/unchanged log change

## Description

Add an entry under [Unreleased] in CHANGELOG.md noting that 'shablon generate' now prints 'unchanged <path>' for files whose content+mode already match, and skips the rewrite (mtime preserved). Mention that downstream tooling grepping 'wrote ' will see fewer matches on no-op runs.
