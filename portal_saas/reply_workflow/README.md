# AI Reply Workflow Entry

R007 defines a review-only reply workflow:

- replies are generated as drafts under `runtime/workspaces/<workspace_id>/reply_drafts/`;
- every reply draft defaults to `review_status=needs_review`;
- hard-sell and impersonation risks are tagged before review;
- no reply is sent automatically.

This round does not connect to real comment systems and does not impersonate users.
