# ADR 0001: repository location

Status: accepted for now; **must be revisited before phase 4 data work or phase 11**, because the current repository is public.

## Context

The brief asks for a dedicated monorepo. This session can only push to `zsiguli04/claude-skills-founder`, whose root is a published Claude Code plugin (`founder`). Putting `apps/` and `packages/` at that root would mix two products and break the plugin's layout.

## Decision

Build the platform in `wealth-intelligence/` on the current branch, laid out exactly as the target monorepo, with no imports from outside that folder except the existing `engine/`, which phase 5 moves in.

## Visibility

`zsiguli04/claude-skills-founder` is a **public** fork (checked 2026-10-08). Everything pushed to this branch is visible to anyone. Until the platform has its own private repository:

- only code, documentation, and fictional `DEMO DATA` may be committed here;
- no real company data, no client data, no rule database exports beyond what is already public, no infrastructure details, no secrets;
- the product's moat (company data, valuation history, regulatory rule history) must live in private storage and a private repository.

## Consequences

- The folder can become its own repository with `git subtree split --prefix wealth-intelligence` (history kept) once a new repository exists.
- CI workflows for it live in the root `.github/workflows/` with `paths: wealth-intelligence/**` until the move.
- Required: create a dedicated **private** repository before any real data, deployment configuration, or proprietary rule data is added.
