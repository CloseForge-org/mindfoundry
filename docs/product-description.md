# MindFoundry — Product Description

## One-liner

**MindFoundry is a NemoClaw-secured long agent that builds AI replicants of your teammates from chat, docs, and ops history — then answers operational questions on their behalf, with citations.**

## Short description (≈ 100 words)

MindFoundry is a NemoClaw-secured autonomous agent that continuously interviews your team across Discord, docs, and chat history, builds a structured "replicant" of every teammate's knowledge, and answers operational questions in their voice — with inline citations and policy-enforced privacy. Powered by Nemotron via NVIDIA NIM for reasoning, NemoClaw for filesystem / network / inference guardrails, and OpenClaw for the long-running agent runtime. The reference deployment is NeMo Lodge, a 250-room simulated hotel with 8 staff replicants, 500 incidents, bilingual ops (English + Traditional Chinese), Discord-driven team comms, and 100% baseline scores on routing, policy, privacy, and no-hallucination.

## Long description (≈ 200 words)

In every team, the most valuable operational knowledge lives in people's heads, scrollback, and a few Google Docs nobody re-reads. When the right person is asleep, on leave, or overwhelmed, that knowledge is inaccessible — decisions stall, mistakes repeat, institutional memory decays.

MindFoundry is a persistent autonomous agent that **builds a living replicant of every teammate**. It reads chat and docs, extracts durable facts and decision patterns, stores them as structured memory with confidence and freshness, and answers operational questions via RAG — citing the right teammate's memory, the right policy doc, and the right live-ops signal.

The agent is wrapped in **NemoClaw policy guardrails** that enforce filesystem allowlists, network egress rules, and a PII redaction layer that catches passwords, guest emails, phone numbers, payment data, passport IDs, and `internal_notes` before they ever leave the agent. Every gate decision is logged to an immutable audit trail.

The reference deployment is **NeMo Lodge**, a 250-room simulated hotel with 8 staff replicants, 500 incidents, and a fully wired bilingual Discord ops surface. Baseline evaluation scores 100% on routing, policy grounding, privacy, and no-hallucination.

Powered by **Nemotron via NVIDIA NIM**, **NemoClaw**, and **OpenClaw**.

## Why this wins

1. **It's real, not a slide deck.** Working code, real data, real Discord channels.
2. **It's persistent.** Runs continuously; replicants accumulate over time.
3. **It's autonomous.** No human in the loop for knowledge gathering, RAG, or routing.
4. **It's secure by construction.** NemoClaw policy guards every file read, network call, and inference response.
5. **It solves a universal problem.** Institutional knowledge loss happens in every team; hospitality is just the concrete, high-stakes proof vertical.

## Team

- **Roger Lee** — product direction, hospitality operations domain expertise.
- **Jarvis** (AI agent collaborator, OpenClaw) — engineering, data generation, evaluation, policy gate, RAG bridge.
