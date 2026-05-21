# AI Content Factory Entry

R006 defines a review-only content draft factory:

- inputs must come from Workspace knowledge and Workspace pain points;
- generated drafts stay under `runtime/workspaces/<workspace_id>/content_drafts/`;
- every draft has `review_status=needs_review` by default;
- supported draft targets include TikTok, Instagram, Reddit, YouTube, and SEO.

This round does not publish content and does not call external AI providers.
