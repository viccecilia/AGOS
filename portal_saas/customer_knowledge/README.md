# Customer Knowledge Base Entry

R003 defines a workspace-scoped knowledge base:

- every knowledge base is stored under `runtime/workspaces/<workspace_id>/knowledge_base.json`;
- every record must bind to an existing `workspace_id`;
- supported sections are brand voice, product facts, FAQ, industry notes, and content templates;
- later content generation rounds should read this service instead of using shared global prompt text.

This round does not connect to external platforms and does not generate promotional content.
