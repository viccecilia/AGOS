# ROUND-GROWTH-PLUGIN-005

## Round Name
AGOS_CROSS_PLATFORM_PROMOTION_PLAN_ENGINE

## Phase
MERCHANT_HOMEPAGE_GROWTH_ENGINE

## Goal
Build Cross-Platform Promotion Plan Engine so AGOS can expand one answer draft into platform-specific homepage promotion plans.

## Scope
- Read `runtime/answer_to_homepage_drafts/answer_drafts.json`.
- Generate plans for Reddit, TikTok, Instagram, X, YouTube, Threads, SEO, and Xiaohongshu.
- Generate content calendar draft, platform priority, and human review queue.
- Keep every plan in `needs_human_review`.
- Keep `auto_publish_allowed=false`.

## Safety Boundary
This round does not auto-publish, schedule posts, operate real accounts, send DMs, or call platform write APIs.
