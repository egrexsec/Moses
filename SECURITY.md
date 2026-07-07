# Security Policy

## Scope

Moses is a local media-processing workflow. The most relevant security concerns are:
- dependency and container hygiene
- accidental exposure if the local UI is bound beyond trusted networks
- unsafe handling of user-supplied media files
- committing copyrighted or sensitive media during development

## Reporting

Please avoid posting sensitive details publicly first.

If no private reporting channel exists, open a minimal GitHub issue labeled `security` without sharing exploit instructions or private media.

## Expectations

Before merging runtime changes:
- keep the app local to trusted environments
- avoid exposing demo or test files you do not have permission to share
- review container/runtime changes carefully
