# MindFoundry — 60-second Quickstart

For judges, reviewers, or anyone who wants to see the whole stack run end-to-end on a fresh clone.

## Prereqs

- Python 3.11+
- `git`, `curl`
- macOS, Linux, or WSL2

## Run

```bash
git clone https://github.com/CloseForge-org/mindfoundry.git
cd mindfoundry

# Your own NVIDIA NIM key — get one at https://build.nvidia.com/
export NVIDIA_NIM_API_KEY="nvapi-..."

make setup        # venv + pip + generate the simulated hotel
make api          # start the retrieval API in the background
make demo         # run the end-to-end walkthrough
```

`make demo` prints, in sequence:

1. **API health check** — verifies the retrieval layer is up.
2. **Nemotron RAG answer** — a real ops question synthesized via NVIDIA NIM with `[n]` citations.
3. **Adversarial probe** — the same agent refusing to leak PII, with the NemoClaw policy gate redactions shown.
4. **Baseline evaluation summary** — 500 incidents, 100% on routing / policy / privacy / no-hallucination.

If any step fails, `make doctor` prints what's missing.

## Common overrides

```bash
# Use a different NIM model
export NVIDIA_NIM_MODEL="nvidia/llama-3.1-nemotron-70b-instruct"

# Port 8765 is taken by something else (e.g. on a shared dev box)
export HOTELSIM_PORT=8766
make api && make demo
```

## Other targets

| Target | What it does |
| --- | --- |
| `make help` | Show all targets with short descriptions |
| `make smoke` | Quick Nemotron-only smoke test (skips API server, no SQLite touch) |
| `make eval` | Run only the 500-incident baseline evaluation, write `reports/eval-baseline-500.json` |
| `make discord` | Drip one simulated incident into the live Discord (needs `DISCORD_BOT_TOKEN`) |
| `make doctor` | Print environment diagnostics (Python, venv, NIM key, port, etc.) |
| `make stop` | Stop the background API |
| `make clean` | Remove generated state (SQLite, reports, caches) |
| `make reset` | `make clean` + remove the venv |

## What you should see (sample)

```
=== 1. Local retrieval API health ===
OK  http://127.0.0.1:8765/health -> {'ok': True, ...}

=== 2. RAG synthesis (Nemotron via NVIDIA NIM) ===
USED NIM  model=nvidia/llama-3.3-nemotron-super-49b-v1.5  redactions=0
**NeMo Lodge RAG · Nemotron**
Question: How should we handle a guest who cannot access their room?
...

=== 3. Adversarial probe (Nemotron refusal + NemoClaw redaction) ===
USED NIM  model=nvidia/llama-3.3-nemotron-super-49b-v1.5  redactions=2
Policy gate scrubbed:
  - internal_note: internal_notes for the m
  ...

=== 4. Baseline evaluation (500 incidents) ===
  evaluated:              500
  routing_accuracy:       100.0%
  policy_grounding_rate:  100.0%
  privacy_pass_rate:      100.0%
  hallucination_pass:     100.0%
```

That's the full hackathon money shot from a fresh clone in under five minutes.
