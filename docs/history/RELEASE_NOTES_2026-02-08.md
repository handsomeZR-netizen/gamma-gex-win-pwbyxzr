# Release Notes - 2026-02-08

## Summary

This release focuses on maintainability and observability:
- strengthened repository hygiene
- added canonical architecture/history documents
- prepared project for first clean GitHub publication path

## Included Changes

### Documentation
- Added architecture baseline:
  - `docs/architecture/ARCHITECTURE_CURRENT.md`
- Added history documents:
  - `docs/history/ARCH_UPGRADE_HISTORY.md`
  - `docs/history/FEATURE_CHANGELOG.md`
  - `docs/history/INDEX.md`
- Added optimization recommendations:
  - `docs/PROJECT_OPTIMIZATION_RECOMMENDATIONS.md`
- Updated README navigation and runtime API section.

### Repository Hygiene
- Updated `.gitignore` for:
  - snapshot jsonl files
  - logs/tmp runtime artifacts
  - transient frontend reverse-engineering files
  - runtime marker files

## Validation Snapshot

- Dashboard runtime remains read-only and API-compatible.
- Core dashboard endpoints unchanged in behavior:
  - `/api/health`
  - `/api/dashboard/snapshot`
  - `/api/dashboard/history`
  - `/api/dashboard/debug`
