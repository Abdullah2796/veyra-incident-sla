# Business requirements

> Veyra Safety Services is a fictional company. All data in this project is synthetic.

## Context
Veyra monitors connected fire and smoke alarm panels at 2,400 customer sites across six municipalities. Incidents are raised automatically by monitoring or by customers (phone, portal, email). They are handled by three internal teams (NOC Level 1, NOC Level 2, Platform Engineering) and three field vendors, each covering two municipalities.

## Audience and questions

| Audience | Questions |
|---|---|
| Operations manager | Are we within SLA? Where and when do we miss it? |
| Vendor manager | Which vendor is slowest, and how does it compare with internal teams? |
| NOC team lead | How big and how old is the open backlog? What is unassigned? |
| Customer success | Does resolution speed affect satisfaction? What do customers complain about? |

## SLA policy

| Priority | Response target | Resolution target |
|---|---|---|
| P1 Critical | 15 min | 4 hrs |
| P2 High | 30 min | 8 hrs |
| P3 Moderate | 2 hrs | 24 hrs |
| P4 Low | 8 hrs | 72 hrs |

The service runs 24/7, so SLA clocks use calendar time.

## KPI targets

| KPI | Target | Weight |
|---|---|---|
| Resolution SLA met | ≥ 90% | 30% |
| Response SLA met | ≥ 95% | 20% |
| Reopen rate | ≤ 4% | 15% |
| CSAT (1–5) | ≥ 4.2 | 20% |
| Backlog older than SLA | ≤ 10% | 15% |

## Business rules
- Response time = acknowledged − opened. Resolution time = resolved − opened.
- An incident with a resolved timestamp before its opened timestamp is excluded from resolution time and SLA, and reported in the data-quality log.
- "Business hours" = Monday to Friday, 07:00–20:00. Everything else is "Evenings & weekends".
- An open incident is "aged" when its age exceeds the resolution target for its priority.
- CSAT only counts survey responses that match a known incident.
