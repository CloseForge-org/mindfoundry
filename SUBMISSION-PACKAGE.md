# MindFoundry — Airtable Submission Package

**Form:** https://airtable.com/appuGjP9jaVJtwxJt/pagqXe6ElIlXx6oa3/form
**Deadline:** May 28, 2026 · 12:00 PM Taiwan Time

Copy/paste these directly into the corresponding Airtable fields. Fill the `<TBD>` slots last (demo video URL).

---

## Project / Product Name
```
MindFoundry
```

## One-line description / Tagline
```
NemoClaw-secured long agent that builds AI replicants of your teammates and answers operational questions on their behalf, with cited Nemotron synthesis.
```

## Short description (≈ 100 words)
```
MindFoundry is a NemoClaw-secured autonomous agent that continuously interviews your team across Discord, docs, and chat history, builds a structured "replicant" of every teammate's knowledge, and answers operational questions in their voice — with inline citations and policy-enforced privacy. Powered by Nemotron via NVIDIA NIM for reasoning, NemoClaw for filesystem / network / inference guardrails, and OpenClaw for the long-running agent runtime. Reference deployment: NeMo Lodge, a 250-room simulated hotel with 8 staff replicants, 500 incidents, bilingual ops (English + Traditional Chinese), Discord team comms, and 100% baseline scores on routing, policy, privacy, and no-hallucination.
```

## Long description (≈ 200 words)
```
In every team, the most valuable operational knowledge lives in people's heads, scrollback, and a few Google Docs nobody re-reads. When the right person is asleep, on leave, or overwhelmed, that knowledge is inaccessible — decisions stall, mistakes repeat, institutional memory decays.

MindFoundry is a persistent autonomous agent that builds a living replicant of every teammate. It reads chat and docs, extracts durable facts and decision patterns, stores them as structured memory with confidence and freshness, and answers operational questions via RAG — citing the right teammate's memory, the right policy doc, and the right live-ops signal.

The agent is wrapped in NemoClaw policy guardrails that enforce filesystem allowlists, network egress rules, and a PII redaction layer that catches passwords, guest emails, phone numbers, payment data, passport IDs, and internal_notes before they ever leave the agent. Every gate decision is logged to an immutable audit trail.

The reference deployment is NeMo Lodge, a 250-room simulated hotel with 8 staff replicants, 500 incidents, and a fully wired bilingual Discord ops surface. Baseline evaluation scores 100% on routing, policy grounding, privacy, and no-hallucination. Powered by Nemotron via NVIDIA NIM, NemoClaw, and OpenClaw.
```

## GitHub Repository URL
```
<TBD - inserted after gh repo create>
```

## Demo Video URL
```
<TBD - YouTube unlisted link, paste after upload>
```

## NVIDIA Tools Used
```
• Nemotron (model: nvidia/llama-3.3-nemotron-super-49b-v1.5) — core reasoning: RAG synthesis, knowledge extraction, routing, action drafting
• NVIDIA NIM — model inference endpoint (https://integrate.api.nvidia.com/v1), OpenAI-compatible chat completions
• NemoClaw / OpenShell — policy-based guardrails: filesystem allowlists, network egress rules, PII redaction layer, role-based egress (public_discord, finance_private, manager_private), per-decision audit logging
• OpenClaw — long-running agent runtime: heartbeats, scheduled cron jobs (drip / RAG / replicant updater), Discord integration across 10 channels, subagent orchestration, SQLite + JSONL persistence
```

## Team
```
Roger Lee (lead, hospitality ops domain expertise)
Jarvis (AI agent collaborator, OpenClaw — engineering, data generation, evaluation, policy gate, RAG bridge)
```

## Contact Email
```
roger@closeforge.org
```
(Use whichever email matches Roger's Luma registration if different — confirm before submitting.)

---

## Hackathon Scoring Self-Assessment

| Criterion | Status |
| --- | --- |
| Runs autonomously (no human in loop) | ✅ Long agent loop: gather → extract → update → answer; scheduled cron jobs (drip 15min, RAG 2min, replicant updater 5min) |
| Uses Nemotron as core reasoning model | ✅ `nvidia/llama-3.3-nemotron-super-49b-v1.5` via NIM; smoke-tested in `reports/nemotron-smoke-test.json` |
| Performs real task | ✅ Cited RAG retrieval, routing, draft guest replies, audit logging |
| Deployable and persistent | ✅ Runs on Mac mini, SQLite + JSONL persistence, OpenClaw heartbeats |
| ⭐ Bonus: NemoClaw guardrails | ✅ Policy YAML at `docs/openshell-policy-neemo-lodge.yaml`; runtime enforcement in `hotel_sim/policy_gate.py`; adversarial PII probes redacted before send |

---

## Pre-submission Checklist

- [ ] Confirm Luma registration at https://luma.com/agent-challenge (Roger must do this personally if not done).
- [ ] Verify GitHub repo URL is correct and publicly accessible.
- [ ] Record demo video (script at `docs/demo-script.md`).
- [ ] Upload to YouTube as **unlisted**; copy the share link.
- [ ] Paste video URL into this file and into the Airtable form.
- [ ] Submit form at https://airtable.com/appuGjP9jaVJtwxJt/pagqXe6ElIlXx6oa3/form.
- [ ] Confirm submission email/receipt.

---

## Notes for Roger before submitting

1. The Airtable form is the official submission. The README, demo script, and this package are all written so that copy/paste in <60 seconds gets you across the line.
2. Verify the contact email matches your Luma registration.
3. The demo video is the only deliverable Jarvis can't produce — please record from `docs/demo-script.md`.
4. After uploading the video, edit `README.md` and this file to replace the two `<TBD>` placeholders; push the update.
