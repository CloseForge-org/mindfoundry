# MindFoundry — Airtable Submission Package

**Form:** https://airtable.com/appuGjP9jaVJtwxJt/pagqXe6ElIlXx6oa3/form
**Deadline:** May 28, 2026 · 12:00 PM Taiwan Time

Copy/paste these into the matching Airtable fields. The form is JS-rendered, so field names are visible only when you're logged in via Luma. The values below cover every likely field.

---

## Quick-fill cheat sheet (most common fields)

| Field (most likely label) | Value |
| --- | --- |
| **Project / Product name** | `MindFoundry` |
| **Team name** | `MindFoundry` |
| **Lead / Submitter name** | `Roger Lee` |
| **Email** | `roger@closeforge.org` (or whichever you used for Luma) |
| **Country / Location** | `Taiwan` |
| **GitHub repo URL** | `https://github.com/CloseForge-org/mindfoundry` |
| **Demo video URL** | `<TBD - YouTube unlisted, paste after upload>` |
| **Live demo URL** (if asked) | leave blank, or `https://github.com/CloseForge-org/mindfoundry#one-command-demo-walkthrough` |
| **Open-source license** | `MIT` |

---

## Project name
```
MindFoundry
```

## Tagline (≤ 140 chars)
```
NemoClaw-secured long agent that builds AI replicants of your teammates and answers ops questions with cited Nemotron synthesis.
```

## Short description (≈ 100 words)
```
MindFoundry is a NemoClaw-secured autonomous agent that continuously interviews your team across Discord, Google Workspace, and ops history, builds a structured "replicant" of every teammate's knowledge, and answers operational questions in their voice — with inline citations and policy-enforced privacy. Powered by Nemotron via NVIDIA NIM for reasoning, NemoClaw for filesystem / network / inference guardrails, and OpenClaw for the long-running agent runtime. Reference deployment: NeMo Lodge, a 250-room simulated hotel with 8 staff replicants, 500 incidents, bilingual ops (English + Traditional Chinese), Discord team comms, and 100% baseline scores on routing, policy, privacy, and no-hallucination.
```

## Long description (≈ 250 words)
```
In every team, the most valuable operational knowledge lives in people's heads, scrollback, and a few Google Docs nobody re-reads. When the right person is asleep, on leave, or overwhelmed, that knowledge is inaccessible — decisions stall, mistakes repeat, institutional memory decays.

MindFoundry is a persistent autonomous agent that builds a living replicant of every teammate. It reads Discord chat, Google Workspace docs, and ops history, extracts durable facts and decision patterns, stores them as structured memory with confidence and freshness, and answers operational questions via Nemotron RAG — citing the right teammate's memory, the right policy doc, and the right live-ops signal.

The agent is wrapped in NemoClaw policy guardrails that enforce filesystem allowlists, network egress rules, and a PII redaction layer that catches passwords, guest emails, phone numbers, payment data, passport IDs, and internal_notes before they ever leave the agent. Every gate decision is logged to an immutable audit trail.

The reference deployment is NeMo Lodge, a 250-room simulated hotel with 8 staff replicants, 500 incidents, and a fully wired bilingual Discord ops surface. Baseline evaluation scores 100% on routing, policy grounding, privacy, and no-hallucination. The whole stack is reproducible from a fresh `git clone` in under five minutes, ending in a single `python3 scripts/demo_walkthrough.py` that exercises Nemotron, NemoClaw, and the eval suite end-to-end.

Powered by Nemotron via NVIDIA NIM, NemoClaw, and OpenClaw.
```

## Problem statement
```
Operational knowledge in every team is trapped in people's heads, chat scrollback, and unread docs. When the right person isn't available, decisions stall and institutional memory decays. We built MindFoundry to make every teammate's knowledge persistently queryable — safely.
```

## Solution / How it works
```
1. Knowledge Gatherer continuously reads Discord channels and Google Workspace (Docs, Sheets, Drive).
2. Replicant Updater extracts durable facts and decision patterns into per-teammate memory profiles with confidence and freshness scoring.
3. Nemotron RAG retrieves cited memories + policy docs and synthesizes a grounded answer via NVIDIA NIM.
4. NemoClaw policy engine enforces filesystem, network, and inference rules — PII is redacted before any outbound message.
5. Every decision is logged to an immutable audit trail.
```

## NVIDIA Tools / Stack
```
• Nemotron — nvidia/llama-3.3-nemotron-super-49b-v1.5; core reasoning for RAG synthesis, knowledge extraction, routing, action drafting
• NVIDIA NIM — model inference endpoint (https://integrate.api.nvidia.com/v1), OpenAI-compatible chat completions
• NemoClaw / OpenShell — policy-based guardrails: filesystem allowlists, network egress rules, PII redaction, role-based egress (public_discord, finance_private, manager_private), per-decision audit logging
• OpenClaw — long-running agent runtime: heartbeats, scheduled cron jobs (incident drip 15min, RAG watcher 2min, replicant updater 5min), Discord integration, subagent orchestration, SQLite + JSONL persistence
```

## Key features (if bulleted)
```
• Persistent autonomous agent (not a one-shot script)
• Cited Nemotron RAG with inline [n] references back to the source teammate memory or policy doc
• NemoClaw policy gate that scrubs PII before any outbound message (verified against adversarial probes)
• Bilingual operations: English + Traditional Chinese
• Discord-native team surface across 10 simulated hotel-ops channels
• Google Workspace integration: Docs, Drive, Sheets, Admin
• 500-incident baseline evaluation with 100% across routing, policy, privacy, and no-hallucination
• Single-command demo walkthrough for judges (`python3 scripts/demo_walkthrough.py`)
```

## Tech stack (general)
```
Python 3.11 · SQLite · Discord API · Google Workspace API · NVIDIA NIM · OpenClaw runtime · MIT license
```

## What was built during the hackathon window
```
The end-to-end MindFoundry stack: data generation, bilingual simulated hotel, 10 Discord channels with autonomous drip simulation, replicant memory format, retrieval API, Nemotron-via-NIM synthesizer, NemoClaw policy gate with PII redaction, audit logging, one-command demo walkthrough, evaluation harness with 500-incident baseline, full README and architecture diagram, and the NeMo Lodge Discord ops surface itself.
```

## GitHub repo URL
```
https://github.com/CloseForge-org/mindfoundry
```

## Demo video URL
```
<TBD - YouTube unlisted, paste after upload>
```

## Live demo URL
```
(Local-first; see README "One-command demo walkthrough" for setup. No public live URL — by design, the agent runs against private team Discord/Workspace.)
```

## License
```
MIT
```

## Team
```
Roger Lee — product direction, hospitality operations domain expertise
Jarvis (AI agent collaborator, OpenClaw) — engineering, data generation, evaluation, policy gate, RAG bridge
```

## Contact email
```
roger@closeforge.org
```
(Use whichever email matches your Luma registration. If Luma was registered under rogerblee@gmail.com, use that.)

## Country / Region
```
Taiwan
```

---

## Hackathon scoring self-assessment

| Criterion | Status |
| --- | --- |
| Runs autonomously (no human in loop) | ✅ Long agent loop: gather → extract → update → answer; cron jobs (drip 15min, RAG 2min, replicant updater 5min) |
| Uses Nemotron as core reasoning model | ✅ `nvidia/llama-3.3-nemotron-super-49b-v1.5` via NIM; live transcript in `reports/nemotron-smoke-test.json` |
| Performs real task | ✅ Cited RAG retrieval, routing, draft guest replies, audit logging |
| Deployable and persistent | ✅ Runs on Mac mini and any Linux/WSL host, SQLite + JSONL persistence |
| ⭐ Bonus: NemoClaw guardrails | ✅ Policy YAML at `docs/openshell-policy-neemo-lodge.yaml`; runtime enforcement in `hotel_sim/policy_gate.py`; adversarial PII probes redacted before send |
| Reproducibility | ✅ `git clone` → `make setup` → `make demo` (see README); `reports/eval-baseline-500.json` committed |

---

## Pre-submission checklist

- [x] Luma registration confirmed
- [x] GitHub repo public and judge-cloneable (verified fresh clone on Hulkbuster WSL)
- [x] README, architecture diagram, NVIDIA-tools doc, eval baseline JSON all committed
- [ ] Demo video recorded
- [ ] Video uploaded to YouTube as **unlisted**, share link copied
- [ ] Video URL pasted into `README.md` + `SUBMISSION-PACKAGE.md`, committed, pushed
- [ ] Airtable form submitted
- [ ] Submission email/receipt confirmed

---

## Notes for Roger before submitting

1. The Airtable form may have fewer or more fields than listed here — this package covers every common pattern. Use the matching value, skip ones the form doesn't ask for.
2. If the form asks for a **thumbnail / cover image**, use `docs/mindfoundry-preview.png` (1280×640 social card) — generated alongside this package.
3. Confirm the contact email matches your Luma registration before submitting.
4. After uploading the video, do the URL backfill commit before submitting so the README a judge clicks is fully populated.
