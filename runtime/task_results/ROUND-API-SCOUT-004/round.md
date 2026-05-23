# ROUND-API-SCOUT-004

## Round Name
AGOS_API_RATE_LIMIT_AND_SAFETY_GUARD

## Phase
PLATFORM_API_SCOUT_INTEGRATION

## Goal
建立 API Safety Guard，让 AGOS 在使用平台 API 前能够监控请求频率、重复查询和可疑读取模式，避免接近平台风控边界。

## Scope
- 新增 `services/api_rate_limit_guard.py`
- 输出 `runtime/api_risk/`
- 在 War Room 控制中心显示 API Risk Feed
- 保持所有行为为本地只读风险评估

## Safety Boundary
本轮不实现发帖、回复、关注、DM、自动互动，也不绕过任何平台限制。
