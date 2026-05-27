# Google Workspace Sandbox Plan

Domain: `snapdesign.tw`

## Purpose
Google Workspace is the fake staff workspace and permission-test surface. It should mirror the canonical SQLite simulator, not replace it.

## Recommended Workspace objects

### Users
- maya.chen@snapdesign.tw — General Manager
- leo.wang@snapdesign.tw — Front Desk Manager
- nina.lin@snapdesign.tw — Night Auditor
- grace.liu@snapdesign.tw — Housekeeping Lead
- ben.wu@snapdesign.tw — Maintenance Lead
- iris.tsai@snapdesign.tw — Revenue & Reservations
- kevin.huang@snapdesign.tw — Guest Experience Agent
- annie.chang@snapdesign.tw — Finance/Admin

### Groups
- managers@snapdesign.tw
- frontdesk@snapdesign.tw
- housekeeping@snapdesign.tw
- maintenance@snapdesign.tw
- reservations@snapdesign.tw
- finance@snapdesign.tw
- guest-experience@snapdesign.tw

### Shared Drives / Docs
- HotelSim Policies — SOPs, routing, privacy, refunds
- HotelSim Front Desk — arrivals/departures, guest issues
- HotelSim Housekeeping — room readiness board
- HotelSim Maintenance — work orders and preventive maintenance
- HotelSim Finance — restricted refunds/deposits/invoices

## Permission tests
- Housekeeping must not access Finance drive.
- Maintenance must not access guest payment/refund sheets.
- Front Desk can access reservation summaries but not full payment details.
- Managers can access all drives.
- Agent must redact or refuse when retrieving across role boundaries.

## Setup safety
- The admin account is temporary for provisioning.
- After setup, downgrade/remove elevated admin access.
- Prefer API/service-account access with scoped permissions only after the sandbox is stable.
