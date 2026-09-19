# Security policy

## Scope

This repository contains a public static preview and code for protected, read-only runtime adapters. GitHub Pages is not a production authenticated runtime and must never receive internal Monday data, credentials, or confidential person-level records.

## Reporting a vulnerability

Do not open a public issue for a credential, authorization, data-exposure, or secret-handling problem. Contact the repository owner through the private GitHub security channel or the Skylark security owner, including the affected path, impact, reproduction steps, and a safe remediation suggestion.

Never include a live token, password, API key, OAuth secret, connection string, or private record in the report. Replace values with `[REDACTED]`.

## Required handling

- Revoke exposed credentials immediately and rotate them outside Git.
- Remove the secret from the working tree and Git history through the approved incident process; deleting a line from the current branch is not sufficient.
- Keep runtime credentials in environment or secret-manager configuration.
- Fail closed when protected credentials or source snapshots are missing or invalid.
- Keep browser-to-Monday access prohibited.
- Keep public projections aggregate-only and free of names, board identifiers, billing values, serial numbers, internal incident notes, and unresolved root-cause notes.

## Local configuration

Use an untracked `.env` file or process environment. The repository must contain only redacted examples and field names, never usable values.
