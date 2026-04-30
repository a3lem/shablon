---
id: shab-de64
status: completed
type: feature
priority: 2
deps: []
links: []
tags: []
xref: report-render-changes
created: 2026-04-30T19:10:57.928683+00:00
---
# Report changed files in shablon generate

## Description

Spec change: specs/changes/report-render-changes/

Make 'shablon generate' distinguish files actually written from files left untouched. Stdout uses 'wrote <path>' for create/overwrite and 'unchanged <path>' for skipped writes. Skip the write entirely when rendered bytes and intended mode already match what is on disk.
