# ROUND-API-SCOUT-005

## Round Name
AGOS_API_SIGNAL_NORMALIZATION

## Phase
PLATFORM_API_SCOUT_INTEGRATION

## Goal
建立 API Signal Normalization，让 AGOS 能把 TikTok trends、Reddit hot topics、YouTube search、X trend data 统一理解为同一套增长信号字段。

## Scope
- 新增 `services/api_signal_normalization.py`
- 输出 `runtime/api_normalized_signals/`
- 在 War Room 控制中心显示 API Signal Normalization 面板
- 保持本轮为只读、本地 JSON 归一化

## Safety Boundary
本轮不实现发帖、回复、关注、DM，也不调用写侧平台 API。
