## What changed

<!-- Describe the user-visible or contract-visible result. -->

## Scope

- [ ] Internal portal polish only
- [ ] Public Wallboard
- [ ] Runtime or adapter
- [ ] Source contract or business logic
- [ ] Documentation or repository tooling

## Safety and boundaries

- [ ] Routes, labels, and data flow are preserved where required.
- [ ] No browser-to-Monday access was added.
- [ ] Unsupported metrics remain omitted or in a review/unavailable state.
- [ ] No credentials, secrets, tokens, or private records were committed.
- [ ] Public-safe projection rules were checked if a public surface changed.

## Verification

- [ ] `pytest -q`
- [ ] Python compilation
- [ ] JavaScript syntax checks
- [ ] `git diff --check`
- [ ] Public-surface safety check, when applicable
- [ ] Browser/runtime QA, or limitation documented

## Notes for reviewers

<!-- List source references, affected routes, deployment impact, and known limitations. -->
