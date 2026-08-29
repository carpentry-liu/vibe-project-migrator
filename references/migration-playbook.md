# Migration playbook

Use this playbook for planning or applying a repository migration. The desired outcome is not identical filenames across projects; it is a durable chain from human intent to implementation evidence.

## 1. Establish authority and scope

Determine, in order:

1. the user's current request and explicit authorization;
2. applicable repository and subtree instructions;
3. checked-in architecture, product, security, build, test, release, and Git facts;
4. existing team conventions;
5. external sources needed to fill a genuine gap.

If sources conflict, report the conflict instead of silently choosing one. Do not make a historical document authoritative merely because it is detailed.

## 2. Inventory before designing

Inspect the worktree without mutating it:

- Git branch, status, remotes, and recent commit style;
- languages, build systems, package managers, applications, libraries, and deployable targets;
- README, docs index, architecture, product, requirements, decisions, security, contribution, release, and testing guides;
- root and nested AI instruction files;
- CI workflows, PR templates, issue forms, ownership rules, and hooks;
- commands that actually exist in manifests and scripts;
- high-risk behaviors such as deletion, migration, credentials, network publishing, billing, production deployment, or regulated data.

Preserve unrelated dirty files. A migration should not clean or normalize the whole repository unless that is the task.

## 3. Choose a profile

### Baseline

Use when one team and one main technology can share a concise rule set.

Typical artifacts:

- root `AGENTS.md` or an existing equivalent;
- contribution guide with exact validation commands;
- AI collaboration section or document;
- PR template that requires scope, risk, and evidence.

### Standard

Use when the repository has regular feature work, multiple contributors, user-facing behavior, or meaningful operational risk.

Add only the relevant artifacts:

- docs index;
- lightweight change-proposal template;
- issue forms for defects and features;
- security reporting path;
- architecture and decision update rules;
- AI participation and human-review disclosure.

### Layered

Use when different subtrees have materially different commands, architecture boundaries, ownership, generated files, or safety rules. Create nested `AGENTS.md` only at those boundaries. Do not mirror every directory.

Each nested file should state its parent, scope, local facts, and differences. Avoid repeating unchanged root rules.

## 4. Map instead of duplicate

Create a migration map before editing:

| Need | Existing authority | Action | Reason |
|---|---|---|---|
| AI entrypoint | `CLAUDE.md` | update and add a small `AGENTS.md` router | keep one facts source while supporting multiple agents |
| Change design | existing RFC template | extend | avoid a second proposal system |
| Verification | package scripts and CI | link | commands remain executable and current |

Prefer updating a coherent existing artifact. Add a new file only when it has a distinct audience or authority.

## 5. Encode stable rules

The root entrypoint should contain only facts that materially change agent decisions:

- scope and precedence;
- project purpose and non-negotiable product or safety boundaries;
- repository map and dependency direction;
- how to obtain context;
- when a proposal or human review is required;
- exact validation sources or commands;
- Git and external-write boundaries.

Keep rapidly changing module lists, versions, flags, owners, and historical snapshots in their authoritative code or docs rather than duplicating them in the entrypoint.

## 6. Make non-trivial work traceable

Use risk tiers rather than treating every change as a design project:

- **L0**: wording, links, formatting, mechanical metadata. Require a clean diff and a relevant check.
- **L1**: contained behavior or tooling change. Record root cause, scope, implementation, and tests.
- **L2**: feature, cross-module refactor, public API/data format, security boundary, destructive behavior, irreversible or expensive decision. Require alternatives, risks, rollback, staged implementation, and acceptance evidence.

The repository may rename or combine these tiers. Preserve an existing effective process instead of imposing the labels.

## 7. Keep stages distinguishable

For L2 work, make the following states separately reviewable even if they live in one document:

1. user problem and acceptance criteria;
2. research and alternatives;
3. selected design and decision log;
4. implementation record and deviations;
5. verification commands, actual results, and limitations.

AI may help produce every stage, but it cannot supply the missing human authorization for safety-sensitive actions or approve its own evidence on behalf of a maintainer.

## 8. Validate the migration

At minimum:

- all referenced files and local Markdown links resolve;
- generated templates contain no accidental placeholders;
- build and test commands match checked-in configuration;
- the new hierarchy has no contradictory instructions;
- the PR and issue templates ask for observable evidence rather than future checklists;
- project-specific secrets, internal URLs, identities, and reference-repository language were not copied;
- documentation-only migration did not change product behavior;
- unexecuted checks and human review are explicitly identified.

## 9. Commit in reviewable units

When commit authorization exists, separate governance scaffolding from unrelated product work. Use the repository's established commit convention and write a concrete subject. Never rewrite or force-push shared history merely to make the migration look clean.

The final receipt should let another maintainer answer: what changed, why this profile was chosen, what evidence passed, what was deliberately omitted, and what still needs human judgment.
