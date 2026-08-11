# Presenter card — Telano voice telecom tutorial

**Total:** 75–90 minutes · **Gate:** `make verify` must pass before Step 0.

## Timing

| Step | Minutes | Topic | Escape hatch |
|---:|---:|---|---|
| Setup | 5 | `make install` / `make env` / `make verify` | Share a pre-verified machine |
| 0 | 8 | Scaffold + voice | Paste `step-00-scaffold/` |
| 1 | 8 | FAQ prose skill | Paste `step-01-faq/` |
| 2 | 10 | First `@tool` (check bill) | Paste `step-02-check-bill/` |
| 3 | 8 | `tool_constraints` | Paste `step-03-tool-constraints/` |
| 4 | 15 | **Reset router showcase** | Paste `step-04-reset-router/` |
| 5 | 12 | Composition (internet) | Paste `step-05-internet/` |
| 6 | 8 | Fast-forward remaining | Paste `step-06-remaining/` or stay on finished tree |
| 7 | 10 | Voice mic pass | Text mode if mic fails |
| 8 | 5 | Flywheel tighten-one-control | Skip if over time |

## Sticky-note utterances

- “Hi Telano”
- “What is the difference between rebooting and resetting a router?”
- “Can you explain my February bill?”
- “My internet is slow”
- “Please factory-reset my router”
- “I want a human”
- “Thanks, that’s all”

## Demo facts (cheat sheet)

```bash
make show-demo-data
```

- Customer: **Serena Williams** / id `123` (loaded by `default_session_start`)
- February bill: **$55.00** Internet
- Router: **RTR-123-01** RasaGate Fiber X1
- Factory-reset tool name: **`factory_reset_router`** (skill remains `reset_router`)

## Escape hatches

1. **Anything broken mid-session:** `make verify`, then `make inspect` on the
   finished tree (this repo’s `main` / current finished skills).
2. **Train fails:** `make clean && make train`. If the archive is tiny (&lt;10 KB),
   treat it as a stub and retrain.
3. **Voice fails on Zoom:** use Inspector text input; continue the same script.
4. **Over time:** skip Step 6 typing; jump to finished skills + Step 7 voice.

## Recovery checkpoints

See [`TAGS.md`](TAGS.md) for git-style recovery points named by teaching step.
