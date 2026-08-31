---
type: agent-context
owner: repo-agent
scope: repo/shal
reviewed: 2026-08-31
---

# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

This is a **single-context** repo (one library, not a monorepo).

## Before exploring, read these

- **`docs/ARCHITECTURE.md`** — the north star, and **§5 is the Decision Ledger of record**
  (`D1`–`D20`, grandfathered at this path by `decision-ledger-standard.md`). This is the
  only ledger: there is no `docs/DECISIONS.md` and no `docs/adr/` here.
- **`docs/agents/context.md`** — the working-context file (project guide, conventions,
  non-negotiables).
- **`docs/design/DESIGN V2.md`** — the architecture detail behind the ledger.
- **`src/shal/SDK.md`** — the authoring contract (how drivers/buses/topologies are written).
- **Module docstrings in `src/shal/*.py`** — each states the file's invariants; this is
  the de-facto glossary. Read the docstring of any module you touch.

Superseded design docs live in `docs/design/archive/` — provenance only, never cite them
as live. If any referenced file doesn't exist, **proceed silently**.

## File structure

Single-context repo:

```
/
├── docs/
│   ├── ARCHITECTURE.md               ← north star; §5 = the Decision Ledger (D1–D20)
│   ├── CATALOG.md                    ← the bus/driver roadmap
│   ├── agents/                       ← agent context (context.md, this file, issue-tracker, triage-labels)
│   └── design/                       ← design detail (in-repo only, not packaged)
│       ├── DESIGN V2.md              ← the architecture detail
│       ├── DESIGN - PHASE 2 ASYNC.md ← the async/streaming design
│       └── archive/                  ← superseded, kept for provenance
├── dev/eval/                         ← release-acceptance harnesses + trial reports
├── examples/                         ← demos + the driver-creator benchmark (not shipped)
├── integrations/                     ← agent-host packs, e.g. Claude Code skills (not shipped)
├── tests/                            ← pytest suite
└── src/shal/                         ← the package (module docstrings = glossary)
    ├── AGENT_GUIDE.md                ← cold-user quickstart (shipped; `shal docs`)
    └── SDK.md                        ← authoring contract (shipped; `shal docs --sdk`)
```

## Use the project's vocabulary

When your output names a domain concept (an issue title, a refactor proposal, a
hypothesis, a test name), use the term as the project uses it — the canonical phrasing
is *"a bus is just a node that provides a transport to its children"*, transport **kinds**
(ByteTransport / CommandTransport / MessageTransport / Stream), **capabilities**,
**drivers** bound by `compatible`, declared **operating limits**. Don't drift to synonyms.

If the concept you need isn't named anywhere in the docs or docstrings, that's a signal —
either you're inventing language the project doesn't use (reconsider) or there's a real gap.

## Flag decision conflicts

The rows of the Decision Ledger (`docs/ARCHITECTURE.md` §5) are **locked**. If your
output contradicts one, surface it explicitly rather than silently overriding:

> _Contradicts the "delivery-unknown writes are never auto-retried" decision — but worth
> reopening because…_
