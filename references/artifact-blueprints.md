# Artifact blueprints

Use these as content contracts, not files to copy verbatim. Adapt headings, language, filenames, and depth to the target repository.

## AI entrypoint

A useful root `AGENTS.md` or equivalent normally answers:

1. Where does this rule apply, and what takes precedence?
2. What does the product do, and which behaviors must never be weakened silently?
3. Where do major responsibilities live?
4. Which existing docs are authoritative for architecture, product, security, and operations?
5. Which work is trivial, and which work requires a proposal or human review?
6. Which exact commands or checked-in scripts prove a change?
7. Which Git, deployment, publication, and external-write actions require explicit authorization?

Avoid generic coding advice, exhaustive module inventories, duplicated build flags, aspirational claims, personal preferences, or volatile ownership data.

## AI collaboration guide

Recommended content:

- why the project uses AI assistance;
- human, AI, reviewer, and user responsibilities;
- the project's change-risk tiers;
- context acquisition order;
- research, design, implementation, and verification evidence;
- how deviations and new risks are recorded;
- the definition of done;
- prohibited behaviors such as fabricated tests, silent scope expansion, credential disclosure, and self-approval of high-risk work.

State that AI code is judged by the same observable evidence as human code. Do not require disclosure that has no review value; ask for the areas AI touched, the human-reviewed scope, and unverified areas.

## Change proposal

For risk-bearing work, include:

- user problem, goal, and observable acceptance criteria;
- scope and non-goals;
- at least two realistic alternatives when a real choice exists;
- selected approach and affected modules or interfaces;
- security, privacy, persistence, compatibility, performance, and operations impact as applicable;
- risks, mitigations, and executable rollback boundary;
- implementation slices that can be reviewed or reverted independently;
- verification matrix with commands or steps and actual results;
- decision log and implementation deviations;
- AI participation, human reviewer, and uncovered areas.

Do not force irrelevant categories into trivial changes. “Not applicable” is useful only when it closes a plausible risk.

## Contribution guide

Keep onboarding executable:

- supported toolchain derived from manifests or CI;
- install, format, lint, test, build, smoke, and release commands as applicable;
- safety or data rules contributors must preserve;
- branch and commit convention based on current history;
- when docs, changelog, architecture, translations, fixtures, snapshots, or generated files must change;
- PR evidence and review expectations;
- security reporting path.

Avoid undocumented machine-specific paths and commands that were not verified.

## Pull request template

Ask for:

- user value;
- included scope and non-goals;
- change summary;
- security, data, compatibility, and rollback impact where relevant;
- commands or steps actually executed and their results;
- explicitly unexecuted checks and reasons;
- screenshots or other visual evidence when behavior is visual;
- AI involvement, human-reviewed scope, and unverified areas;
- a short completion checklist for secrets, docs, tests, and commit quality.

Do not use empty future-tense test checklists as evidence.

## Issue forms

Defect intake should request impact, minimal reproduction, environment or version, expected and actual results, and redacted logs. Feature intake should start with the user problem and acceptance criteria, then scope, safety/data impact, and alternatives.

Provide a private security-reporting route when the repository can actually receive it. Never direct vulnerability details into a public issue.

## Docs index

Group links by reader intent rather than mirroring directories:

- users and operators;
- architecture and design;
- security and data handling;
- development and testing;
- AI collaboration and change records.

Identify the authoritative source for each decision class so that code, README, and agent entrypoints do not compete.

## Nested instructions

Add a subtree instruction file only when local work differs materially in build commands, generated-file policy, architecture boundary, language style, safety, or ownership. Link to the parent and record differences rather than duplicating the root.
