# ROUND-API-SCOUT-004 Tasks

## TASK-001
状态：done

新增 `services/api_rate_limit_guard.py`。

## TASK-002
状态：done

支持 `requests/minute`、`requests/hour`、`requests/day` 限制检测。

## TASK-003
状态：done

建立 API Risk Feed，并输出到 `runtime/api_risk/api_risk_feed.json`。

## TASK-004
状态：done

检测 unusual frequency、repeated queries、suspicious pattern。

## TASK-005
状态：done

输出 `runtime/api_risk/API_RATE_LIMIT_GUARD_REPORT.json`、`api_risk_feed.json`、`api_usage_summary.json`。

## REVIEW-001
状态：done

控制中心显示 AGOS 是否正在接近平台风控。
