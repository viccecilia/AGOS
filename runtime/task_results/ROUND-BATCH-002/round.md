# ROUND-BATCH-002

## Round Name
AGOS_BATCH_TOPIC_CLUSTERING

## Phase
RUNTIME_BATCH_INTELLIGENCE

## Goal
建立 Batch Topic Clustering，让 AGOS 能够从批量问题中自动发现高价值问题群。

## Scope
- 新增 `services/batch_topic_clustering.py`
- 批量聚类相似问题、高频问题、高情绪问题、高增长信号
- 输出 Batch Trend Clusters
- 建立 `runtime/batch_clusters/`
- 在 War Room 控制中心显示 Batch Topic Clustering Panel

## Safety Boundary
本轮只处理本地 batch analysis，不自动发帖、回复、follow、DM，不调用任何外部 write API。
