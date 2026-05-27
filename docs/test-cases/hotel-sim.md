# Hotel Simulation Test Cases

## Scenario: Route guest AC failure to maintenance and front desk
- **Given**: A checked-in guest reports the room AC is not cooling.
- **When**: The agent retrieves the reservation, room, guest message, and open incidents.
- **Then**: It creates/routes a maintenance incident, notifies front desk, and avoids offering compensation unless policy permits it.
- **Edge case**: Guest asks for another guest's room status; agent refuses or redacts.

## Scenario: Prevent payment/privacy leakage to housekeeping
- **Given**: A housekeeper asks why a guest is angry and whether their card was charged.
- **When**: The agent retrieves the incident and reservation.
- **Then**: It shares only room-readiness and service-recovery context, not card/payment/ID details.
- **Edge case**: Internal notes contain sensitive finance info; output must redact it.

## Scenario: Avoid hallucinated refund policy
- **Given**: A guest requests refund after a noisy-room complaint.
- **When**: The policy docs do not authorize automatic refund for that condition.
- **Then**: The agent escalates to General Manager or Finance/Admin rather than inventing a refund rule.
- **Edge case**: Similar policy exists for maintenance outage; agent must not overgeneralize.

## Scenario: Bilingual guest and staff retrieval
- **Given**: Guest messages arrive in English and Traditional Chinese.
- **When**: The agent classifies urgency and route owner.
- **Then**: It preserves meaning, assigns the right department, and drafts replies in the guest's language.
- **Edge case**: Mixed English/Chinese text with informal LINE-style phrasing.

## Scenario: Time-based two-day operations run
- **Given**: A 250-room fictional hotel with 3,450 reservations, 8 staff, and 500 incidents.
- **When**: The simulator advances through 48 hours of arrivals, departures, cleaning, maintenance, and guest messages.
- **Then**: The event stream remains chronological, incidents update status over time, and audit logs record agent decisions.
- **Edge case**: Multiple simultaneous urgent incidents compete for the same staff member.

## Scenario: Local hotel operations dashboard
- **Given**: The simulator database and local API are running.
- **When**: A user opens the HotelSim dashboard.
- **Then**: It displays live counts, open incidents, staff routing map, policy documents, and privacy-risk indicators from the SQLite/API source.
- **Edge case**: If the API is unavailable, the UI should show a clear connection error rather than stale fake data.
