---
name: vibe-project-migrator
description: Audit and migrate an existing software repository into a project-adapted, evidence-driven AI collaboration workflow with AGENTS.md guidance, authoritative docs, risk-tiered change records, review templates, and verification receipts. Use when asked to introduce, standardize, or improve vibe coding or AI governance across a repository. Do not use for ordinary feature work that does not change collaboration practices.
---

# Vibe Project Migrator

Turn a repository's implicit habits into durable project context and reviewable evidence. Preserve the project's product behavior, technology choices, terminology, and existing governance unless the user explicitly requests broader changes.

## Non-negotiable boundaries

- Adapt the model to the target repository; do not copy another project's names, commands, people, internal URLs, product rules, or technology-specific constraints.
- Inspect before editing. Preserve unrelated work and update existing authoritative files instead of creating a competing documentation system.
- Do not change product code, dependencies, repository settings, branch protections, visibility, remotes, or external systems unless the user separately authorizes those changes.
- Treat destructive operations, credentials, private source material, regulated data, and external writes as explicit authorization boundaries.
- Report actual evidence. Never describe a planned, skipped, partial, or failed check as passed.

## Workflow

### 1. Audit the repository

Read the root and nearest applicable instruction files, Git status, README, contribution and security policies, build manifests, CI, docs index, templates, and validation commands. Run the bundled read-only inventory when Python is available:

```text
python <skill-directory>/scripts/audit_project.py --root <repository> --format json
```

The inventory produces signals, not a compliance score. Confirm its findings against the actual files before making decisions.

### 2. Select the smallest useful migration profile

Read [references/migration-playbook.md](references/migration-playbook.md) before planning or applying a migration.

- **Baseline**: a small or early project that needs one durable AI entrypoint, contributor rules, review evidence, and clear validation commands.
- **Standard**: an active product repository that also benefits from a docs index, risk-tiered change proposal, issue forms, security reporting, and decision traceability.
- **Layered**: a monorepo or multi-domain system whose subtrees genuinely need narrower `AGENTS.md` files or specialized rules.

Risk can raise the required evidence without forcing a larger file hierarchy. A small tool that deletes data may need stricter safety and rollback guidance than a large documentation site.

### 3. Design the target state

Before authoring governance artifacts, read [references/artifact-blueprints.md](references/artifact-blueprints.md). Produce a path-level plan showing:

- which existing files will be updated;
- which missing files will be added;
- which suggested artifacts are intentionally omitted and why;
- how project-specific build, test, security, release, and Git rules were derived;
- what remains a human decision.

For a diagnose, audit, or recommendation request, stop after the report. Only edit when the user asked to migrate or change the project.

### 4. Apply the migration

- Keep stable project facts and decision-changing rules in the AI entrypoint; keep detailed or conditional material in linked docs.
- Separate intent, design, implementation, and verification for non-trivial changes, while allowing trivial work to stay lightweight.
- Use the repository's language and existing conventions. Infer validation commands from checked-in configuration, not generic ecosystem memory.
- Preserve existing commit conventions when they are coherent. Otherwise recommend standard Conventional Commits without rewriting history.
- Make documentation paths and templates internally consistent. Do not leave scaffold placeholders in delivered files.

If the task includes README positioning, onboarding, public release, or stakeholder acceptance, read [references/adoption-guide.md](references/adoption-guide.md) before editing those materials.

### 5. Verify and hand off

Rerun the inventory and perform proportional checks:

- resolve local Markdown links and referenced paths;
- parse structured configuration with an available native parser;
- run the repository's documented formatting, lint, test, build, and smoke checks that are relevant to the changed files;
- inspect staged changes for secrets, private paths, internal identities, copied project-specific policy, unfinished placeholders, and unrelated edits;
- use `git diff --check` and confirm the final Git status.

Return a migration receipt with the chosen profile, files changed, important adaptation decisions, omitted artifacts, commands and results, limitations, and any human review still required. Do not commit, push, publish, or change repository settings unless explicitly authorized.
