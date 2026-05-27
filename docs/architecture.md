# HotelSim Architecture

## Real-world pattern checked
Modern hotel systems typically separate these layers:

- PMS source of truth: guests, reservations, rooms, folios/payments, room status.
- Operations tools: housekeeping boards, maintenance work orders, guest requests, staff assignments.
- API/webhook layer: real-time updates for reservation changes, room status, tasks, payments, and guest messages.
- Messaging layer: guest messaging and internal staff comms connected to PMS/ops, but not the canonical database.
- SOP/policy knowledge base: refund, privacy, routing, escalation, and service recovery rules.

Examples reviewed: Oracle Hospitality OPERA/OHIP docs, Mews API positioning, Cloudbeds API docs, HotelKey PMS docs, Actabl/Alice, HelloShift, Agilysys, and housekeeping/PMS integration writeups.

## Chosen simulation architecture

- SQLite: canonical fake PMS + operations database.
- Local API: real-time retrieval surface for the AI agent.
- Markdown policy docs: retrieval-grounded SOP source to test hallucination.
- JSONL event stream: 48-hour chronological simulation.
- Discord: fake internal team chat.
- Google Workspace: fake staff workspace with Drive/Docs/Sheets/Calendar/Gmail and role-based permission tests.

## Current scale

- 250 rooms
- 2,500 bookers
- 3,150 reservations
  - 2,050 bookers with 1 reservation
  - 300 bookers with 2 reservations
  - 100 bookers with 3 reservations
  - 50 bookers with 4 reservations
- 8 staff
- 500 operations incidents/messages over two simulated days

Note: the correct reservation total is 3,150, not 3,450.
