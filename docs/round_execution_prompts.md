# AGOS 60 Round Execution Prompts

本文件是 AGOS 项目的逐轮执行任务词。每个 Round 执行前必须先验证前一个 Round 的结果；每个阶段验收 Round 必须暂停推进并通知用户验收。

## 全局执行规则

- 执行前先读取 `docs/project_control_center.html` 和本文件。
- 从 R002 开始，每轮执行前必须验证前一轮的 `runtime/task_results/<Round ID>/ROUND_SUMMARY.md`、验证记录、Git 状态和控制中心更新是否一致。
- 不允许跳过失败的前置验证。如果前置验证失败，先修复或向用户报告阻塞。
- 每轮完成后必须更新 `docs/project_control_center.html` 中对应 Round、模块进度、报告嵌入区和 Git 版本信息。
- 每轮完成后必须写入 `runtime/task_results/<Round ID>/ROUND_SUMMARY.md`。
- 阶段验收 Round：R012、R020、R030、R040、R048、R054、R060。执行完成后必须停止继续推进，并通知用户人工验收。

## 标准输出格式

```text
Round ID:
Round Name:

修改了什么:

每个任务状态:
- 执行任务:
- 测试任务:
- 协作验收任务:

验证结果:

协作验收结果:

未完成/风险:

下一轮建议:
```

---

## R001

Round ID: R001
Round Name: 通用 AI Growth OS 蓝图与控制中心

前置验证:
- 确认 `C:\PycharmProjects\AGOS` 可读写。
- 确认 `docs/project_control_center.html` 存在或需要创建。

本轮目标:
- 建立 AGOS 项目控制中心，作为后续 Codex 执行、Round 管理、Git 版本和报告入口。

本轮任务:
- 执行任务: 创建或完善 `docs/project_control_center.html`，包含项目总览、AI 完成度、60 Round 路线图、报告嵌入、Git 版本区、文件导航和新增 Round 模板。
- 测试任务: 验证 HTML 可解析、内置 JSON 可解析、Round 数量为 60、模块数量正确。
- 协作验收任务: 报告控制中心路径、预览方式、当前 Git 状态和后续维护方法。

允许修改:
- `docs/project_control_center.html`
- `docs/round_execution_prompts.md`
- `.gitignore`
- `runtime/task_results/R001/`

禁止修改:
- 尚未存在业务代码时，不创建无关业务模块。
- 不删除用户提供的原始蓝图文件。

必须运行的验证:
- JSON 解析验证。
- HTML 本地预览或 HTTP 预览验证。
- `git status --short`

完成定义:
- 控制中心可打开，显示 60 Round、模块进度、Git 状态和报告区。
- R001 报告已写入并嵌入控制中心。

输出格式:
- 使用标准输出格式。

---

## R002

Round ID: R002
Round Name: Product Workspace 架构

前置验证:
- 验证 R001 控制中心存在且能解析。
- 验证 R001 报告和 Git 提交状态一致。

本轮目标:
- 建立“一个客户/产品 = 一个 Workspace”的核心架构，防止不同客户、产品、内容和数据混用。

本轮任务:
- 执行任务: 设计 Workspace 数据结构、目录结构、基础页面入口和状态字段。
- 测试任务: 验证可以创建、读取、列出 Workspace；验证不同 Workspace 数据隔离。
- 协作验收任务: 向用户展示 Workspace 字段、路径和后续扩展方式。

允许修改:
- `portal_saas/workspace/`
- `schemas/workspace*`
- `models/workspace*`
- `services/workspace*`
- `runtime/task_results/R002/`
- `docs/project_control_center.html`

禁止修改:
- 不实现具体推广业务逻辑。
- 不混入 Japan AI Guide 专属逻辑。

必须运行的验证:
- 语法检查或项目可用的最小测试命令。
- Workspace 数据隔离 smoke test。
- 控制中心 R002 状态更新检查。

完成定义:
- Workspace 有清晰数据契约、入口和隔离规则。

输出格式:
- 使用标准输出格式。

---

## R003

Round ID: R003
Round Name: 客户知识库系统

前置验证:
- 验证 R002 Workspace 可创建、读取、隔离。
- 验证 R002 报告存在。

本轮目标:
- 为每个 Workspace 建立独立客户知识库，包含 FAQ、产品资料、品牌语气、行业资料和内容模板来源。

本轮任务:
- 执行任务: 创建知识库数据结构、导入入口、编辑入口和 Workspace 绑定。
- 测试任务: 验证不同 Workspace 的知识库互不污染；验证缺失字段有清晰提示。
- 协作验收任务: 展示一个示例客户知识库结构。

允许修改:
- `portal_saas/customer_knowledge/`
- `services/knowledge*`
- `schemas/knowledge*`
- `models/knowledge*`
- `runtime/task_results/R003/`
- `docs/project_control_center.html`

禁止修改:
- 不接入真实外部平台账号。
- 不自动生成推广内容。

必须运行的验证:
- 知识库 CRUD smoke test。
- Workspace 隔离测试。
- 控制中心 R003 更新检查。

完成定义:
- 每个 Workspace 可拥有独立知识库，且后续 AI 内容可引用。

输出格式:
- 使用标准输出格式。

---

## R004

Round ID: R004
Round Name: 官方账号矩阵中心

前置验证:
- 验证 R003 知识库可按 Workspace 读取。
- 验证控制中心中 R003 状态和报告已更新。

本轮目标:
- 管理每个 Workspace 的官方推广账号矩阵，支持 TikTok、Instagram、X、YouTube、Reddit、Threads、SEO 等渠道。

本轮任务:
- 执行任务: 建立账号矩阵模型、平台字段、账号状态、内容策略和风险状态。
- 测试任务: 验证同一 Workspace 可绑定多个平台账号；验证账号状态影响后续内容计划。
- 协作验收任务: 输出账号矩阵样例和平台字段说明。

允许修改:
- `portal_saas/account_matrix/`
- `services/account_matrix*`
- `schemas/account_matrix*`
- `models/account_matrix*`
- `runtime/task_results/R004/`
- `docs/project_control_center.html`

禁止修改:
- 不调用真实平台 API。
- 不保存真实账号密码或 token。

必须运行的验证:
- 账号矩阵 CRUD smoke test。
- 平台枚举和状态测试。
- 控制中心 R004 更新检查。

完成定义:
- 每个 Workspace 可维护多平台账号矩阵。

输出格式:
- 使用标准输出格式。

---

## R005

Round ID: R005
Round Name: 全网痛点雷达

前置验证:
- 验证 R004 账号矩阵存在且可按 Workspace 查询。

本轮目标:
- 建立痛点收集、分类、聚类、趋势标签和高价值痛点识别的基础系统。

本轮任务:
- 执行任务: 创建痛点数据模型、来源字段、国家/人群/平台标签和趋势分数。
- 测试任务: 使用本地样例数据验证痛点录入、聚类、排序和筛选。
- 协作验收任务: 输出痛点雷达样例表和字段解释。

允许修改:
- `portal_saas/pain_radar/`
- `services/pain_point_engine.py`
- `schemas/pain_point*`
- `models/pain_point*`
- `runtime/task_results/R005/`
- `docs/project_control_center.html`

禁止修改:
- 不抓取真实网站数据。
- 不绕过平台访问限制。

必须运行的验证:
- 痛点样例导入测试。
- 趋势排序 smoke test。
- 控制中心 R005 更新检查。

完成定义:
- 系统可用样例数据展示痛点、趋势和优先级。

输出格式:
- 使用标准输出格式。

---

## R006

Round ID: R006
Round Name: AI 内容工厂 MVP

前置验证:
- 验证 R005 可提供痛点列表和趋势分数。

本轮目标:
- 基于痛点和知识库生成平台适配的图文、短视频脚本、Hook、标题、标签和 SEO 草稿。

本轮任务:
- 执行任务: 建立内容生成服务、模板结构、平台适配字段和人工确认状态。
- 测试任务: 使用样例痛点生成 TikTok、Instagram、Reddit、YouTube、SEO 五类草稿。
- 协作验收任务: 展示每个平台的生成样例和人工确认流程。

允许修改:
- `portal_saas/content_factory/`
- `services/content_engine.py`
- `schemas/content*`
- `models/content*`
- `runtime/task_results/R006/`
- `docs/project_control_center.html`

禁止修改:
- 不自动发布内容。
- 不生成违反平台规则的垃圾营销内容。

必须运行的验证:
- 内容生成 smoke test。
- 平台模板验证。
- 控制中心 R006 更新检查。

完成定义:
- 可从痛点生成多平台内容草稿，并保留人工确认状态。

输出格式:
- 使用标准输出格式。

---

## R007

Round ID: R007
Round Name: AI 回复工作流 MVP

前置验证:
- 验证 R006 内容草稿可生成并保留人工确认状态。

本轮目标:
- 建立自然回复工作流，支持评论/帖子回复草稿、人审、拒绝硬广和回复记录。

本轮任务:
- 执行任务: 创建回复草稿模型、语气约束、风险标签和人审状态。
- 测试任务: 使用样例评论生成自然回复，验证高风险回复被标记。
- 协作验收任务: 展示回复样例、拒绝原因和审核状态。

允许修改:
- `portal_saas/reply_workflow/`
- `services/reply_engine.py`
- `schemas/reply*`
- `models/reply*`
- `runtime/task_results/R007/`
- `docs/project_control_center.html`

禁止修改:
- 不接入真实评论区。
- 不自动发送回复。
- 不生成冒充真人或误导性内容。

必须运行的验证:
- 回复生成 smoke test。
- 风险标记测试。
- 控制中心 R007 更新检查。

完成定义:
- 系统可生成自然回复草稿并进入人审流程。

输出格式:
- 使用标准输出格式。

---

## R008

Round ID: R008
Round Name: AI 学习与复盘系统

前置验证:
- 验证 R007 回复草稿、人审状态和风险标签可用。

本轮目标:
- 建立 AI 学习闭环，记录收藏、忽略、转化、回复效果和内容表现。

本轮任务:
- 执行任务: 创建反馈数据结构、学习事件、内容效果字段和推荐更新机制。
- 测试任务: 使用样例反馈验证内容优先级变化和建议更新。
- 协作验收任务: 展示反馈如何影响下一轮内容建议。

允许修改:
- `portal_saas/learning_loop/`
- `services/learning_engine.py`
- `schemas/learning*`
- `models/learning*`
- `runtime/task_results/R008/`
- `docs/project_control_center.html`

禁止修改:
- 不训练或微调真实模型。
- 不使用真实用户隐私数据。

必须运行的验证:
- 反馈写入测试。
- 推荐排序 smoke test。
- 控制中心 R008 更新检查。

完成定义:
- 系统能从反馈中生成下一步优化建议。

输出格式:
- 使用标准输出格式。

---

## R009

Round ID: R009
Round Name: 报告系统 MVP

前置验证:
- 验证 R008 可产生学习事件和优化建议。

本轮目标:
- 自动生成日报、周报、月报，汇总痛点、内容、回复、增长和优化建议。

本轮任务:
- 执行任务: 创建报告服务、报告模板、报告存储路径和控制中心嵌入格式。
- 测试任务: 使用样例数据生成日报、周报、月报。
- 协作验收任务: 展示报告样例和用户可读摘要。

允许修改:
- `services/report_engine.py`
- `portal_saas/reports/`
- `schemas/report*`
- `models/report*`
- `runtime/task_results/R009/`
- `docs/project_control_center.html`

禁止修改:
- 不伪造真实业务结果。
- 不把测试数据标记为真实增长数据。

必须运行的验证:
- 日报/周报/月报生成测试。
- 报告嵌入控制中心检查。
- 控制中心 R009 更新检查。

完成定义:
- 系统可基于样例数据生成三类报告并在控制中心引用。

输出格式:
- 使用标准输出格式。

---

## R010

Round ID: R010
Round Name: AI Provider 基础桥接

前置验证:
- 验证 R009 报告系统可读取内容、回复和学习数据。

本轮目标:
- 建立 OpenAI、DeepSeek、Claude、客户自有 API Key 和未来本地模型的统一 Provider 抽象。

本轮任务:
- 执行任务: 设计 Provider 配置、调用接口、能力标签、额度字段和错误回退。
- 测试任务: 使用 mock provider 验证多 Provider 路由和错误处理。
- 协作验收任务: 输出 Provider 配置示例和安全边界。

允许修改:
- `services/ai_provider_engine.py`
- `config/ai_providers*`
- `schemas/ai_provider*`
- `models/ai_provider*`
- `runtime/task_results/R010/`
- `docs/project_control_center.html`

禁止修改:
- 不写入真实 API Key。
- 不把密钥提交到 Git。
- 不进行真实付费调用，除非用户明确要求。

必须运行的验证:
- mock provider 路由测试。
- 密钥泄露扫描或配置检查。
- 控制中心 R010 更新检查。

完成定义:
- 后续服务可通过统一接口选择 AI Provider。

输出格式:
- 使用标准输出格式。

---

## R011

Round ID: R011
Round Name: Skill Marketplace 基础结构

前置验证:
- 验证 R010 Provider 抽象存在且不含真实密钥。

本轮目标:
- 建立 Skill Marketplace，支持 SEO、TikTok、Reddit、X Trend、行业包、Premium AI Pack 等能力包。

本轮任务:
- 执行任务: 创建 Skill 数据模型、套餐绑定、启用状态和 Workspace 授权规则。
- 测试任务: 验证不同套餐可启用不同 Skill；验证禁用 Skill 不可被调用。
- 协作验收任务: 展示 Skill 市场样例和套餐差异。

允许修改:
- `portal_saas/skill_marketplace/`
- `services/skill_engine.py`
- `schemas/skill*`
- `models/skill*`
- `runtime/task_results/R011/`
- `docs/project_control_center.html`

禁止修改:
- 不实现真实付费扣费。
- 不绕过套餐权限。

必须运行的验证:
- Skill 启用/禁用测试。
- 套餐权限 smoke test。
- 控制中心 R011 更新检查。

完成定义:
- Workspace 可根据套餐启用 Skill，且权限可验证。

输出格式:
- 使用标准输出格式。

---

## R012

Round ID: R012
Round Name: 通用增长 MVP 阶段验收

前置验证:
- 验证 R001-R011 报告、控制中心状态和 Git 记录齐全。

本轮目标:
- 对 Phase 1 通用增长 MVP 做阶段验收，确认 Workspace、知识库、痛点、内容、回复、学习、报告、Provider、Skill 是否形成闭环。

本轮任务:
- 执行任务: 汇总 Phase 1 功能链路，补齐缺失报告和控制中心进度。
- 测试任务: 运行端到端 smoke test：Workspace -> 知识库 -> 痛点 -> 内容 -> 回复 -> 学习 -> 报告。
- 协作验收任务: 生成阶段验收报告，并通知用户验收后再进入 R013。

允许修改:
- `runtime/task_results/R012/`
- `docs/project_control_center.html`
- Phase 1 相关文档和小范围修复文件

禁止修改:
- 不新增 Phase 2 Japan AI Guide 专属功能。
- 不掩盖失败测试。

必须运行的验证:
- Phase 1 端到端 smoke test。
- R001-R012 报告完整性检查。
- 控制中心阶段完成度检查。

完成定义:
- Phase 1 有明确通过/未通过结论。
- 已通知用户进行阶段验收。

输出格式:
- 使用标准输出格式，并明确写出“等待用户验收”。

---

## R013-R020 Phase 2: Japan AI Guide 推广验证

以下 Round 以 Japan AI Guide 作为第一个真实推广 Workspace。禁止改动无关 AGOS 基础架构，除非为 JAG 样板验证所必需。

### R013

Round ID: R013
Round Name: Japan AI Guide 推广画像

前置验证:
- 用户已验收 R012 或明确允许进入 Phase 2。

本轮目标:
- 为 Japan AI Guide 建立真实推广 Workspace、目标用户画像、国家/平台优先级和知识库基础。

本轮任务:
- 执行任务: 创建 JAG Workspace 样板、用户画像、核心痛点和推广目标。
- 测试任务: 验证 JAG 数据与通用样例 Workspace 隔离。
- 协作验收任务: 展示 JAG Workspace 概览。

允许修改:
- `runtime/task_results/R013/`
- JAG Workspace 样例数据
- `docs/project_control_center.html`

禁止修改:
- 不改 Japan AI Guide 业务应用代码，除非用户另行指定。

必须运行的验证:
- Workspace 隔离测试。
- JAG 样例数据读取测试。

完成定义:
- JAG 成为可追踪的首个真实推广 Workspace。

输出格式:
- 使用标准输出格式。

### R014

Round ID: R014
Round Name: JAG 平台账号矩阵

前置验证:
- 验证 R013 JAG Workspace 存在。

本轮目标:
- 为 JAG 建立 TikTok、Instagram、X、YouTube、Reddit、SEO 的账号矩阵和策略字段。

本轮任务:
- 执行任务: 创建 JAG 平台账号策略、账号状态、内容倾向和风险备注。
- 测试任务: 验证 JAG 多平台账号矩阵可读取和筛选。
- 协作验收任务: 输出 JAG 平台优先级。

允许修改:
- JAG 账号矩阵样例数据
- `runtime/task_results/R014/`
- `docs/project_control_center.html`

禁止修改:
- 不保存真实账号密码、cookie、token。

必须运行的验证:
- 账号矩阵读取测试。
- 平台筛选 smoke test。

完成定义:
- JAG 平台矩阵可用于内容计划。

输出格式:
- 使用标准输出格式。

### R015

Round ID: R015
Round Name: JAG 痛点库

前置验证:
- 验证 R014 平台矩阵可读取。

本轮目标:
- 建立 JAG 游客痛点库，覆盖第一次来日本、交通、语言、餐饮、隐藏景点、避坑等主题。

本轮任务:
- 执行任务: 录入痛点分类、搜索意图、国家/人群标签和高价值标记。
- 测试任务: 验证痛点可按人群、平台和主题筛选。
- 协作验收任务: 展示前 20 个高价值痛点。

允许修改:
- JAG 痛点样例数据
- `runtime/task_results/R015/`
- `docs/project_control_center.html`

禁止修改:
- 不声称样例痛点来自实时抓取。

必须运行的验证:
- 痛点筛选测试。
- 趋势排序 smoke test。

完成定义:
- JAG 痛点库可驱动内容生成。

输出格式:
- 使用标准输出格式。

### R016

Round ID: R016
Round Name: JAG 内容主题池

前置验证:
- 验证 R015 痛点库可输出高价值痛点。

本轮目标:
- 把 JAG 痛点转化为内容主题、标题、脚本、短视频 Hook 和 SEO 关键词。

本轮任务:
- 执行任务: 生成 JAG 内容主题池和平台适配模板。
- 测试任务: 验证每个高价值痛点至少能生成一个内容主题。
- 协作验收任务: 展示 JAG 内容主题样例。

允许修改:
- JAG 内容主题样例数据
- `runtime/task_results/R016/`
- `docs/project_control_center.html`

禁止修改:
- 不自动发布。
- 不生成夸大承诺。

必须运行的验证:
- 痛点到内容主题映射测试。
- 平台模板 smoke test。

完成定义:
- JAG 可从痛点稳定生成内容主题池。

输出格式:
- 使用标准输出格式。

### R017

Round ID: R017
Round Name: JAG 自然回复模板

前置验证:
- 验证 R016 内容主题池可生成。

本轮目标:
- 建立 JAG 在 Reddit、Quora、Instagram、TikTok 评论中的自然回复模板。

本轮任务:
- 执行任务: 创建非硬广回复规则、语气模板、引导方式和风险拒绝规则。
- 测试任务: 用样例评论生成回复并检查硬广风险。
- 协作验收任务: 展示可接受和不可接受回复对比。

允许修改:
- JAG 回复模板样例数据
- `runtime/task_results/R017/`
- `docs/project_control_center.html`

禁止修改:
- 不自动发送回复。
- 不冒充用户真实体验。

必须运行的验证:
- 回复模板测试。
- 风险拒绝测试。

完成定义:
- JAG 可生成自然、安全、可人工审核的回复草稿。

输出格式:
- 使用标准输出格式。

### R018

Round ID: R018
Round Name: JAG 增长报告

前置验证:
- 验证 R017 回复模板和风险规则存在。

本轮目标:
- 生成 JAG 日报、周报和优化建议报告。

本轮任务:
- 执行任务: 汇总 JAG 痛点、内容、回复、平台策略和下一步建议。
- 测试任务: 使用样例数据生成 JAG 报告。
- 协作验收任务: 展示报告摘要和下一步建议。

允许修改:
- `runtime/task_results/R018/`
- JAG 报告样例
- `docs/project_control_center.html`

禁止修改:
- 不把样例结果伪装成真实增长结果。

必须运行的验证:
- JAG 报告生成测试。
- 控制中心报告嵌入检查。

完成定义:
- JAG 报告可用于决策下一步推广。

输出格式:
- 使用标准输出格式。

### R019

Round ID: R019
Round Name: JAG 自动化闭环

前置验证:
- 验证 R018 报告可生成。

本轮目标:
- 验证 JAG 从痛点到内容、回复、反馈、报告的闭环。

本轮任务:
- 执行任务: 串联 JAG Workspace 的完整增长流程。
- 测试任务: 运行 JAG 端到端 smoke test。
- 协作验收任务: 展示闭环链路和失败点。

允许修改:
- JAG 样板数据
- `runtime/task_results/R019/`
- `docs/project_control_center.html`

禁止修改:
- 不接入真实平台自动操作。

必须运行的验证:
- JAG 端到端 smoke test。
- 报告完整性检查。

完成定义:
- JAG 样板能完成增长流程闭环。

输出格式:
- 使用标准输出格式。

### R020

Round ID: R020
Round Name: JAG 推广验证阶段验收

前置验证:
- 验证 R013-R019 报告、测试和控制中心状态完整。

本轮目标:
- 对 Japan AI Guide 作为首个真实样板进行阶段验收。

本轮任务:
- 执行任务: 汇总 JAG Workspace、账号矩阵、痛点、内容、回复、报告和闭环证据。
- 测试任务: 运行 JAG 阶段验收测试。
- 协作验收任务: 通知用户验收，等待确认后再进入 R021。

允许修改:
- `runtime/task_results/R020/`
- `docs/project_control_center.html`
- JAG 样板报告

禁止修改:
- 不进入欧美市场 Phase 3。

必须运行的验证:
- R013-R020 报告完整性检查。
- JAG 端到端验收测试。

完成定义:
- 已生成 JAG 阶段验收报告，并明确等待用户验收。

输出格式:
- 使用标准输出格式，并明确写出“等待用户验收”。

---

## R021-R030 Phase 3: 欧美市场验证

### R021
Round ID: R021
Round Name: 欧美用户画像
前置验证: 验证用户已通过 R020 验收。
本轮目标: 建立欧美用户画像、核心动机、预算、旅行经验和内容偏好。
本轮任务:
- 执行任务: 创建欧美市场画像和 Workspace 扩展字段。
- 测试任务: 验证画像可驱动痛点筛选。
- 协作验收任务: 展示欧美画像摘要。
允许修改: 欧美样板数据、`runtime/task_results/R021/`、`docs/project_control_center.html`
禁止修改: 不覆盖 JAG 样板数据。
必须运行的验证: 画像读取测试、Workspace 隔离测试。
完成定义: 欧美画像可作为内容和痛点输入。
输出格式: 使用标准输出格式。

### R022
Round ID: R022
Round Name: 英文痛点雷达
前置验证: 验证 R021 欧美画像存在。
本轮目标: 建立 Reddit、Quora、SEO 场景下的英文痛点库。
本轮任务:
- 执行任务: 创建英文痛点分类、搜索意图和平台标签。
- 测试任务: 验证按 Reddit/Quora/SEO 筛选。
- 协作验收任务: 展示英文高价值痛点。
允许修改: 英文痛点样例、`runtime/task_results/R022/`、`docs/project_control_center.html`
禁止修改: 不进行实时抓取。
必须运行的验证: 痛点筛选测试、趋势排序 smoke test。
完成定义: 英文痛点可驱动内容工厂。
输出格式: 使用标准输出格式。

### R023
Round ID: R023
Round Name: 英文内容工厂
前置验证: 验证 R022 英文痛点可输出。
本轮目标: 生成英文图文、短视频、长内容和 SEO 草稿。
本轮任务:
- 执行任务: 创建英文内容模板和平台适配规则。
- 测试任务: 每类痛点生成至少一条英文内容。
- 协作验收任务: 展示英文内容样例。
允许修改: 英文内容样例、`runtime/task_results/R023/`、`docs/project_control_center.html`
禁止修改: 不自动发布。
必须运行的验证: 内容生成测试、平台模板测试。
完成定义: 英文内容工厂可用于欧美市场。
输出格式: 使用标准输出格式。

### R024
Round ID: R024
Round Name: Reddit / Quora 回复工作流
前置验证: 验证 R023 英文内容模板存在。
本轮目标: 建立 Reddit 和 Quora 的自然讨论回复工作流。
本轮任务:
- 执行任务: 创建讨论式回复规则、风险规则和人审状态。
- 测试任务: 使用英文样例问题生成回复。
- 协作验收任务: 展示自然回复和硬广拒绝样例。
允许修改: 英文回复模板、`runtime/task_results/R024/`、`docs/project_control_center.html`
禁止修改: 不自动发帖或评论。
必须运行的验证: 回复生成测试、风险拒绝测试。
完成定义: 回复草稿自然且可审核。
输出格式: 使用标准输出格式。

### R025
Round ID: R025
Round Name: Instagram / TikTok 英文短视频
前置验证: 验证 R023 英文内容模板可用。
本轮目标: 建立英文短视频 Hook、脚本、镜头建议和标签。
本轮任务:
- 执行任务: 创建短视频模板和平台差异规则。
- 测试任务: 生成 TikTok 与 Instagram 两类脚本。
- 协作验收任务: 展示短视频样例。
允许修改: 短视频模板、`runtime/task_results/R025/`、`docs/project_control_center.html`
禁止修改: 不自动上传视频。
必须运行的验证: 脚本生成测试、字段完整性测试。
完成定义: 可生成短视频内容包。
输出格式: 使用标准输出格式。

### R026
Round ID: R026
Round Name: YouTube 长内容策略
前置验证: 验证 R023 英文内容工厂可用。
本轮目标: 建立 YouTube 长内容选题、结构、脚本和 SEO 描述。
本轮任务:
- 执行任务: 创建长内容模板和章节结构。
- 测试任务: 生成一个完整长视频大纲。
- 协作验收任务: 展示 YouTube 内容方案。
允许修改: YouTube 模板、`runtime/task_results/R026/`、`docs/project_control_center.html`
禁止修改: 不生成误导性攻略。
必须运行的验证: 大纲生成测试、SEO 字段测试。
完成定义: YouTube 长内容策略可复用。
输出格式: 使用标准输出格式。

### R027
Round ID: R027
Round Name: 英文增长报告
前置验证: 验证 R024-R026 内容和回复数据存在。
本轮目标: 生成英文市场日报、周报和优化建议。
本轮任务:
- 执行任务: 汇总英文痛点、内容、回复和平台建议。
- 测试任务: 生成英文报告样例。
- 协作验收任务: 展示英文市场优化建议。
允许修改: `runtime/task_results/R027/`、英文报告样例、`docs/project_control_center.html`
禁止修改: 不伪造真实数据。
必须运行的验证: 报告生成测试、报告嵌入检查。
完成定义: 英文报告可读且可指导下一步。
输出格式: 使用标准输出格式。

### R028
Round ID: R028
Round Name: 欧美趋势预测
前置验证: 验证 R027 英文报告存在。
本轮目标: 建立欧美趋势信号、季节变化、平台热点和内容机会识别。
本轮任务:
- 执行任务: 创建趋势信号模型和建议输出。
- 测试任务: 使用样例趋势数据生成建议。
- 协作验收任务: 展示趋势到内容建议链路。
允许修改: 趋势样例、`runtime/task_results/R028/`、`docs/project_control_center.html`
禁止修改: 不声称样例为实时市场数据。
必须运行的验证: 趋势建议 smoke test。
完成定义: 趋势可转化为内容建议。
输出格式: 使用标准输出格式。

### R029
Round ID: R029
Round Name: 英文平台适配器
前置验证: 验证 R028 趋势建议可输出。
本轮目标: 把同一痛点适配为 Reddit、TikTok、Instagram、YouTube、SEO 的不同表达。
本轮任务:
- 执行任务: 创建平台适配器和输出格式。
- 测试任务: 同一痛点生成五个平台版本。
- 协作验收任务: 展示平台差异。
允许修改: 平台适配器样例、`runtime/task_results/R029/`、`docs/project_control_center.html`
禁止修改: 不覆盖通用内容模板。
必须运行的验证: 多平台生成测试。
完成定义: 同一痛点可稳定多平台转写。
输出格式: 使用标准输出格式。

### R030
Round ID: R030
Round Name: 欧美市场阶段验收
前置验证: 验证 R021-R029 报告完整。
本轮目标: 验收欧美市场扩展能力。
本轮任务:
- 执行任务: 汇总欧美画像、痛点、内容、回复、趋势、报告。
- 测试任务: 运行欧美市场端到端 smoke test。
- 协作验收任务: 通知用户验收，等待确认后再进入 R031。
允许修改: `runtime/task_results/R030/`、`docs/project_control_center.html`
禁止修改: 不进入 Phase 4。
必须运行的验证: R021-R030 完整性检查、端到端验收测试。
完成定义: 已生成欧美阶段验收报告并等待用户验收。
输出格式: 使用标准输出格式，并明确写出“等待用户验收”。

---

## R031-R040 Phase 4: 韩台市场验证

### R031
Round ID: R031
Round Name: 韩国用户画像
前置验证: 验证用户已通过 R030 验收。
本轮目标: 建立韩国游客画像、语气偏好和平台偏好。
本轮任务:
- 执行任务: 创建韩国市场画像。
- 测试任务: 验证画像可驱动韩语内容。
- 协作验收任务: 展示韩国画像摘要。
允许修改: 韩国样板数据、`runtime/task_results/R031/`、`docs/project_control_center.html`
禁止修改: 不覆盖其他市场数据。
必须运行的验证: 画像读取测试、隔离测试。
完成定义: 韩国画像可用于后续痛点和内容。
输出格式: 使用标准输出格式。

### R032
Round ID: R032
Round Name: 韩语内容模板
前置验证: 验证 R031 韩国画像存在。
本轮目标: 建立韩语短视频、图文和平台语气模板。
本轮任务:
- 执行任务: 创建韩语内容模板。
- 测试任务: 生成韩语内容样例。
- 协作验收任务: 展示模板差异。
允许修改: 韩语模板、`runtime/task_results/R032/`、`docs/project_control_center.html`
禁止修改: 不进行低质量机器翻译替代本地化。
必须运行的验证: 模板生成测试。
完成定义: 韩语模板可复用。
输出格式: 使用标准输出格式。

### R033
Round ID: R033
Round Name: 韩国视觉内容策略
前置验证: 验证 R032 韩语模板可用。
本轮目标: 建立韩国市场视觉内容策略、镜头偏好和内容风格。
本轮任务:
- 执行任务: 创建视觉内容策略字段。
- 测试任务: 生成视觉内容建议。
- 协作验收任务: 展示视觉策略样例。
允许修改: 视觉策略样例、`runtime/task_results/R033/`、`docs/project_control_center.html`
禁止修改: 不生成真实图片资产，除非用户要求。
必须运行的验证: 策略生成 smoke test。
完成定义: 视觉策略可指导内容创作。
输出格式: 使用标准输出格式。

### R034
Round ID: R034
Round Name: 台湾用户画像
前置验证: 验证 R033 韩国视觉策略已完成。
本轮目标: 建立台湾繁中用户画像和旅行偏好。
本轮任务:
- 执行任务: 创建台湾市场画像。
- 测试任务: 验证画像可驱动繁中内容。
- 协作验收任务: 展示台湾画像摘要。
允许修改: 台湾样板数据、`runtime/task_results/R034/`、`docs/project_control_center.html`
禁止修改: 不覆盖韩国样板。
必须运行的验证: 画像读取和隔离测试。
完成定义: 台湾画像可用于繁中内容。
输出格式: 使用标准输出格式。

### R035
Round ID: R035
Round Name: 繁中内容模板
前置验证: 验证 R034 台湾画像存在。
本轮目标: 建立繁中深度攻略、短视频和社媒内容模板。
本轮任务:
- 执行任务: 创建繁中内容模板。
- 测试任务: 生成繁中内容样例。
- 协作验收任务: 展示繁中模板。
允许修改: 繁中模板、`runtime/task_results/R035/`、`docs/project_control_center.html`
禁止修改: 不混用简体语气。
必须运行的验证: 模板生成测试。
完成定义: 繁中模板可复用。
输出格式: 使用标准输出格式。

### R036
Round ID: R036
Round Name: 韩台痛点库
前置验证: 验证 R032 和 R035 模板存在。
本轮目标: 建立韩语和繁中痛点库。
本轮任务:
- 执行任务: 创建韩台痛点分类和市场标签。
- 测试任务: 验证按地区和语言筛选。
- 协作验收任务: 展示韩台痛点对比。
允许修改: 韩台痛点样例、`runtime/task_results/R036/`、`docs/project_control_center.html`
禁止修改: 不合并成不可区分的单一市场。
必须运行的验证: 地区筛选测试。
完成定义: 韩台痛点可分别驱动内容。
输出格式: 使用标准输出格式。

### R037
Round ID: R037
Round Name: 韩台回复工作流
前置验证: 验证 R036 韩台痛点库存在。
本轮目标: 建立韩语和繁中自然回复规则。
本轮任务:
- 执行任务: 创建韩台回复模板和风险规则。
- 测试任务: 生成韩语和繁中回复样例。
- 协作验收任务: 展示语言差异。
允许修改: 韩台回复模板、`runtime/task_results/R037/`、`docs/project_control_center.html`
禁止修改: 不自动发送回复。
必须运行的验证: 回复生成测试、风险测试。
完成定义: 韩台回复可审核、可复用。
输出格式: 使用标准输出格式。

### R038
Round ID: R038
Round Name: 季节内容系统
前置验证: 验证 R037 回复工作流可用。
本轮目标: 建立樱花、红叶、温泉、祭典等季节内容系统。
本轮任务:
- 执行任务: 创建季节内容日历和内容模板。
- 测试任务: 根据季节生成内容建议。
- 协作验收任务: 展示季节内容样例。
允许修改: 季节内容样例、`runtime/task_results/R038/`、`docs/project_control_center.html`
禁止修改: 不假定实时天气或活动信息。
必须运行的验证: 季节匹配 smoke test。
完成定义: 季节内容可被多市场复用。
输出格式: 使用标准输出格式。

### R039
Round ID: R039
Round Name: 韩台数据报告
前置验证: 验证 R031-R038 数据链路存在。
本轮目标: 生成韩台市场报告。
本轮任务:
- 执行任务: 汇总韩台画像、痛点、内容、回复和季节建议。
- 测试任务: 生成韩台报告样例。
- 协作验收任务: 展示报告和建议。
允许修改: `runtime/task_results/R039/`、`docs/project_control_center.html`
禁止修改: 不伪造真实增长数据。
必须运行的验证: 报告生成测试。
完成定义: 韩台报告可指导下一步内容。
输出格式: 使用标准输出格式。

### R040
Round ID: R040
Round Name: 韩台市场阶段验收
前置验证: 验证 R031-R039 报告完整。
本轮目标: 验收韩台市场能力。
本轮任务:
- 执行任务: 汇总韩台画像、模板、痛点、回复、季节内容和报告。
- 测试任务: 运行韩台端到端 smoke test。
- 协作验收任务: 通知用户验收，等待确认后再进入 R041。
允许修改: `runtime/task_results/R040/`、`docs/project_control_center.html`
禁止修改: 不进入 Phase 5。
必须运行的验证: R031-R040 完整性检查、端到端测试。
完成定义: 已生成韩台阶段验收报告并等待用户验收。
输出格式: 使用标准输出格式，并明确写出“等待用户验收”。

---

## R041-R048 Phase 5: 东南亚市场扩展

### R041
Round ID: R041
Round Name: 东南亚国家优先级
前置验证: 验证用户已通过 R040 验收。
本轮目标: 确定新加坡、泰国、马来西亚、印尼等市场优先级。
本轮任务:
- 执行任务: 创建国家优先级、语言、预算和平台字段。
- 测试任务: 验证按国家输出策略。
- 协作验收任务: 展示市场优先级。
允许修改: 东南亚样板数据、`runtime/task_results/R041/`、`docs/project_control_center.html`
禁止修改: 不覆盖已有市场。
必须运行的验证: 国家筛选测试。
完成定义: 东南亚市场优先级明确。
输出格式: 使用标准输出格式。

### R042
Round ID: R042
Round Name: 东南亚痛点标签
前置验证: 验证 R041 国家优先级存在。
本轮目标: 建立预算、家庭、清真、购物、季节、交通等标签。
本轮任务:
- 执行任务: 创建标签体系和痛点映射。
- 测试任务: 验证标签筛选和组合。
- 协作验收任务: 展示标签矩阵。
允许修改: 标签样例、`runtime/task_results/R042/`、`docs/project_control_center.html`
禁止修改: 不把所有国家痛点混为一类。
必须运行的验证: 标签筛选测试。
完成定义: 标签可驱动内容生成。
输出格式: 使用标准输出格式。

### R043
Round ID: R043
Round Name: 新加坡高端客模型
前置验证: 验证 R042 标签体系可用。
本轮目标: 建立新加坡高端家庭、服务型、亲子和品质内容模型。
本轮任务:
- 执行任务: 创建新加坡高端客画像和内容策略。
- 测试任务: 生成高端客内容建议。
- 协作验收任务: 展示模型样例。
允许修改: 新加坡样例、`runtime/task_results/R043/`、`docs/project_control_center.html`
禁止修改: 不泛化到所有东南亚国家。
必须运行的验证: 画像到内容测试。
完成定义: 新加坡高端客模型可用于内容。
输出格式: 使用标准输出格式。

### R044
Round ID: R044
Round Name: 泰国年轻客内容模板
前置验证: 验证 R042 标签体系存在。
本轮目标: 建立泰国年轻客短视频、购物、美食和社交内容模板。
本轮任务:
- 执行任务: 创建泰语/英文混合内容模板。
- 测试任务: 生成泰国年轻客内容样例。
- 协作验收任务: 展示内容样例。
允许修改: 泰国模板、`runtime/task_results/R044/`、`docs/project_control_center.html`
禁止修改: 不使用低质量直译。
必须运行的验证: 模板生成测试。
完成定义: 泰国年轻客模板可复用。
输出格式: 使用标准输出格式。

### R045
Round ID: R045
Round Name: 马来 / 印尼家庭模型
前置验证: 验证 R042 标签体系存在。
本轮目标: 建立家庭便利、清真餐饮、多人数出行和预算控制模型。
本轮任务:
- 执行任务: 创建马来/印尼家庭画像和内容策略。
- 测试任务: 生成家庭出行内容样例。
- 协作验收任务: 展示模型差异。
允许修改: 马来/印尼样例、`runtime/task_results/R045/`、`docs/project_control_center.html`
禁止修改: 不忽视清真和家庭需求。
必须运行的验证: 画像到内容测试。
完成定义: 马来/印尼家庭模型可用于内容。
输出格式: 使用标准输出格式。

### R046
Round ID: R046
Round Name: 东南亚多语言内容工厂
前置验证: 验证 R043-R045 市场模型存在。
本轮目标: 建立英语、泰语、印尼语、马来语内容模板。
本轮任务:
- 执行任务: 创建多语言模板和字段约束。
- 测试任务: 同一痛点生成多语言版本。
- 协作验收任务: 展示多语言输出对比。
允许修改: 多语言模板、`runtime/task_results/R046/`、`docs/project_control_center.html`
禁止修改: 不把机器翻译当作最终本地化。
必须运行的验证: 多语言生成测试。
完成定义: 多语言内容可稳定输出。
输出格式: 使用标准输出格式。

### R047
Round ID: R047
Round Name: 东南亚报告系统
前置验证: 验证 R046 多语言内容可输出。
本轮目标: 生成东南亚国家、平台、内容维度报告。
本轮任务:
- 执行任务: 汇总东南亚痛点、内容和建议。
- 测试任务: 生成报告样例。
- 协作验收任务: 展示国家维度建议。
允许修改: `runtime/task_results/R047/`、`docs/project_control_center.html`
禁止修改: 不伪造真实增长数据。
必须运行的验证: 报告生成测试。
完成定义: 东南亚报告可指导扩展。
输出格式: 使用标准输出格式。

### R048
Round ID: R048
Round Name: 东南亚市场阶段验收
前置验证: 验证 R041-R047 报告完整。
本轮目标: 验收东南亚市场扩展能力。
本轮任务:
- 执行任务: 汇总国家优先级、标签、市场模型、多语言内容和报告。
- 测试任务: 运行东南亚端到端 smoke test。
- 协作验收任务: 通知用户验收，等待确认后再进入 R049。
允许修改: `runtime/task_results/R048/`、`docs/project_control_center.html`
禁止修改: 不进入 SaaS 商业化 Phase 6。
必须运行的验证: R041-R048 完整性检查、端到端测试。
完成定义: 已生成东南亚阶段验收报告并等待用户验收。
输出格式: 使用标准输出格式，并明确写出“等待用户验收”。

---

## R049-R054 Phase 6: SaaS 商业化闭环

### R049
Round ID: R049
Round Name: SaaS 客户管理中心
前置验证: 验证用户已通过 R048 验收。
本轮目标: 建立 SaaS 客户列表、Workspace 数量、套餐、AI 活跃度和异常状态。
本轮任务:
- 执行任务: 创建客户管理页面和数据结构。
- 测试任务: 验证客户与 Workspace 关联。
- 协作验收任务: 展示客户管理样例。
允许修改: `portal_saas/customer_management/`、`runtime/task_results/R049/`、`docs/project_control_center.html`
禁止修改: 不实现真实支付。
必须运行的验证: 客户 CRUD smoke test、Workspace 关联测试。
完成定义: SaaS 管理端可查看客户与 Workspace。
输出格式: 使用标准输出格式。

### R050
Round ID: R050
Round Name: 客户分析看板
前置验证: 验证 R049 客户管理可用。
本轮目标: 建立客户维度的内容、回复、增长、建议和风险看板。
本轮任务:
- 执行任务: 创建客户分析页面和指标聚合。
- 测试任务: 使用样例客户生成看板数据。
- 协作验收任务: 展示客户看板。
允许修改: `portal_saas/customer_dashboard/`、`runtime/task_results/R050/`、`docs/project_control_center.html`
禁止修改: 不展示其他客户数据。
必须运行的验证: 客户隔离测试、看板 smoke test。
完成定义: 客户可被独立分析。
输出格式: 使用标准输出格式。

### R051
Round ID: R051
Round Name: 订阅与账单中心
前置验证: 验证 R050 客户看板可读取客户状态。
本轮目标: 建立月付、季付、年付、企业版、账单历史和续费状态。
本轮任务:
- 执行任务: 创建订阅引擎和账单数据结构。
- 测试任务: 验证套餐状态和账单历史。
- 协作验收任务: 展示套餐和账单样例。
允许修改: `services/subscription_engine.py`、`portal_saas/billing/`、`runtime/task_results/R051/`、`docs/project_control_center.html`
禁止修改: 不接入真实支付网关。
必须运行的验证: 套餐状态测试、账单 smoke test。
完成定义: 客户订阅状态可追踪。
输出格式: 使用标准输出格式。

### R052
Round ID: R052
Round Name: 权限与角色系统
前置验证: 验证 R051 订阅状态可读取。
本轮目标: 建立管理员、运营、财务、审核、只读等角色权限。
本轮任务:
- 执行任务: 创建权限引擎、角色定义和操作日志字段。
- 测试任务: 验证不同角色访问不同能力。
- 协作验收任务: 展示权限矩阵。
允许修改: `services/permission_engine.py`、`runtime/task_results/R052/`、`docs/project_control_center.html`
禁止修改: 不绕过角色权限。
必须运行的验证: 权限矩阵测试、只读角色测试。
完成定义: 角色权限可被验证。
输出格式: 使用标准输出格式。

### R053
Round ID: R053
Round Name: AI 安全与风控
前置验证: 验证 R052 权限系统可用。
本轮目标: 建立内容审核、频率限制、品牌保护、敏感操作和异常提示。
本轮任务:
- 执行任务: 创建风控引擎和风险标签。
- 测试任务: 验证高风险内容被拦截或标记。
- 协作验收任务: 展示风险案例。
允许修改: `services/risk_control_engine.py`、`runtime/task_results/R053/`、`docs/project_control_center.html`
禁止修改: 不允许自动 spam、不允许绕过审核。
必须运行的验证: 风险拦截测试、频率限制 smoke test。
完成定义: 高风险行为可被识别和阻断。
输出格式: 使用标准输出格式。

### R054
Round ID: R054
Round Name: SaaS 商业化阶段验收
前置验证: 验证 R049-R053 报告完整。
本轮目标: 验收客户管理、客户看板、订阅、权限和风控。
本轮任务:
- 执行任务: 汇总 SaaS 商业化能力。
- 测试任务: 运行 SaaS 管理端端到端 smoke test。
- 协作验收任务: 通知用户验收，等待确认后再进入 R055。
允许修改: `runtime/task_results/R054/`、`docs/project_control_center.html`
禁止修改: 不进入 Phase 7。
必须运行的验证: R049-R054 完整性检查、SaaS 端到端测试。
完成定义: 已生成 SaaS 阶段验收报告并等待用户验收。
输出格式: 使用标准输出格式，并明确写出“等待用户验收”。

---

## R055-R060 Phase 7: AI 自动化中枢与最终验收

### R055
Round ID: R055
Round Name: AI 趋势反馈引擎
前置验证: 验证用户已通过 R054 验收。
本轮目标: 建立趋势信号、需求变化、平台变化和内容机会反馈引擎。
本轮任务:
- 执行任务: 创建趋势反馈模型和建议输出。
- 测试任务: 使用样例趋势生成反馈。
- 协作验收任务: 展示趋势反馈链路。
允许修改: `services/trend_feedback_engine.py`、`runtime/task_results/R055/`、`docs/project_control_center.html`
禁止修改: 不声称样例为实时趋势。
必须运行的验证: 趋势反馈 smoke test。
完成定义: 趋势可反馈到内容计划。
输出格式: 使用标准输出格式。

### R056
Round ID: R056
Round Name: AI 内容策略智能体
前置验证: 验证 R055 趋势反馈可输出。
本轮目标: 自动建议每日内容计划、优先级和多市场内容安排。
本轮任务:
- 执行任务: 创建内容策略智能体和计划输出。
- 测试任务: 根据样例趋势生成每日计划。
- 协作验收任务: 展示内容计划。
允许修改: `services/content_strategy_agent.py`、`runtime/task_results/R056/`、`docs/project_control_center.html`
禁止修改: 不自动发布。
必须运行的验证: 内容计划生成测试。
完成定义: AI 可生成可审阅的内容策略。
输出格式: 使用标准输出格式。

### R057
Round ID: R057
Round Name: AI 回复质量风控
前置验证: 验证 R056 内容策略可用。
本轮目标: 检查回复是否机械、误导、硬广、过度承诺或违反品牌语气。
本轮任务:
- 执行任务: 创建回复质量检查器。
- 测试任务: 对可接受和不可接受样例进行判断。
- 协作验收任务: 展示质量评分和拒绝原因。
允许修改: `services/reply_quality_engine.py`、`runtime/task_results/R057/`、`docs/project_control_center.html`
禁止修改: 不自动发送未经审核回复。
必须运行的验证: 质量判断测试、拒绝测试。
完成定义: 回复质量可被自动评估。
输出格式: 使用标准输出格式。

### R058
Round ID: R058
Round Name: AI 增长复盘引擎
前置验证: 验证 R057 回复质量风控可用。
本轮目标: 自动复盘内容、回复、线索、转化和被忽略内容。
本轮任务:
- 执行任务: 创建增长复盘引擎和优化建议。
- 测试任务: 使用样例表现数据生成复盘。
- 协作验收任务: 展示复盘报告。
允许修改: `services/growth_review_engine.py`、`runtime/task_results/R058/`、`docs/project_control_center.html`
禁止修改: 不伪造真实转化。
必须运行的验证: 复盘生成测试。
完成定义: 系统可输出下一步增长优化建议。
输出格式: 使用标准输出格式。

### R059
Round ID: R059
Round Name: 多市场运营总控台
前置验证: 验证 R058 增长复盘可输出。
本轮目标: 统一查看多客户、多产品、多市场、多平台的运营状态。
本轮任务:
- 执行任务: 创建总控台数据结构和页面导航。
- 测试任务: 使用多市场样例数据验证聚合。
- 协作验收任务: 展示总控台视图。
允许修改: `portal_saas/operation_control/`、`runtime/task_results/R059/`、`docs/project_control_center.html`
禁止修改: 不混淆不同客户数据。
必须运行的验证: 多客户隔离测试、多市场聚合测试。
完成定义: 总控台可查看整体运营状态。
输出格式: 使用标准输出格式。

### R060
Round ID: R060
Round Name: AI Growth OS SaaS 最终验收
前置验证: 验证 R001-R059 报告、测试、控制中心和 Git 记录完整。
本轮目标: 对 AGOS 全项目做最终验收，确认形成长期自动增长基础设施。
本轮任务:
- 执行任务: 汇总全项目模块、Round、报告、风险、未完成项和后续路线。
- 测试任务: 运行全链路 smoke test 和报告完整性检查。
- 协作验收任务: 通知用户进行最终验收，并输出最终验收包。
允许修改: `runtime/task_results/R060/`、`docs/project_control_center.html`、最终验收文档
禁止修改: 不隐藏失败项，不把未完成项标记为完成。
必须运行的验证: R001-R060 完整性检查、全链路 smoke test、Git 状态检查。
完成定义: 最终验收报告生成，控制中心显示真实完成度，并等待用户最终验收。
输出格式: 使用标准输出格式，并明确写出“等待用户最终验收”。
