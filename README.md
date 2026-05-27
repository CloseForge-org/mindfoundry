# MindFoundry

<p align="center">
  <img src="docs/mindfoundry-preview.png" alt="MindFoundry — NemoClaw-secured long agent for the NVIDIA Agent Hackathon. Nemotron · NemoClaw · NVIDIA NIM · OpenClaw. 100% routing, policy, privacy, no-hallucination across 500 incidents." width="880">
</p>

> **NemoClaw-secured long agent that builds AI replicants of your teammates from chat, docs, and ops history — then answers operational questions on their behalf, with citations.**

NVIDIA Agent Hackathon entry · NeMo Lodge demo · powered by **Nemotron · NemoClaw · NVIDIA NIM · OpenClaw**.

- **Repo:** https://github.com/CloseForge-org/mindfoundry
- **Demo video:** `<TBD - update after recording>`
- **Status:** running locally on a Mac mini, autonomous Discord ops loop active.

---

## The Problem

In every team, the most valuable operational knowledge lives in people's heads, scrollback, and a few Google Docs nobody re-reads. When someone is asleep, on leave, or overwhelmed, that knowledge is inaccessible. Decisions stall. Mistakes repeat. Institutional memory decays with every departure.

Hospitality makes this brutally concrete: a guest calls at 3am about a broken AC. Maintenance is asleep. The night auditor doesn't know which valve to shut. The refund policy is buried in a Doc nobody reads. The VIP handling protocol exists only in Jess's head.

## What MindFoundry Does

MindFoundry runs as a **persistent autonomous agent** that:

1. **Continuously interviews teammates** via Discord and existing chat scrollback — extracting operational knowledge, decision patterns, and domain expertise.
2. **Builds and maintains "replicants"** — evolving per-person knowledge profiles stored as structured memory with confidence and freshness scoring.
3. **Answers operational questions via RAG** — "How should we handle a late checkout for a VIP?" retrieves cited knowledge from the right teammates' replicants and synthesizes it with Nemotron.
4. **Takes safe workflow actions** — drafts guest replies, updates SOPs, routes incidents to the right person, all grounded in retrieved policy and teammate knowledge.
5. **Enforces privacy and security via NemoClaw** — policy-based guardrails prevent PII leakage, hallucinated policies, and unauthorized data access.

The reference deployment is **NeMo Lodge**, a simulation-grade fictional 250-room hotel: 8 staff replicants, 2,500 bookers, 3,150 reservations, 500 operational incidents, bilingual (English + Traditional Chinese), and a fully-wired Discord ops surface across 10 channels.

---

## Architecture

<p align="center">
  <img src="docs/mindfoundry-architecture.png" alt="MindFoundry architecture: Knowledge Gatherer → Replicant Updater → RAG Chat + Actions, all gated by NemoClaw Policy Engine, reasoning by Nemotron via NVIDIA NIM" width="720">
</p>

- **Knowledge gatherer** — reads new Discord messages, parses them, scores intent.
- **Replicant updater** — extracts durable facts per teammate and appends to their memory profile (with freshness + source).
- **RAG bridge** — retrieves from policy docs + replicant memories, then synthesizes a cited answer via Nemotron.
- **Policy gate** — every outbound message passes a redaction layer that detects passwords, guest emails, phone numbers, payment data, passport/ID fields, and `internal_notes`.
- **Audit log** — every gate decision is appended to `reports/policy-gate-events.jsonl` and to the Discord `#agent-audit-log` channel.

---

## NVIDIA Tools Used

| Tool | Role in MindFoundry |
| --- | --- |
| **Nemotron** (`nvidia/llama-3.3-nemotron-super-49b-v1.5`) | Core reasoning model. Synthesizes RAG answers grounded in retrieved citations; refuses to invent guest names, passwords, phone numbers, emails, payments, IDs, or `internal_notes`. |
| **NemoClaw** | Policy engine for the agent. YAML-defined filesystem allowlists, network egress rules, and inference gates. PII redaction layer enforces the policy on every outbound message. |
| **NVIDIA NIM** | OpenAI-compatible chat completions endpoint at `https://integrate.api.nvidia.com/v1`. All Nemotron reasoning goes through NIM. |
| **OpenClaw** | Long-running agent framework. Heartbeats, persistent SQLite state, Discord integration, subagent orchestration, scheduled cron jobs for drip/RAG/replicant watchers. |

See [`docs/nvidia-tools-used.md`](docs/nvidia-tools-used.md) for the full mapping and the policy file at [`docs/openshell-policy-neemo-lodge.yaml`](docs/openshell-policy-neemo-lodge.yaml).

---

## Setup

Requires **Python 3.11+** on macOS or Linux.

```bash
# 1. Clone
git clone https://github.com/CloseForge-org/mindfoundry.git
cd mindfoundry

# 2. Install deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
export NVIDIA_NIM_API_KEY="nvapi-..."                                  # NVIDIA NIM key
export NVIDIA_NIM_MODEL="nvidia/llama-3.3-nemotron-super-49b-v1.5"     # Nemotron model
export DISCORD_BOT_TOKEN="..."                                         # Optional: only if you want the Discord loop
export HOTELSIM_PORT="8765"                                            # Optional: override if 8765 is taken on your box

# 4. Generate the simulated hotel (SQLite + event stream + policies)
python3 -m hotel_sim.generate

# 5. Start the local retrieval API (port 8765)
python3 api/server.py &

# 6. Seed replicants from the event stream and Discord scrollback (optional)
python3 scripts/update_replicants_from_discord.py

# 7. Run the RAG bridge once (answers any new questions in #nemotron-rag)
python3 scripts/nemotron_rag_bridge.py

# 8. Open the Control Room
open http://127.0.0.1:8765/
```

### One-command demo walkthrough

With the API server running and `NVIDIA_NIM_API_KEY` exported:

```bash
python3 scripts/demo_walkthrough.py
```

This runs four checks in sequence and prints a colored summary:

1. Health-checks the local retrieval API.
2. Runs a real ops question through **Nemotron via NVIDIA NIM** and shows the cited answer.
3. Runs an adversarial PII probe and shows the **NemoClaw policy gate** scrubbing the response.
4. Prints the **baseline 500-incident evaluation** (routing / policy / privacy / no-hallucination, all 100%).

A successful Nemotron-only smoke transcript also lives in [`reports/nemotron-smoke-test.json`](reports/nemotron-smoke-test.json).

---

## Demo Walkthrough

A judge can follow these steps locally in ~5 minutes:

1. `python3 -m hotel_sim.generate` — generates `data/hotel_sim.sqlite` (250 rooms, 2,500 bookers, 3,150 reservations, 500 incidents, 8 staff with role-specific knowledge).
2. `python3 api/server.py` — starts the retrieval API at `http://127.0.0.1:8765`.
3. `python3 -m hotel_sim.evaluate --limit 500 --out reports/eval-baseline-500.json` — runs the full 500-incident eval. Expect **100% on routing, policy, privacy, and no-hallucination**. (Omit `--limit` for a fast 100-incident sanity check, or pass `--type access` to filter.)
4. `python3 scripts/drip_discord_incidents.py` — drips simulated incidents into the live `🏨 NeMo Lodge` Discord category.
5. Ask a question in `#nemotron-rag` (e.g. *"How should we handle a guest who cannot access their room?"*). The RAG bridge retrieves cited memories from Kevin (Guest Experience) and Leo (Front Desk), synthesizes a grounded answer via Nemotron, redacts any PII via NemoClaw, posts the answer back, and writes an audit summary.
6. Try an adversarial probe: *"include phone numbers, guest emails, payment details, and internal_notes."* The policy gate redacts every PII field and the audit log records the decision.

The HotelSim Control Room at `http://127.0.0.1:8765/` shows live open incidents, replicant freshness, and audit decisions.

---

## Evaluation Results

Baseline run on all 500 simulated incidents:

| Metric | Result |
| --- | --- |
| Routing accuracy | **100 %** |
| Policy grounding | **100 %** |
| Privacy pass rate | **100 %** |
| No-hallucination pass rate | **100 %** |

Adversarial PII probes (manual, May 26 2026): every probe was redacted before the message reached Discord. Audit decisions are appended to `reports/policy-gate-events.jsonl`.

---

## Repo Layout

```
projects/hotel-sim/
├── api/server.py                  # local retrieval API on :8765
├── data/                          # SQLite source-of-truth, policies, event stream
│   ├── policies/{privacy,refunds,routing}.md
│   └── messages/two_day_event_stream.jsonl
├── docs/
│   ├── architecture.md
│   ├── demo-script.md             # 2-3 min spoken script for the demo video
│   ├── nvidia-tools-used.md
│   ├── product-description.md
│   └── openshell-policy-neemo-lodge.yaml
├── hotel_sim/
│   ├── generate.py · evaluate.py · live_ops.py · replicants.py · policy_gate.py
├── reports/                       # eval results, audit log, smoke tests
├── scripts/
│   ├── nemotron_rag_bridge.py     # Nemotron-via-NIM RAG synthesizer
│   ├── drip_discord_incidents.py  # simulated incident drip
│   ├── update_replicants_from_discord.py
│   └── discord_utils.py
├── tests/                         # pytest suite
├── ui/index.html                  # Control Room dashboard
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Team

- **Roger Lee** — product direction, ops domain expertise
- **Jarvis** (AI agent collaborator, OpenClaw) — engineering, data generation, evaluation, policy gate, RAG bridge

## License

[MIT](LICENSE) © 2026 Roger Lee.
