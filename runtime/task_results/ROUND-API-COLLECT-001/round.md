# ROUND-API-COLLECT-001

## Round Name

AGOS_PLATFORM_ACCOUNT_CONNECTION_CENTER

## Phase

CONTROLLED_API_INTELLIGENCE_COLLECTION

## Goal

建立 Platform Account Connection Center，让 AGOS 能够管理平台 API 账号连接状态。

## Scope

- 新增 `services/platform_account_connection_center.py`
- 支持 Reddit / YouTube / X / TikTok / Instagram / Threads
- 显示 `connection_status` / `read_permission` / `write_permission` / `token_expiration` / `workspace_scope`
- 默认 `write_permission=false`
- 新增 `runtime/platform_connections/`
- 更新 War Room 的 Platform Connection Center 面板

## Safety Boundary

本轮只管理本地连接状态，不调用真实平台 API，不启用写权限，不自动发帖、不自动回复、不自动注册账号。
