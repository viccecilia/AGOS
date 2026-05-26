# ROUND-GROWTH-PLUGIN-003

## Round Name
AGOS_OPPORTUNITY_QUALIFICATION_ENGINE

## Phase
MERCHANT_HOMEPAGE_GROWTH_ENGINE

## Goal
Build Opportunity Qualification Engine so AGOS can decide which Problem Seeker candidates are worth using for merchant homepage promotion.

## Scope
- Read `runtime/problem_seeker_loop/problem_candidates.json`.
- Score each candidate by pain strength, homepage fit, answerability, platform suitability, conversion potential, risk level, spam risk, and brand fit.
- Classify opportunities as `high_value`, `monitor`, `low_value`, or `unsafe`.
- Keep every opportunity human-gated and block automatic promotion actions.

## Safety Boundary
This round does not generate replies, post, contact users, perform real platform interaction, or execute any promotion action.
