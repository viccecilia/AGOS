# ROUND-EXT-003

## Round Name

MANUAL_EXTERNAL_FEEDBACK_INTAKE

## Goal

Build manual intake for external feedback without automatic platform collection.

## Scope

- Support human-entered views, likes, replies, saves, comments, and rejection reason.
- Mark imported feedback with `feedback_source=manual_import`.
- Connect evidence-approved feedback into `PromotionFeedbackLearning`.
- Block feedback without evidence from learning memory.

## Safety Boundary

This round does not crawl platforms, verify external pages, call platform APIs, post, reply, DM, follow, like, or log in.
