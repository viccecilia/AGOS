# ROUND-PREDICT-001

## Round Name
AGOS_SEASONAL_DEMAND_CALENDAR_ENGINE

## Phase
PREDICTIVE_DEMAND_INTELLIGENCE

## Goal
Build the Seasonal Demand Calendar Engine so AGOS can understand Japan tourism seasons, holidays, event placeholders, and Google Trends keyword monitoring structure.

## Scope
- Add `services/seasonal_demand_calendar_engine.py`
- Add `runtime/seasonal_demand_calendar/`
- Generate seasonal calendar, keywords, monitoring plan, and summary
- Update `docs/project_control_center.html`
- Add `tests/seasonal_demand_calendar_smoke_test.py`

## Safety Boundary
This round uses local sample/manual-import-ready seasonal planning data only. It does not call Google Trends, scrape login-only data, post, reply, contact customers, dispatch drivers, or call platform write APIs.
