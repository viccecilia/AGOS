# ROUND-GROWTH-PLUGIN-004

## Round Name
AGOS_ANSWER_TO_HOMEPAGE_DRAFT_ENGINE

## Phase
MERCHANT_HOMEPAGE_GROWTH_ENGINE

## Goal
Build Answer-to-Homepage Draft Engine so AGOS can turn high-value qualified opportunities into helpful answer drafts that solve the user problem first and softly reference the merchant homepage.

## Scope
- Read `runtime/opportunity_qualification/qualified_opportunities.json`.
- Generate answer drafts for high-value opportunities.
- Support Reddit, TikTok, Instagram, X, YouTube, Threads, SEO, and Xiaohongshu platform tones.
- Keep every draft in `needs_human_review`.
- Keep `auto_publish_allowed=false`.

## Safety Boundary
This round does not auto-post, auto-reply, send DMs, operate real accounts, or call platform write APIs.
