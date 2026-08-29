# Adoption and acceptance guide

Use this guide when the migration includes README positioning, onboarding, a public repository, or stakeholder acceptance.

## Why governance is necessary

Natural-language coding removes friction from implementation, but it also makes it easy to produce more change than reviewers can safely absorb. Chat history is temporary, model context is incomplete, and a confident answer is not test evidence. Repository-native governance converts implicit team knowledge into durable constraints and produces a trail that people can inspect without replaying an AI session.

The skill is valuable when it reduces these failure modes:

- repeated rediscovery of architecture and commands;
- conflicting instructions across tools or contributors;
- design decisions hidden inside chat;
- large generated diffs with unclear user value;
- safety or external-write boundaries inferred too late;
- “tests passed” claims without commands and results;
- maintainers rejecting AI-assisted work because its provenance and review coverage are unclear.

The goal is not process for its own sake. Apply the smallest profile that makes the next change safer and easier to review.

## README narrative

Lead in this order:

1. **Problem**: what repository pain does the skill remove?
2. **Outcome**: what durable artifacts and behaviors appear after migration?
3. **Safety**: what the skill will not change without permission.
4. **Proof**: audit output, validation commands, tests, and examples.
5. **Usage**: one install path and one realistic invocation.
6. **Depth**: profiles, artifact catalog, architecture, and contribution details.

Avoid leading with an internal methodology name. Readers adopt a tool because it reduces risk or review time, not because it has many templates.

## Acceptance contract

Make the following promises observable:

- **Project-adapted**: generated rules cite the target repository's actual scripts and docs.
- **Behavior-preserving**: governance migration does not modify product behavior by default.
- **Reviewable**: every created artifact has a defined audience and authority.
- **Proportional**: small repositories are not forced into a large-enterprise document tree.
- **Transparent**: AI involvement, human review, skipped checks, and limitations remain visible.
- **Reversible**: changes are ordinary repository files and can be reviewed or reverted by commit.

## Before and after demonstration

Use a compact comparison rather than a marketing claim:

| Before | After |
|---|---|
| commands live in memory or chat | exact commands live in contributor and agent guidance |
| non-trivial work begins directly in code | risk-bearing work records scope, alternatives, rollback, and acceptance |
| PR says “tests passed” | PR shows the executed command and result |
| every agent rebuilds context | root and subtree instructions route to authoritative sources |
| reviewers distrust a large AI diff | scope, AI participation, human-reviewed areas, and gaps are explicit |

## Progressive rollout

Recommend three adoption steps:

1. Start with a root AI entrypoint, contributor commands, and PR evidence.
2. Add change proposals, issue forms, and a docs index when the project has recurring non-trivial work.
3. Add nested instructions only after different subtrees demonstrate different needs.

Useful success signals include shorter onboarding, fewer repeated context questions, smaller PRs, fewer review rounds caused by missing evidence, and fewer regressions from misunderstood safety boundaries. Do not invent metrics; establish a baseline before claiming improvement.
