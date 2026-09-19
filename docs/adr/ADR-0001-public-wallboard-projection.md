# ADR-0001: Separate Six-Screen Public Wallboard

Status: Accepted  
Date: 2026-09-17

## Context

The portal contains internal operational modules, while the requested TV display must be readable without a mouse, scrolling, or access to protected detail.

## Decision

Publish the Public Wallboard as a separate fixed 16:9 route with six independently understandable screens and automatic cycling.

## Consequences

- Public and protected information boundaries can be tested separately.
- Each screen must carry its own interpretation and freshness context.
- Wallboard UI cannot depend on portal drawers, hover, or internal route state.
- A separate public projection is required before live protected data is exposed.
