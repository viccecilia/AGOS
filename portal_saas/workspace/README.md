# Product Workspace Entry

R002 defines the Workspace as the primary isolation boundary:

- one customer/product maps to one workspace;
- knowledge, pain points, content, replies, reports, and AI settings must be scoped by `workspace_id`;
- workspace metadata is stored under `runtime/workspaces/<workspace_id>/workspace.json`;
- later portal pages should call `services.workspace_service.WorkspaceStore` instead of reading raw files directly.

This entry intentionally does not implement promotion logic. That starts in later rounds after the workspace boundary is stable.
