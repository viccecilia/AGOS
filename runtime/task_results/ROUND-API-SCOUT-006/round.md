# ROUND-API-SCOUT-006

## Round Name
AGOS_API_TO_SCOUT_PIPELINE

## Phase
PLATFORM_API_SCOUT_INTEGRATION

## Goal
建立 API → Scout Pipeline，让 AGOS 能把平台 API 趋势接入 Scout Intelligence 链路。

## Scope
- 新增 `services/api_to_scout_pipeline.py`
- 输出 `runtime/api_scout_pipeline/`
- 在 War Room 控制中心显示 API Scout Feed
- 保持本轮为只读、本地 JSON pipeline，不执行外部平台动作

## Safety Boundary
本轮不实现发帖、回复、关注、DM，不抓取登录数据，也不绕过平台限制。
