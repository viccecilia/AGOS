
    const state = JSON.parse(document.getElementById("project-state").textContent);
    const runtimeApiBase = "http://127.0.0.1:8766";
    const runtimeApiState = {
      connected: false,
      last_api_ping: "never",
      last_runtime_action: "none",
      last_error: "Runtime API 未连接"
    };

    const statusLabel = {
      planned: "未开始",
      in_progress: "进行中",
      done: "已完成",
      blocked: "阻塞",
      not_initialized: "Git 未初始化",
      local_initialized: "本地 Git 已初始化",
      clean: "已上传 Git",
      dirty: "本地有改动"
    };
    const statusClass = {
      planned: "b-violet",
      in_progress: "b-amber",
      done: "b-green",
      blocked: "b-red",
      not_initialized: "b-amber",
      local_initialized: "b-cyan",
      clean: "b-green",
      dirty: "b-amber"
    };

    function el(id) { return document.getElementById(id); }
    function esc(value) {
      return String(value ?? "").replace(/[&<>"']/g, ch => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[ch]));
    }
    function badge(status) {
      return `<span class="badge ${statusClass[status] || "b-blue"}">${statusLabel[status] || status}</span>`;
    }
    function copyText(text) {
      navigator.clipboard?.writeText(text).catch(() => {});
    }
    async function saveSnapshot(version) {
      const content = version.snapshot || `Version: ${version.label}\nGit: ${version.gitRef}\nLocation: ${version.location}\n`;
      const filename = `${version.id}.txt`;
      if (window.showSaveFilePicker) {
        const handle = await window.showSaveFilePicker({
          suggestedName: filename,
          types: [{ description: "Text snapshot", accept: { "text/plain": [".txt"] } }]
        });
        const writable = await handle.createWritable();
        await writable.write(content);
        await writable.close();
        return;
      }
      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }

    function renderOverview() {
      el("project-title").textContent = `${state.project.name} 控制中心`;
      el("project-summary").textContent = state.project.activeFocus;
      el("current-phase").textContent = state.project.currentPhase;
      el("next-round").textContent = state.project.nextRound;
      el("project-version-badge").textContent = `Control Center v${state.project.controlCenterVersion}`;
      el("current-round-badge").textContent = `当前 ${state.project.currentRound}`;
      el("metric-progress").textContent = `${state.project.overallProgress}%`;
      el("metric-rounds").textContent = state.metrics.roundsPlanned;
      el("metric-active").textContent = state.metrics.roundsInProgress;
      el("metric-reports").textContent = state.metrics.reportsEmbedded;
      el("nav-version").textContent = `v${state.project.controlCenterVersion}`;
      el("nav-progress").textContent = `${state.project.overallProgress}%`;
      el("nav-reports").textContent = state.metrics.reportsEmbedded;
      el("nav-git").textContent = state.git.status === "not_initialized" ? "pending" : state.git.branch || state.git.latestCommit;
    }


    function renderPhaseBlueprint() {
      const bp = state.phaseBlueprint || { phases: [], roundTemplate: { sections: [], outputFormat: [] } };
      el('blueprint-final-goal').innerHTML = '<strong>Final goal:</strong> ' + esc(bp.finalGoal || 'AI Growth Operating System');
      el('phase-blueprint-grid').innerHTML = (bp.phases || []).map(phase => `
        <article class="card">
          <div class="topline"><h3>${esc(phase.id)}</h3><span class="badge b-blue">${esc(phase.rounds)}</span></div>
          <p><strong>${esc(phase.name)}</strong></p>
          <p>${esc(phase.goal)}</p>
          <p><code>${esc(phase.file)}</code></p>
          <ul>
            ${(phase.acceptance || []).map(item => `<li>${esc(item)}</li>`).join('')}
          </ul>
          <p><strong>Next:</strong> ${esc(phase.next)}</p>
        </article>
      `).join('');
      const tpl = bp.roundTemplate || { sections: [], outputFormat: [] };
      el('round-template-summary').innerHTML = `
        <p><code>${esc(tpl.file || '')}</code></p>
        <div class="grid two">
          <div><h3>Required Sections</h3><ul>${(tpl.sections || []).map(item => `<li>${esc(item)}</li>`).join('')}</ul></div>
          <div><h3>Output Format</h3><ul>${(tpl.outputFormat || []).map(item => `<li>${esc(item)}</li>`).join('')}</ul></div>
        </div>
      `;
    }

    function renderRealGrowth() {
      const rg = state.realGrowthVerification || {};
      const status = rg.status || 'pending';
      el('real-growth-status').className = `badge ${status === 'passed' ? 'b-green' : 'b-amber'}`;
      el('real-growth-status').textContent = status;
      const metrics = [
        ['Today new questions', rg.todayNewQuestions ?? 0],
        ['Pending replies', rg.pendingReplyQuestions ?? 0],
        ['Replied questions', rg.repliedQuestions ?? 0],
        ['High-engagement answers', rg.highEngagementAnswers ?? 0],
        ['Ignored answers', rg.ignoredAnswers ?? 0],
        ['Best answer branches', rg.bestAnswerBranches ?? 0],
        ['Workspace isolation', rg.workspaceIsolation || 'pending'],
        ['Human review default', rg.humanReviewDefault ? 'yes' : 'pending']
      ];
      el('real-growth-metrics').innerHTML = metrics.map(([label, value]) => `
        <div class="card"><h3>${esc(label)}</h3><p><strong>${esc(value)}</strong></p></div>
      `).join('');
      el('real-growth-checklist').innerHTML = (rg.acceptanceItems || []).map(item => `
        <div class="card" style="margin-bottom:10px">
          <div class="topline"><span class="badge ${item.passed ? 'b-green' : 'b-amber'}">${item.passed ? 'passed' : 'pending'}</span></div>
          <p>${esc(item.label)}</p>
        </div>
      `).join('');
    }




    function renderSeasonalDemandCalendar() {
      const seasonal = state.seasonalDemandCalendar || {};
      const seasons = seasonal.seasonalCalendar || [];
      const summary = seasonal.summary || {};
      const keywords = seasonal.keywordSample || [];
      const source = seasonal.realApiConnected ? 'real API' : (seasonal.dataSourceLabel || seasonal.dataSource || 'local sample');
      el('seasonal-data-source').textContent = source;
      el('seasonal-data-source').className = 'badge ' + (seasonal.realApiConnected ? 'b-green' : 'b-amber');
      const metrics = [
        ['Current focus', seasonal.currentFocusSeason || summary.current_focus_season || 'pending'],
        ['Seasons monitored', summary.seasons ?? seasons.length],
        ['Keywords', summary.keywords ?? keywords.length],
        ['Write API', seasonal.writeOperationsEnabled ? 'enabled' : 'blocked']
      ];
      el('seasonal-demand-metrics').innerHTML = metrics.map(([label, value]) =>
        '<div class="card"><h3>' + esc(label) + '</h3><p><strong>' + esc(value) + '</strong></p></div>'
      ).join('');
      const upcoming = new Set(seasonal.upcomingPeakSeasons || []);
      const peakSeasons = seasons.filter(item => upcoming.has(item.season_name)).slice(0, 6);
      el('seasonal-peak-list').innerHTML = peakSeasons.map(item =>
        '<div class="feed-item"><time>' + esc(item.time_window) + '</time><div class="feed-main"><strong>' + esc(item.season_name) + '</strong><span>Markets: ' + esc((item.target_markets || []).join(' / ')) + '</span><span>Locations: ' + esc((item.likely_locations || []).slice(0, 5).join(' / ')) + '</span><span>Pain: ' + esc((item.mobility_pain_points || []).join(' / ')) + '</span></div><span class="badge b-blue">' + esc(item.monitoring_frequency) + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>No seasonal peaks configured</strong><span>Add records through manual, CSV, JSON, or future API import.</span></div><span class="badge b-amber">pending</span></div>';
      el('seasonal-keyword-list').innerHTML = keywords.map(item =>
        '<div class="feed-item"><time>' + esc(item.season_id || '') + '</time><div class="feed-main"><strong>' + esc(item.keyword || '') + '</strong><span>' + esc((item.monitoring_channels || []).join(' / ')) + '</span><span>Markets: ' + esc((item.target_markets || []).join(' / ')) + '</span></div><span class="badge ' + (item.real_google_trends_connected ? 'b-green' : 'b-amber') + '">' + esc(item.real_google_trends_connected ? 'real API' : 'sample/import') + '</span></div>'
      ).join('');
      el('seasonal-demand-table').innerHTML = seasons.map(item =>
        '<tr><td><strong>' + esc(item.season_name) + '</strong><br><code>' + esc(item.season_id) + '</code></td><td>' + esc(item.time_window) + '</td><td>' + esc((item.target_markets || []).join(' / ')) + '</td><td><strong>' + esc((item.predicted_demand_types || []).join(' / ')) + '</strong><br>' + esc((item.mobility_pain_points || []).join(' / ')) + '<br><span class="muted">' + esc(item.risk_notes || '') + '</span></td><td>' + esc(item.data_origin || seasonal.dataSource || 'local_sample') + '<br>real_api_connected=' + esc(item.real_api_connected || false) + '</td></tr>'
      ).join('');
    }

    function runtimeBadgeClass(status) {
      if (status === 'RUNNING') return 'rt-running';
      if (status === 'PAUSED') return 'rt-paused';
      if (status === 'STOPPED') return 'rt-stopped';
      return 'b-amber';
    }

    function mergeRuntimeBridgeData(runtimeData) {
      if (!runtimeData || typeof runtimeData !== 'object') return;
      state.warRoomGrowth = {
        ...(state.warRoomGrowth || {}),
        ...runtimeData,
        systemControl: {
          ...((state.warRoomGrowth || {}).systemControl || {}),
          ...(runtimeData.systemControl || {})
        }
      };
    }

    function mergeRuntimeApiPayload(payload) {
      if (!payload || typeof payload !== 'object') return;
      mergeRuntimeBridgeData(payload.ui_state || payload);
      runtimeApiState.connected = true;
      runtimeApiState.last_api_ping = new Date().toLocaleTimeString();
      runtimeApiState.last_error = "";
      if (payload.status && state.warRoomGrowth) {
        state.warRoomGrowth.runtimeStatus = String(payload.status).toUpperCase();
      }
    }

    function renderRuntimeApiBanner() {
      const banner = el('runtime-api-banner');
      if (!banner) return;
      const status = runtimeApiState.connected ? "connected" : "disconnected";
      banner.innerHTML =
        '<strong>Runtime API: ' + esc(status) + '</strong>' +
        ' · last_api_ping: ' + esc(runtimeApiState.last_api_ping) +
        ' · last_runtime_action: ' + esc(runtimeApiState.last_runtime_action) +
        (runtimeApiState.last_error ? ' · last_error: ' + esc(runtimeApiState.last_error) : '');
    }

    async function fetchRuntimeApiStatus() {
      if (location.protocol !== "http:" && location.protocol !== "https:") return false;
      try {
        const response = await fetch(`${runtimeApiBase}/api/runtime/status?runtime_api=${Date.now()}`, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        mergeRuntimeApiPayload(payload);
        renderRuntimeApiBanner();
        renderWarRoomGrowth();
        return true;
      } catch (error) {
        runtimeApiState.connected = false;
        runtimeApiState.last_error = "Runtime API 未连接。请运行：python services/runtime_api_server.py";
        renderRuntimeApiBanner();
        return false;
      }
    }

    async function callRuntimeApi(action) {
      runtimeApiState.last_runtime_action = action;
      try {
        const response = await fetch(`${runtimeApiBase}/api/runtime/${action}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}"
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        mergeRuntimeApiPayload(payload);
        renderRuntimeApiBanner();
        renderWarRoomGrowth();
      } catch (error) {
        runtimeApiState.connected = false;
        runtimeApiState.last_error = "Runtime API 未连接。请运行：python services/runtime_api_server.py";
        renderRuntimeApiBanner();
        await fetchRuntimeBridgeState();
      }
    }

    async function callRuntimeReview(reviewId, decision) {
      const rejectReason = el(`reject_reason_${reviewId}`)?.value || "";
      const humanModifiedVersion = el(`modify_text_${reviewId}`)?.value || "";
      if (decision === "reject" && !rejectReason.trim()) {
        runtimeApiState.last_error = "Reject requires reject_reason";
        renderRuntimeApiBanner();
        return;
      }
      runtimeApiState.last_runtime_action = `review:${decision}`;
      const payload = {
        review_id: reviewId,
        decision,
        reject_reason: rejectReason,
        human_modified_version: humanModifiedVersion
      };
      try {
        const response = await fetch(`${runtimeApiBase}/api/runtime/review`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        mergeRuntimeApiPayload(await response.json());
        renderRuntimeApiBanner();
        renderWarRoomGrowth();
      } catch (error) {
        runtimeApiState.connected = false;
        runtimeApiState.last_error = "Review API failed";
        renderRuntimeApiBanner();
      }
    }

    async function submitRuntimeCorrection() {
      const payload = {
        workspace: el("runtime-correction-workspace")?.value || "JAG-LAB",
        industry_pack: el("runtime-correction-industry")?.value || "Travel Pack / Lab",
        affected_runtime_stage: el("runtime-correction-stage")?.value || "Human Review",
        correction_type: el("runtime-correction-type")?.value || "错误机会判断",
        target_id: `manual_${Date.now()}`,
        decision: "reject",
        correction_reason: el("runtime-correction-reason")?.value || "Human correction submitted from War Room."
      };
      runtimeApiState.last_runtime_action = "correction:submit";
      try {
        const response = await fetch(`${runtimeApiBase}/api/runtime/correction`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        mergeRuntimeApiPayload(await response.json());
        renderRuntimeApiBanner();
        renderWarRoomGrowth();
      } catch (error) {
        runtimeApiState.connected = false;
        runtimeApiState.last_error = "Correction API failed";
        renderRuntimeApiBanner();
      }
    }

    async function submitPersonalityTraining(decision) {
      const payload = {
        decision,
        workspace: "JAG-LAB",
        platform: el("personality-train-platform")?.value || "reddit",
        market: el("personality-train-market")?.value || "Japan",
        tone: el("personality-train-tone")?.value || "trusted_guide",
        style: ["真实", "可信", "专业", "像导游", "不营销"],
        reason: el("personality-train-reason")?.value || "Human personality training from War Room.",
        modified_personality: {
          workspace: "JAG-LAB",
          platform: el("personality-train-platform")?.value || "reddit",
          market: el("personality-train-market")?.value || "Japan",
          tone: el("personality-train-tone")?.value || "trusted_guide",
          style: ["真实", "可信", "专业", "克制", "不营销"],
          reason: "Human modified personality from War Room."
        }
      };
      runtimeApiState.last_runtime_action = `personality:${decision}`;
      try {
        const response = await fetch(`${runtimeApiBase}/api/runtime/personality`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        mergeRuntimeApiPayload(await response.json());
        renderRuntimeApiBanner();
        renderWarRoomGrowth();
      } catch (error) {
        runtimeApiState.connected = false;
        runtimeApiState.last_error = "Personality Training API failed";
        renderRuntimeApiBanner();
      }
    }

    function renderWarRoomGrowth() {
      const wr = state.warRoomGrowth || {};
      const control = wr.systemControl || {};
      const workspace = wr.runtimeWorkspace || wr.jagWorkspace || {};
      const topStats = wr.runtimeUiStats || {};
      const runtimeStatus = wr.runtimeStatus || control.status || 'STOPPED';
      const currentStage = wr.current_runtime_stage || 'Scout';
      el('war-room-status').className = 'badge ' + runtimeBadgeClass(runtimeStatus);
      el('war-room-status').textContent = runtimeStatus;
      el('war-room-control-panel').innerHTML =
        '<div class="runtime-brand">AGOS Runtime</div>' +
        '<div class="runtime-kv"><span>状态</span><strong>' + esc(runtimeStatus) + '</strong></div>' +
        '<div class="runtime-kv"><span>当前 Cycle</span><strong>' + esc(control.currentCycle || wr.currentCycle || 'CYCLE-001') + '</strong></div>' +
        '<div class="runtime-kv"><span>当前节点</span><strong>' + esc(currentStage) + '</strong></div>' +
        '<div class="runtime-kv"><span>已运行时间</span><strong>' + esc(wr.runtimeElapsed || '00:00:00') + '</strong></div>' +
        '<div class="runtime-kv"><span>Workspace</span><strong>' + esc(control.currentWorkspace || workspace.workspace || 'jag_app_growth') + '</strong></div>' +
        '<div class="runtime-kv"><span>Runtime API</span><strong>' + esc(runtimeApiState.connected ? 'connected' : 'disconnected') + '</strong></div>' +
        '<div class="runtime-kv"><span>Pending Reviews</span><strong>' + esc(topStats.pendingReviews ?? 0) + '</strong></div>' +
        '<div class="runtime-kv"><span>Correction Alerts</span><strong>' + esc(topStats.correctionAlerts ?? 0) + '</strong></div>' +
        '<div class="runtime-kv"><span>Human Decisions Today</span><strong>' + esc(topStats.humanDecisionsToday ?? 0) + '</strong></div>' +
        '<div class="runtime-actions"><button class="primary" type="button" data-runtime-action="start">启动</button><button class="danger" type="button" data-runtime-action="stop">停止</button></div>';
      el('war-room-control-panel').querySelectorAll('[data-runtime-action]').forEach(button => {
        button.addEventListener('click', () => {
          callRuntimeApi(button.dataset.runtimeAction);
        });
      });
      renderRuntimeApiBanner();
      el('runtime-drift-banner').textContent = wr.isLearningDrifting ? 'AGOS 正在学歪风险：需要人工审核样例结论，禁止把样例当成真实反馈。' : 'AGOS 学习方向正常。';
      el('runtime-pipeline-note').textContent = 'current_runtime_stage = ' + currentStage;
      el('runtime-pipeline').innerHTML = (wr.runtimePipeline || []).map(node => {
        const status = node.id === currentStage ? 'current' : node.status;
        return '<div class="pipeline-node node-' + esc(status) + '"><strong>' + esc(node.label) + '</strong><span>' + esc(status) + '</span><span>' + esc(node.note || '') + '</span></div>';
      }).join('');
      el('war-room-feed').innerHTML = (wr.warRoomFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.time) + '</time><div class="feed-main"><strong>' + esc(item.type) + '</strong><span>' + esc(item.sourcePlatform) + ' · ' + esc(item.country) + ' · ' + esc(item.language) + ' · ' + esc(item.audience) + ' · 情绪 ' + esc(item.emotion) + '</span></div><span class="badge ' + (item.status === 'risk' || item.status === 'needs_human_review' ? 'b-amber' : 'b-blue') + '">' + esc(item.aiAction) + '</span></div>'
      ).join('');
      el('war-room-jag-workspace').innerHTML =
        '<div class="runtime-title-row"><h3>Runtime Workspace Card</h3><span class="badge b-cyan">' + esc(workspace.workspaceStatus || 'learning') + '</span></div>' +
        '<div class="runtime-stat-grid">' +
        '<div class="runtime-stat"><span>Workspace</span><strong>' + esc(workspace.workspace || workspace.workspace_id) + '</strong></div>' +
        '<div class="runtime-stat"><span>Industry Pack</span><strong>' + esc(workspace.industryPack) + '</strong></div>' +
        '<div class="runtime-stat"><span>当前目标市场</span><strong>' + esc(workspace.targetMarket || workspace.focusMarket) + '</strong></div>' +
        '<div class="runtime-stat"><span>当前重点平台</span><strong>' + esc((workspace.focusPlatforms || []).join(', ')) + '</strong></div>' +
        '<div class="runtime-stat"><span>当前重点痛点</span><strong>' + esc(workspace.focusPainPoint || '待分析') + '</strong></div>' +
        '<div class="runtime-stat"><span>风险状态</span><strong>' + esc(workspace.riskStatus || 'needs_review') + '</strong></div>' +
        '</div><div style="height:8px"></div><div class="runtime-stat"><span>今日目标</span><strong>' + esc(workspace.todayGoal) + '</strong></div>';
      el('war-room-social-homepages').innerHTML = (wr.socialRuntimeMatrix || []).map(item =>
        '<div class="social-cell"><strong>' + esc(item.platform) + '</strong><span>status: ' + esc(item.status) + '</span><span>today: ' + esc(item.today) + '</span><span>reply: ' + esc(item.reply) + '</span><span>risk: ' + esc(item.risk) + '</span><span>review: ' + esc(item.review) + '</span></div>'
      ).join('');
      el('war-room-growth-cycles').innerHTML = (wr.growthCycles || []).map(cycle => {
        const steps = (cycle.timeline || []).map(step => '<span class="mini-step ' + esc(step.status) + '">' + esc(step.node) + ' ' + (step.status === 'done' ? '✓' : esc(step.status)) + '</span>').join('');
        return '<details class="runtime-details"><summary><span>' + esc(cycle.cycleId) + '</span><span class="mini-steps">' + steps + '</span><span>' + esc(cycle.status) + '</span></summary><div class="runtime-detail-body"><div><strong>收集内容</strong>：' + esc((cycle.collectedQuestions || []).join(' / ')) + '</div><div><strong>分析结果</strong>：' + esc(cycle.analysisConclusion) + '</div><div><strong>学习结果</strong>：' + esc(cycle.learningResult || '') + '</div><div><strong>策略变化</strong>：' + esc(cycle.strategyChange || cycle.generatedStrategy) + '</div></div></details>';
      }).join('');
      el('war-room-growth-stages').innerHTML = (wr.growthStages || []).map(stage =>
        '<details class="strategy-stage"><summary>' + esc(stage.cycleRange) + '<br>' + esc(stage.name) + '</summary><div><strong>阶段目标</strong><br>' + esc(stage.stageGoal) + '<br><strong>学习数量</strong> ' + esc(stage.learningCount ?? stage.collectionCount) + '<br><strong>高价值问题</strong><br>' + esc(stage.highValueQuestion || '待收集') + '<br><strong>最强策略</strong><br>' + esc(stage.strongestStrategy || '待形成') + '<br><strong>最大失败</strong><br>' + esc(stage.biggestFailure || '待运行') + '<br><strong>下一阶段重点</strong><br>' + esc(stage.nextFocus) + '</div></details>'
      ).join('');
      el('war-room-correction-panel').innerHTML = (wr.correctionCenter || []).map(item =>
        '<div class="correction-card"><strong>' + esc(item.issue) + '</strong><span class="badge ' + (item.status === 'needs_code_check' || item.status === 'needs_runtime_validation' ? 'b-red' : item.status === 'needs_human_review' ? 'b-amber' : 'b-blue') + '">' + esc(item.status) + '</span><p>' + esc(item.signal) + '</p><p>' + esc(item.action) + '</p></div>'
      ).join('');
      const runtimeStats = wr.runtimeUiStats || {};
      const reviewQueue = wr.reviewQueue || [];
      el('runtime-review-queue').innerHTML = reviewQueue.map(item => {
        const contentText = JSON.stringify(item.content || {});
        const reason = item.ai_reason || 'AGOS requires human review before learning this output.';
        return '<div class="feed-item review-item"><time>' + esc(item.risk_level || 'medium') + '</time><div class="feed-main"><strong>' + esc(item.review_id) + ' · ' + esc(item.target_type || 'Review') + '</strong><span>' + esc(item.source_platform || 'Local Runtime') + ' · ' + esc(item.country || 'local') + ' · ' + esc(item.language || 'n/a') + ' · ' + esc(item.pain_point || 'pain point pending') + '</span><span>Reasoning: ' + esc(reason) + '</span><span>Generated: ' + esc(item.generated_at || item.created_at || '') + '</span><span>AI Output: ' + esc(contentText) + '</span><textarea id="reject_reason_' + esc(item.review_id) + '" placeholder="reject_reason"></textarea><textarea id="modify_text_' + esc(item.review_id) + '" placeholder="human_modified_version"></textarea><div class="runtime-actions"><button class="primary" type="button" data-review-id="' + esc(item.review_id) + '" data-review-decision="approve">Approve</button><button class="danger" type="button" data-review-id="' + esc(item.review_id) + '" data-review-decision="reject">Reject</button><button type="button" data-review-id="' + esc(item.review_id) + '" data-review-decision="modify">Modify</button></div></div><span class="badge b-amber">' + esc(item.status || 'needs_human_review') + '</span></div>';
      }).join('') || '<div class="feed-item"><time>0</time><div class="feed-main"><strong>No pending review items</strong><span>Start Runtime to generate review items, or wait for the next Human Review gate.</span></div><span class="badge b-green">clear</span></div>';
      document.querySelectorAll('[data-review-id]').forEach(button => {
        button.addEventListener('click', () => callRuntimeReview(button.dataset.reviewId, button.dataset.reviewDecision));
      });
      const correctionButton = el('runtime-submit-correction');
      if (correctionButton && !correctionButton.dataset.bound) {
        correctionButton.dataset.bound = "1";
        correctionButton.addEventListener('click', submitRuntimeCorrection);
      }
      el('runtime-drift-monitor').innerHTML = (wr.runtimeDriftEvents || []).map(item =>
        '<div class="correction-card"><strong>' + esc(item.issue) + '</strong><span class="badge ' + (item.status === 'needs_code_check' ? 'b-red' : 'b-amber') + '">' + esc(item.status) + '</span><p>' + esc(item.signal) + '</p><p>' + esc(item.action) + '</p></div>'
      ).join('') || '<div class="correction-card"><strong>Runtime Drift</strong><span class="badge b-green">clear</span><p>No active drift event.</p><p>Continue monitoring platform style, repetition, over-marketing, and workspace pollution.</p></div>';
      el('runtime-correction-history').innerHTML = (wr.correctionHistory || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.created_at || '') + '</time><div class="feed-main"><strong>' + esc(item.correction_type || item.target_type || 'correction') + '</strong><span>' + esc(item.workspace || 'JAG-LAB') + ' · ' + esc(item.industry_pack || '') + ' · ' + esc(item.affected_runtime_stage || '') + '</span><span>Reason: ' + esc(item.correction_reason || item.reason || '') + '</span></div><span class="badge b-amber">' + esc(item.status || 'recorded') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>No correction history yet</strong><span>Submit a correction to create review evidence.</span></div><span class="badge b-amber">pending</span></div>';
      const topMistakes = (runtimeStats.topCorrectedMistakes || []).map(item => item.target_type + ': ' + item.reason).join(' / ') || 'none';
      el('runtime-human-feedback-summary').innerHTML =
        '<div class="runtime-stat"><span>Pending Reviews</span><strong>' + esc(runtimeStats.pendingReviews ?? reviewQueue.length) + '</strong></div>' +
        '<div class="runtime-stat"><span>Correction Alerts</span><strong>' + esc(runtimeStats.correctionAlerts ?? (wr.correctionCenter || []).length) + '</strong></div>' +
        '<div class="runtime-stat"><span>Human Decisions Today</span><strong>' + esc(runtimeStats.humanDecisionsToday ?? 0) + '</strong></div>' +
        '<div class="runtime-stat"><span>Top Corrected Mistakes</span><strong>' + esc(topMistakes) + '</strong></div>' +
        '<div class="runtime-stat"><span>Most Rejected Strategy</span><strong>' + esc(runtimeStats.mostRejectedStrategy || 'none') + '</strong></div>' +
        '<div class="runtime-stat"><span>Most Approved Reply Style</span><strong>' + esc(runtimeStats.mostApprovedReplyStyle || 'none') + '</strong></div>';
      const personality = wr.personalityStatus || {};
      const currentPersonality = personality.currentPersonality || {};
      const workspacePersonality = currentPersonality.workspacePersonality || {};
      const platformPersonality = currentPersonality.platformPersonality || {};
      const marketPersonality = currentPersonality.marketPersonality || {};
      const tonePersonality = currentPersonality.tonePersonality || {};
      el('runtime-personality-status').innerHTML =
        '<div class="runtime-stat"><span>当前人格</span><strong>' + esc((workspacePersonality.personality || []).join(' / ') || workspacePersonality.voice || 'pending') + '</strong></div>' +
        '<div class="runtime-stat"><span>Platform Personality</span><strong>' + esc(platformPersonality.platform || 'pending') + ' · ' + esc((platformPersonality.style || []).join(' / ') || platformPersonality.tone || '') + '</strong></div>' +
        '<div class="runtime-stat"><span>Market Personality</span><strong>' + esc(marketPersonality.market || 'pending') + ' · ' + esc((marketPersonality.style || []).join(' / ')) + '</strong></div>' +
        '<div class="runtime-stat"><span>Tone Personality</span><strong>' + esc(tonePersonality.tone || 'pending') + ' · ' + esc((tonePersonality.traits || []).join(' / ')) + '</strong></div>' +
        '<div class="runtime-stat"><span>最佳人格</span><strong>' + esc((personality.bestPersonality || {}).tone || 'pending') + '</strong></div>' +
        '<div class="runtime-stat"><span>最常被 Reject 的人格</span><strong>' + esc((personality.failedPersonality || {}).tone || 'none') + '</strong></div>' +
        '<div class="runtime-stat"><span>最近人格漂移</span><strong>' + esc(personality.personalityDrift || 'clear') + '</strong></div>';
      el('runtime-personality-feed').innerHTML = (wr.personalityRuntimeFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.type) + '</time><div class="feed-main"><strong>' + esc(item.status) + '</strong><span>' + esc(JSON.stringify(item.summary || {})) + '</span></div><span class="badge ' + (item.status === 'needs_human_review' ? 'b-amber' : 'b-blue') + '">' + esc(item.status) + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Personality Runtime Feed pending</strong><span>Start Runtime or export personality state.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-strategy-personality').innerHTML = (wr.strategyPersonalityFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.platform) + '</time><div class="feed-main"><strong>' + esc(item.goal) + '</strong><span>Philosophy: ' + esc(item.philosophy) + '</span><span>Action: ' + esc(item.action) + '</span><span>Signal: ' + esc(item.success_signal) + '</span></div><span class="badge b-blue">' + esc(item.status || 'ready') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Strategy Personality pending</strong><span>Runtime will map Reddit / TikTok / X / YouTube into different operating strategies.</span></div><span class="badge b-amber">pending</span></div>';
      const strategyEvolution = wr.strategyEvolution || {};
      el('runtime-strategy-evolution').innerHTML = (wr.strategyEvolutionFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.platform) + '</time><div class="feed-main"><strong>' + esc(item.classification) + ' · score ' + esc(item.score) + '</strong><span>' + esc(item.strategy) + '</span><span>' + esc(item.reason) + '</span></div><span class="badge ' + (item.classification === 'long_term_growth' ? 'b-green' : 'b-amber') + '">' + esc(item.classification) + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Strategy Evolution pending</strong><span>Runtime will classify long-term growth strategy versus short-term traffic tactics.</span></div><span class="badge b-amber">pending</span></div>';
      const trainer = wr.runtimeTrainerDashboard || {};
      el('runtime-trainer-dashboard').innerHTML = (wr.runtimeTrainerFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.type) + '</time><div class="feed-main"><strong>' + esc(item.summary) + '</strong><span>' + esc(item.evidence) + '</span></div><span class="badge ' + (trainer.status === 'training_stable' ? 'b-green' : 'b-amber') + '">' + esc(trainer.status || 'training') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Runtime Trainer Console pending</strong><span>Runtime will show best personality, worst personality, drift alerts, correction frequency, strategy changes, and recent learning.</span></div><span class="badge b-amber">pending</span></div>';
      const gate = wr.personalityEvolutionGate || {};
      el('runtime-personality-evolution-gate').innerHTML = (wr.personalityEvolutionGateChecks || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.name) + '</time><div class="feed-main"><strong>' + esc(item.status) + '</strong><span>' + esc(item.evidence) + '</span><span>' + esc(gate.personalityEvolutionSummary || '') + '</span></div><span class="badge ' + (item.status === 'passed' ? 'b-green' : 'b-amber') + '">' + esc(item.status) + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Personality Evolution Gate pending</strong><span>Runtime will validate workspace, platform, market, and strategy personality stability.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-active-patrol-groups').innerHTML = (wr.activePatrolGroups || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.platform) + '</time><div class="feed-main"><strong>' + esc(item.industry_pack) + ' · ' + esc(item.workspace) + '</strong><span>Targets: ' + esc((item.targets || []).join(' / ')) + '</span><span>Keywords: ' + esc((item.keywords || []).join(' / ')) + '</span><span>' + esc(item.next_action || '') + '</span></div><span class="badge b-green">' + esc(item.status || 'active') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Active Patrol Groups pending</strong><span>Scout Network will define patrol groups for Reddit, TikTok, X, YouTube, and Threads by industry pack.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-keyword-expansion').innerHTML = (wr.keywordExpansionFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.seed_keyword) + '</time><div class="feed-main"><strong>' + esc(item.canonical_pain_point) + '</strong><span>Synonyms: ' + esc((item.synonyms || []).join(' / ')) + '</span><span>Slang: ' + esc((item.slang || []).join(' / ')) + '</span><span>Emotion: ' + esc((item.emotion_expressions || []).join(' / ')) + '</span><span>Multilingual: ' + esc((item.multilingual || []).join(' / ')) + '</span></div><span class="badge b-blue">' + esc(item.status || 'expanded') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Keyword Expansion pending</strong><span>Scout Network will expand synonyms, slang, emotion expressions, platform lingo, and multilingual terms.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-topic-discovery').innerHTML = (wr.discoveredTopics || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.frequency) + 'x</time><div class="feed-main"><strong>' + esc(item.canonical_pain_point) + '</strong><span>Types: ' + (item.repeated ? 'repeated ' : '') + (item.emerging ? 'emerging ' : '') + (item.high_emotion ? 'high_emotion' : '') + '</span><span>Sources: ' + esc((item.source_types || []).join(' / ')) + ' · Platforms: ' + esc((item.platforms || []).join(' / ')) + '</span><span>' + esc((item.sample_questions || []).join(' | ')) + '</span></div><span class="badge ' + (item.high_emotion ? 'b-amber' : 'b-blue') + '">' + esc(item.status || 'discovered') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Topic Discovery pending</strong><span>Scout Network will discover frequent, repeated, emerging, and high-emotion questions.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-trend-clustering').innerHTML = (wr.trendClusters || []).map(item =>
        '<div class="feed-item"><time>' + esc((item.platforms || []).join(' / ')) + '</time><div class="feed-main"><strong>' + esc(item.cluster_name) + '</strong><span>Type: ' + esc(item.cluster_type || 'trend_cluster') + ' | Frequency: ' + esc(item.frequency || 0) + ' | Emotion: ' + esc((item.emotion_tags || []).join(' / ')) + '</span><span>Similar trends: ' + esc((item.similar_trends || []).join(' / ')) + '</span><span>Questions: ' + esc((item.similar_questions || []).slice(0, 3).join(' | ')) + '</span><span>' + esc(item.next_action || '') + '</span></div><span class="badge ' + (item.cross_platform ? 'b-green' : 'b-blue') + '">' + esc(item.status || 'clustered') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Trend Clustering pending</strong><span>Scout Network will cluster similar questions, trends, cross-platform discussion, and emotion patterns.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-heat-detection').innerHTML = (wr.heatSignals || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.heat_level || 'watch') + '</time><div class="feed-main"><strong>' + esc(item.cluster_name) + '</strong><span>Score: ' + esc(item.opportunity_score) + ' | Rising: ' + esc(item.rising_score) + ' | Engagement: ' + esc(item.engagement_score) + ' | Emotion: ' + esc(item.emotion_heat_score) + ' | Spread: ' + esc(item.spread_score) + '</span><span>Signals: ' + esc((item.detectedSignals || []).join(' / ')) + '</span><span>' + esc(item.why_hot || '') + '</span></div><span class="badge ' + (item.heat_level === 'hot' ? 'b-green' : (item.heat_level === 'warming' ? 'b-amber' : 'b-blue')) + '">' + esc(item.status || 'detected') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Heat Detection pending</strong><span>Scout Network will detect rising, engagement, emotion, and spread heat signals.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-heat-opportunity-ranking').innerHTML = (wr.heatOpportunityRanking || []).map(item =>
        '<div class="feed-item"><time>#' + esc(item.rank || '-') + '</time><div class="feed-main"><strong>' + esc(item.cluster_name || item.pain_point || 'Opportunity') + '</strong><span>Opportunity score: ' + esc(item.opportunity_score || item.total_score || 0) + ' | Heat: ' + esc(item.heat_level || 'unknown') + '</span><span>Platforms: ' + esc((item.platforms || []).join(' / ')) + '</span><span>' + esc(item.recommended_action || item.reason || '') + '</span></div><span class="badge ' + (item.heat_level === 'hot' ? 'b-green' : 'b-blue') + '">ranked</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Opportunity Ranking pending</strong><span>Heat Detection will rank what is getting hot first.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-strategic-feed').innerHTML = (wr.strategicFeed || []).map(item =>
        '<div class="feed-item"><time>#' + esc(item.rank || '-') + ' ' + esc(item.heat_level || '') + '</time><div class="feed-main"><strong>' + esc(item.cluster_name || 'Strategic signal') + '</strong><span>Why: ' + esc(item.why || '') + '</span><span>Risk: ' + esc(item.risk_level || '') + ' | Opportunity: ' + esc(item.opportunity_level || '') + '</span><span>Content: ' + esc(item.content_direction || '') + '</span><span>Reply: ' + esc(item.reply_direction || '') + '</span></div><span class="badge ' + (item.risk_level === 'medium' ? 'b-amber' : 'b-blue') + '">' + esc(item.status || 'interpreted') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Strategic Feed pending</strong><span>Scout Network will explain why trends matter and output risk, opportunity, content, reply, and platform direction.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-cross-platform-expansion').innerHTML = (wr.crossPlatformExpansionFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.source_platform || 'source') + ' -> ' + esc((item.target_platforms || []).join(' / ')) + '</time><div class="feed-main"><strong>' + esc(item.cluster_name || 'Expansion strategy') + '</strong><span>' + esc(item.strategy || '') + '</span><span>Review: ' + esc(item.review_status || 'needs_human_review') + ' | Status: ' + esc(item.status || 'draft_only') + '</span></div><span class="badge b-amber">draft</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Cross Platform Expansion pending</strong><span>Scout Network will expand TikTok hot signals into Reddit, YouTube, Instagram, X, and SEO local drafts.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-daily-question-import').innerHTML = (wr.dailyQuestions || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.source_type || 'source') + ' ? ' + esc(item.platform || '') + '</time><div class="feed-main"><strong>' + esc(item.question_id || 'question') + '</strong><span>' + esc(item.question_text || '') + '</span><span>Market: ' + esc(item.market || '') + ' | Language: ' + esc(item.language || '') + ' | Pain: ' + esc(item.canonical_pain_point || '') + '</span><span>Source: ' + esc(item.source || '') + ' | Review: ' + esc(item.review_status || 'needs_human_review') + '</span></div><span class="badge b-green">' + esc(item.status || 'imported') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Daily Question Import pending</strong><span>Real Operations will import 10-30 local/manual questions from RSS, manual, CSV, JSON, and local text sources.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-real-reply-attempts').innerHTML = (wr.replyReviewQueue || wr.replyAttempts || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.platform || 'platform') + ' ? ' + esc(item.status || 'draft') + '</time><div class="feed-main"><strong>' + esc(item.reply_attempt_id || 'reply_attempt') + '</strong><span>Question: ' + esc(item.question_text || '') + '</span><span>Draft: ' + esc(item.reply_text || '') + '</span><span>Reason: ' + esc(item.ai_reason || '') + '</span><span>Review: ' + esc(item.review_status || 'needs_human_review') + ' | Safety: ' + esc(item.safety_boundary || '') + '</span></div><span class="badge b-amber">' + esc(item.review_status || 'needs_human_review') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Real Reply Attempts pending</strong><span>Real Operations will generate Reddit, TikTok, and X reply drafts that require human review.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-real-feedback-capture').innerHTML = (wr.feedbackTimeline || wr.feedbackEvents || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.platform || 'platform') + ' ? ' + esc(item.feedback_id || '') + '</time><div class="feed-main"><strong>' + esc(item.reply_attempt_id || 'reply_attempt') + '</strong><span>Signals: liked=' + esc(item.liked) + ' replied=' + esc(item.replied) + ' ignored=' + esc(item.ignored) + ' saved=' + esc(item.saved) + ' shared=' + esc(item.shared) + '</span><span>Question: ' + esc(item.question_text || '') + '</span><span>Note: ' + esc(item.feedback_note || '') + '</span></div><span class="badge ' + (item.has_positive_feedback ? 'b-green' : (item.has_negative_feedback ? 'b-amber' : 'b-blue')) + '">' + esc(item.status || 'captured') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Real Feedback Capture pending</strong><span>Real Operations will record liked, replied, ignored, saved, and shared feedback events.</span></div><span class="badge b-amber">pending</span></div>';
      const bestMemory = wr.bestAnswerMemory || {};
      const bestRows = [
        {label:'Best Answer', value:(bestMemory.bestAnswer || {}).reply_attempt_id || 'none', detail:(bestMemory.bestAnswer || {}).answer_pattern || ''},
        {label:'Best Hook', value:bestMemory.bestHook || 'none', detail:'hook pattern'},
        {label:'Best Tone', value:bestMemory.bestTone || 'none', detail:'tone'},
        {label:'Best Platform Style', value:bestMemory.bestPlatformStyle || 'none', detail:'platform style'},
        {label:'Failed Answers', value:String((bestMemory.failedAnswers || []).length), detail:(bestMemory.failedStrategies || []).join(' / ')}
      ];
      el('runtime-best-answer-learning').innerHTML = bestRows.map(item =>
        '<div class="feed-item"><time>' + esc(item.label) + '</time><div class="feed-main"><strong>' + esc(item.value) + '</strong><span>' + esc(item.detail || '') + '</span></div><span class="badge b-green">learned</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Best Answer Learning pending</strong><span>Real Operations will learn best answer, hook, tone, platform style, and failed patterns.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-daily-report-feed').innerHTML = (wr.runtimeDailyReportFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.type || '') + '</time><div class="feed-main"><strong>' + esc(item.title || '') + ': ' + esc(item.value) + '</strong><span>' + esc(item.detail || '') + '</span></div><span class="badge b-blue">report</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Runtime Daily Report pending</strong><span>Real Operations will summarize today imports, replies, high engagement, ignored items, best content, and best reply.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-failure-analysis').innerHTML = (wr.failureTimeline || wr.failureItems || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.failure_type || item.type || 'failure') + '</time><div class="feed-main"><strong>' + esc(item.reply_attempt_id || item.failure_id || 'failure_item') + '</strong><span>Why failed: ' + esc(item.why_failed || '') + '</span><span>Fix: ' + esc(item.fix_recommendation || '') + '</span><span>Platform: ' + esc(item.platform || 'unknown') + '</span></div><span class="badge b-amber">' + esc(item.status || 'analyzed') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Failure Analysis pending</strong><span>Real Operations will explain ignored content, ignored replies, failed hooks, and failed strategies.</span></div><span class="badge b-amber">pending</span></div>';
      const growthValidation = wr.realGrowthValidation || {};
      const growthSummary = wr.realGrowthValidationSummary || {};
      el('runtime-real-growth-validation').innerHTML = (wr.realGrowthValidationChecks || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.name || 'check') + '</time><div class="feed-main"><strong>' + esc(item.status || '') + '</strong><span>' + esc(item.evidence || '') + '</span><span>Next stage: ' + esc(growthSummary.next_stage || ((growthValidation.runtimeIntelligenceReview || {}).next_stage || '')) + '</span></div><span class="badge ' + (item.status === 'passed' ? 'b-green' : 'b-amber') + '">' + esc(item.status || 'needs_review') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Real Growth Validation pending</strong><span>Real Operations will validate Runtime, Scout, Reply, Feedback, Learning, and Growth Intelligence.</span></div><span class="badge b-amber">pending</span></div>';
      const strategyMemory = wr.longTermStrategyMemory || {};
      const horizon = wr.strategyHorizonClassification || {};
      const strategyMemoryRows = []
        .concat((wr.longTermEffectiveStrategies || []).map(item => ({type:'long_term_growth', title:item.platform || 'platform', detail:item.strategy || '', meta:'durable ' + esc(item.durable_score || 0) + ' / spike ' + esc(item.spike_score || 0), badge:'stored'})))
        .concat((wr.shortTermEffectiveStrategies || []).map(item => ({type:'short_term_traffic', title:item.platform || 'platform', detail:item.strategy || '', meta:'experiment only / risk ' + esc(item.risk || 0), badge:'experiment'})))
        .concat((wr.longTermFailedStrategies || []).slice(0, 3).map(item => ({type:'failed_strategy', title:item.platform || 'platform', detail:item.why_failed || item.failed_pattern || '', meta:item.avoid_rule || '', badge:'avoid'})));
      el('runtime-long-term-strategy-memory').innerHTML = strategyMemoryRows.map(item =>
        '<div class="feed-item"><time>' + esc(item.type) + '</time><div class="feed-main"><strong>' + esc(item.title) + '</strong><span>' + esc(item.detail) + '</span><span>' + esc(item.meta) + '</span><span>Primary: ' + esc(horizon.primary_long_term_direction || '') + '</span></div><span class="badge ' + (item.type === 'long_term_growth' ? 'b-green' : (item.type === 'failed_strategy' ? 'b-amber' : 'b-blue')) + '">' + esc(item.badge) + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Long-Term Strategy Memory pending</strong><span>Autonomous Growth Preparation will distinguish long-term growth from short-term traffic.</span></div><span class="badge b-amber">pending</span></div>';
      const prioritySummary = wr.prioritySummary || {};
      el('runtime-priority-feed').innerHTML = (wr.runtimePriorityFeed || []).map(item =>
        '<div class="feed-item"><time>#' + esc(item.rank || '-') + ' ' + esc(item.type || 'priority') + '</time><div class="feed-main"><strong>' + esc(item.target || '') + ' / ' + esc(item.priority || '') + '</strong><span>Why changed: ' + esc(item.why_changed || '') + '</span><span>AI action: ' + esc(item.ai_action || '') + '</span><span>Top platform: ' + esc(prioritySummary.top_platform || '') + ' / Top question: ' + esc(prioritySummary.top_question || '') + '</span></div><span class="badge ' + (item.priority === 'high' ? 'b-green' : (item.priority === 'medium' ? 'b-blue' : 'b-amber')) + '">' + esc(item.status || 'watch') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Runtime Priority Feed pending</strong><span>Autonomous Growth Preparation will explain why platform, question, trend, and content priorities changed.</span></div><span class="badge b-amber">pending</span></div>';
      const correlationSummary = wr.correlationSummary || {};
      el('runtime-growth-signal-correlation').innerHTML = (wr.growthSignalCorrelationFeed || []).map(item =>
        '<div class="feed-item"><time>#' + esc(item.rank || '-') + ' ' + esc(item.type || 'correlation') + '</time><div class="feed-main"><strong>' + esc(item.target || '') + ' / score ' + esc(item.growth_score || 0) + '</strong><span>Why it matters: ' + esc(item.why_it_matters || '') + '</span><span>AI action: ' + esc(item.ai_action || '') + '</span><span>Strongest: content=' + esc(correlationSummary.strongest_content_signal || '') + ' / platform=' + esc(correlationSummary.strongest_platform_signal || '') + ' / hook=' + esc(correlationSummary.strongest_hook_signal || '') + '</span></div><span class="badge ' + (item.correlation_strength === 'strong' ? 'b-green' : (item.correlation_strength === 'negative' ? 'b-amber' : 'b-blue')) + '">' + esc(item.status || 'watch') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Growth Signal Correlation pending</strong><span>Autonomous Growth Preparation will show which behaviors actually bring growth signals.</span></div><span class="badge b-amber">pending</span></div>';
      const simulationSummary = wr.simulationSummary || {};
      el('runtime-strategy-simulation').innerHTML = (wr.strategySimulationFeed || []).map(item =>
        '<div class="feed-item"><time>#' + esc(item.rank || '-') + ' simulation</time><div class="feed-main"><strong>' + esc(item.scenario || '') + ' / net ' + esc(item.net_strategy_score || 0) + '</strong><span>Predicted: ' + esc(item.predicted_outcome || '') + '</span><span>Recommendation: ' + esc(item.recommendation || '') + '</span><span>Best: ' + esc(simulationSummary.best_scenario || '') + ' / Highest risk: ' + esc(simulationSummary.highest_risk_scenario || '') + '</span></div><span class="badge b-amber">' + esc(item.status || 'needs_human_review') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Runtime Strategy Simulation pending</strong><span>Autonomous Growth Preparation will simulate what happens if AGOS changes operating strategy.</span></div><span class="badge b-amber">pending</span></div>';
      const autoPrepSummary = wr.autonomousGrowthPreparationSummary || {};
      el('runtime-autonomous-prep-gate').innerHTML = (wr.autonomousGrowthPreparationChecks || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.name || 'gate') + '</time><div class="feed-main"><strong>' + esc(item.status || '') + '</strong><span>' + esc(item.evidence || '') + '</span><span>Gate: ' + esc(autoPrepSummary.gate_decision || '') + ' / Next: ' + esc(autoPrepSummary.next_stage || '') + '</span><span>Best simulation: ' + esc(autoPrepSummary.best_strategy_simulation || '') + ' / Top priority: ' + esc(autoPrepSummary.top_priority || '') + '</span></div><span class="badge ' + (item.status === 'passed' ? 'b-green' : 'b-amber') + '">' + esc(item.status || 'needs_human_review') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Autonomous Growth Preparation Gate pending</strong><span>AGOS will validate Runtime, Personality, Scout, Real Ops, and Strategy Intelligence.</span></div><span class="badge b-amber">pending</span></div>';
      const recommendationSummary = wr.recommendationSummary || {};
      el('runtime-action-recommendations').innerHTML = (wr.actionRecommendationFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.type || 'action') + '</time><div class="feed-main"><strong>' + esc(item.recommendation || '') + '</strong><span>Why: ' + esc(item.why_recommended || '') + '</span><span>Risk: ' + esc(item.risk_level || '') + ' / Expected: ' + esc(item.expected_result || '') + '</span><span>Platform: ' + esc(item.platform || '') + ' / Personality: ' + esc(item.personality || '') + ' / Market: ' + esc(item.market || '') + '</span></div><span class="badge b-amber">' + esc(item.status || 'needs_human_review') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Action Recommendation pending</strong><span>Semi-Autonomous Runtime will recommend content, reply, platform, and trend actions for human review.</span></div><span class="badge b-amber">pending</span></div>';
      const actionQueueSummary = wr.actionQueueSummary || {};
      el('runtime-action-queue').innerHTML = (wr.actionQueueFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.queue_id || '') + ' / ' + esc(item.type || 'action') + '</time><div class="feed-main"><strong>' + esc(item.recommendation || '') + '</strong><span>Why: ' + esc(item.why_recommended || '') + '</span><span>Risk: ' + esc(item.risk_level || '') + ' / Platform: ' + esc(item.platform || '') + ' / Market: ' + esc(item.market || '') + '</span><span>Decision: ' + esc(item.decision || 'pending') + ' / Pending: ' + esc(actionQueueSummary.needs_human_approval || 0) + ' / Recorded: ' + esc(actionQueueSummary.decisions_recorded || 0) + '</span></div><span class="badge b-amber">' + esc(item.status || 'needs_human_approval') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Human-Gated Action Queue pending</strong><span>AGOS recommendations will wait for approve, reject, modify, or postpone.</span></div><span class="badge b-amber">pending</span></div>';
      const runtimePlanSummary = wr.runtimePlanSummary || {};
      const platformFocus = wr.todayPlatformFocus || {};
      const contentRhythm = wr.todayContentRhythm || {};
      const replyPriority = wr.todayReplyPriority || {};
      el('runtime-planner-feed').innerHTML = (wr.runtimePlanFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.plan_id || '') + ' / ' + esc(item.time_block || '') + '</time><div class="feed-main"><strong>' + esc(item.planned_action || '') + '</strong><span>Why: ' + esc(item.why_this_plan || '') + '</span><span>Platform: ' + esc(item.platform || '') + ' / Priority: ' + esc(item.priority || '') + ' / Approval: ' + esc(item.approval_state || '') + '</span><span>Focus: ' + esc(platformFocus.primary_platform || '') + ' / Rhythm: ' + esc(contentRhythm.rhythm || '') + ' / Reply: ' + esc(replyPriority.priority || '') + '</span><span>Planned: ' + esc(runtimePlanSummary.planned_actions || 0) + ' / Pending approval: ' + esc(runtimePlanSummary.pending_approval || 0) + '</span></div><span class="badge b-amber">' + esc(item.status || 'wait_for_human_approval') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Runtime Planner pending</strong><span>AGOS will turn approved or pending action recommendations into a local daily operation plan.</span></div><span class="badge b-amber">pending</span></div>';
      const runtimeRiskSummary = wr.runtimeRiskSummary || {};
      el('runtime-risk-feed').innerHTML = (wr.runtimeRiskFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.risk_type || 'risk') + ' / score ' + esc(item.score || 0) + '</time><div class="feed-main"><strong>' + esc(item.level || '') + '</strong><span>Why predicted: ' + esc(item.reason || '') + '</span><span>Mitigation: ' + esc(item.mitigation || '') + '</span><span>Overall: ' + esc(runtimeRiskSummary.overall_risk || '') + ' / Highest: ' + esc(runtimeRiskSummary.highest_risk || '') + ' / Human review: ' + esc(runtimeRiskSummary.requires_human_review || false) + '</span></div><span class="badge ' + (item.level === 'high' ? 'b-red' : (item.level === 'medium' ? 'b-amber' : 'b-green')) + '">' + esc(item.status || 'watch') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Runtime Risk Prediction pending</strong><span>AGOS will predict spam, platform, drift, over-marketing, and repetition risk before execution.</span></div><span class="badge b-amber">pending</span></div>';
      const approvalSummary = wr.approvalSummary || {};
      el('runtime-human-approval').innerHTML = (wr.unifiedApprovalTimeline || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.unified_id || '') + ' / ' + esc(item.queue_type || '') + '</time><div class="feed-main"><strong>' + esc(item.title || '') + ' / ' + esc(item.target_id || '') + '</strong><span>Why: ' + esc(item.why || '') + '</span><span>Risk: ' + esc(item.risk_level || '') + ' / Human action needed: ' + esc(item.human_action_needed || false) + '</span><span>Total: ' + esc(approvalSummary.total_items || 0) + ' / Review: ' + esc(approvalSummary.review_queue_items || 0) + ' / Action: ' + esc(approvalSummary.action_queue_items || 0) + ' / Correction: ' + esc(approvalSummary.correction_queue_items || 0) + '</span></div><span class="badge ' + (item.status === 'approved' ? 'b-green' : (item.status === 'rejected' ? 'b-red' : 'b-amber')) + '">' + esc(item.status || 'needs_human_review') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Human Approval Orchestration pending</strong><span>AGOS will unify Review Queue, Action Queue, and Correction Queue into one approval timeline.</span></div><span class="badge b-amber">pending</span></div>';
      const executionSimulationSummary = wr.executionSimulationSummary || {};
      el('runtime-execution-simulation').innerHTML = (wr.executionSimulationFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.simulation_id || '') + ' / ' + esc(item.type || '') + '</time><div class="feed-main"><strong>' + esc(item.what_would_happen || '') + '</strong><span>Risk if executed: ' + esc(item.risk_if_executed || '') + ' / Platform: ' + esc(item.platform || '') + '</span><span>Status: ' + esc(item.status || '') + ' / External execution: ' + esc(item.external_execution || false) + '</span><span>Total: ' + esc(executionSimulationSummary.total_scenarios || 0) + ' / Blocked by gate: ' + esc(executionSimulationSummary.blocked_by_human_gate || 0) + ' / Ready local dry-run: ' + esc(executionSimulationSummary.ready_for_local_dry_run || 0) + '</span></div><span class="badge ' + (item.status === 'ready_for_local_dry_run' ? 'b-blue' : 'b-amber') + '">' + esc(item.status || 'simulation_only') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Safe Runtime Execution Simulation pending</strong><span>AGOS will simulate what would happen if approved actions were executed, without touching any external platform.</span></div><span class="badge b-amber">pending</span></div>';
      const semiAutoSummary = wr.semiAutonomousRuntimeSummary || {};
      const semiAutoCapability = wr.semiAutonomousRuntimeCapability || {};
      el('runtime-semi-auto-gate').innerHTML = (wr.semiAutonomousRuntimeChecks || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.name || 'gate') + '</time><div class="feed-main"><strong>' + esc(item.status || '') + '</strong><span>' + esc(item.evidence || '') + '</span><span>Requirement: ' + esc(item.requirement || '') + '</span><span>Gate: ' + esc(semiAutoSummary.gate_decision || '') + ' / Next: ' + esc(semiAutoSummary.next_stage || '') + ' / External execution: ' + esc(semiAutoCapability.external_execution_enabled || false) + '</span></div><span class="badge ' + (item.status === 'passed' ? 'b-green' : (item.status === 'warning' ? 'b-amber' : 'b-red')) + '">' + esc(item.status || 'blocked') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Semi-Autonomous Runtime Gate pending</strong><span>AGOS will validate recommendations, planning, approval, risk prediction, and execution simulation before the next stage.</span></div><span class="badge b-amber">pending</span></div>';
      const apiRegistrySummary = wr.apiRegistrySummary || {};
      el('runtime-api-capability-registry').innerHTML = (wr.apiCapabilityFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.platform || '') + '</time><div class="feed-main"><strong>Allowed: ' + esc((item.allowed || []).join(' / ')) + '</strong><span>Forbidden: ' + esc((item.forbidden || []).join(' / ')) + '</span><span>Human review: ' + esc(item.human_review || false) + ' / API call status: ' + esc(item.status || '') + ' / Boundary: ' + esc(item.boundary || '') + '</span><span>Platforms: ' + esc(apiRegistrySummary.platforms || 0) + ' / External API calls enabled: ' + esc(apiRegistrySummary.external_api_calls_enabled || false) + '</span></div><span class="badge b-amber">' + esc(item.status || 'not_connected') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>API Capability Registry pending</strong><span>AGOS will list what platform APIs may and may not be used for.</span></div><span class="badge b-amber">pending</span></div>';
      const credentialVaultSummary = wr.credentialVaultSummary || {};
      el('runtime-platform-credential-vault').innerHTML = (wr.credentialVaultFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.workspace_id || '') + '</time><div class="feed-main"><strong>Credentials: ' + esc(item.credential_count || 0) + ' / Platforms: ' + esc((item.platforms || []).join(' / ')) + '</strong><span>Types: ' + esc((item.credential_types || []).join(' / ')) + '</span><span>Storage: ' + esc(item.storage || '') + ' / Workspace isolated: ' + esc(item.workspace_isolated || false) + ' / Plaintext exposed: ' + esc(item.plaintext_exposed || false) + '</span><span>Git commit allowed: ' + esc(credentialVaultSummary.git_commit_allowed || false) + ' / Public upload allowed: ' + esc(credentialVaultSummary.public_upload_allowed || false) + '</span></div><span class="badge ' + (item.workspace_isolated ? 'b-green' : 'b-red') + '">' + esc(item.storage || 'local_only') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Platform Credential Vault pending</strong><span>AGOS will show redacted local credential status by workspace. Plaintext values are never displayed.</span></div><span class="badge b-amber">pending</span></div>';
      const platformConnectionSummary = wr.platformConnectionSummary || {};
      el('runtime-platform-connection-center').innerHTML = (wr.platformConnectionFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.platform || '') + '</time><div class="feed-main"><strong>' + esc(item.connection_status || '') + ' / read=' + esc(item.read_permission || false) + ' / write=' + esc(item.write_permission || false) + '</strong><span>Token expiration: ' + esc(item.token_expiration || '') + ' / Workspace scope: ' + esc(item.workspace_scope || '') + '</span><span>Credential: ' + esc(item.credential_status || '') + ' / Collection mode: ' + esc(item.allowed_collection_mode || '') + '</span><span>Platforms: ' + esc(platformConnectionSummary.platforms || 0) + ' / Read connected: ' + esc(platformConnectionSummary.read_connected || 0) + ' / Not connected: ' + esc(platformConnectionSummary.not_connected || 0) + ' / Write enabled: ' + esc(platformConnectionSummary.write_enabled || 0) + '</span><span>All write permissions false: ' + esc(platformConnectionSummary.all_write_permissions_false || false) + '</span></div><span class="badge ' + (item.write_permission ? 'b-red' : (item.read_permission ? 'b-green' : 'b-amber')) + '">' + esc(item.write_permission ? 'write_enabled' : item.connection_status || 'connection') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Platform Connection Center pending</strong><span>AGOS will show platform connection status, read permissions, write permissions, token expiration, and workspace scope.</span></div><span class="badge b-amber">pending</span></div>';
      const credentialSetupSummary = wr.credentialSetupSummary || {};
      el('runtime-api-credential-setup-wizard').innerHTML = (wr.credentialSetupFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.platform || '') + '</time><div class="feed-main"><strong>' + esc(item.setup_status || '') + ' / ' + esc(item.credential_type || '') + '</strong><span>Workspace: ' + esc(item.workspace_id || '') + ' / Scope: ' + esc(item.workspace_scope || '') + '</span><span>Storage: ' + esc(item.storage_mode || '') + ' / Secret redacted: ' + esc(item.secret_redacted || false) + ' / Plaintext logged: ' + esc(item.plaintext_logged || false) + '</span><span>Git commit allowed: ' + esc(item.git_commit_allowed || false) + ' / Public upload allowed: ' + esc(item.public_upload_allowed || false) + ' / Write default: ' + esc(credentialSetupSummary.write_permission_default || false) + '</span><span>Supported: ' + esc((credentialSetupSummary.supported_credential_types || []).join(' / ')) + ' / Local storage only: ' + esc(credentialSetupSummary.local_storage_only || false) + ' / Workspace isolated: ' + esc(credentialSetupSummary.workspace_isolation_enabled || false) + '</span></div><span class="badge ' + (item.setup_status === 'configured_locally' ? 'b-green' : 'b-amber') + '">' + esc(item.storage_mode || 'local_only') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>API Credential Setup Wizard pending</strong><span>AGOS will support API Key, OAuth Token, and Refresh Token setup with local-only storage and redacted status.</span></div><span class="badge b-amber">pending</span></div>';
      const liveCollectionSummary = wr.liveCollectionSummary || {};
      el('runtime-live-collection-runner').innerHTML = (wr.liveCollectionFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.collection_id || '') + ' / ' + esc(item.platform || '') + '</time><div class="feed-main"><strong>' + esc(item.query || '') + ' / score ' + esc(item.collection_score || 0) + '</strong><span>Keyword: ' + esc(item.keyword || '') + ' / Hashtag: ' + esc(item.hashtag || '') + '</span><span>' + esc(item.public_signal_text || '') + '</span><span>Read: ' + esc(item.read_status || '') + ' / Write: ' + esc(item.write_status || '') + ' / Boundary: ' + esc(item.execution_boundary || '') + '</span><span>Modes: ' + esc((liveCollectionSummary.supported_collection_modes || []).join(' / ')) + ' / Items: ' + esc(liveCollectionSummary.items_collected || 0) + ' / Write ops enabled: ' + esc(liveCollectionSummary.write_operations_enabled || false) + '</span><span>post=' + esc(liveCollectionSummary.post_enabled || false) + ' / reply=' + esc(liveCollectionSummary.reply_enabled || false) + ' / DM=' + esc(liveCollectionSummary.dm_enabled || false) + ' / follow=' + esc(liveCollectionSummary.follow_enabled || false) + ' / like=' + esc(liveCollectionSummary.like_enabled || false) + '</span></div><span class="badge ' + (item.write_status === 'blocked' ? 'b-green' : 'b-red') + '">' + esc(item.write_status || 'blocked') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Read-Only Live Collection Runner pending</strong><span>AGOS will collect public trend, keyword, hashtag, and public analytics intelligence while blocking write actions.</span></div><span class="badge b-amber">pending</span></div>';
      const complianceSummary = wr.complianceGuardSummary || {};
      el('runtime-collection-compliance-guard').innerHTML = (wr.complianceRiskFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.risk_id || '') + ' / ' + esc(item.platform || '') + '</time><div class="feed-main"><strong>' + esc(item.risk_type || '') + ' / ' + esc(item.status || '') + ' / ' + esc(item.severity || '') + '</strong><span>Evidence: ' + esc(item.evidence || '') + '</span><span>Blocked action: ' + esc(item.blocked_action || '') + ' / Recommended: ' + esc(item.recommended_action || '') + '</span><span>Write ops enabled: ' + esc(item.write_operations_enabled || false) + ' / Auto interaction enabled: ' + esc(item.automatic_interaction_enabled || false) + '</span><span>Allowed: read-only=' + esc(complianceSummary.read_only_collection_allowed || false) + ' / login scrape=' + esc(complianceSummary.automated_login_scrape_allowed || false) + ' / bypass=' + esc(complianceSummary.platform_limit_bypass_allowed || false) + ' / write API=' + esc(complianceSummary.write_api_allowed || false) + '</span><span>post=' + esc(complianceSummary.post_enabled || false) + ' / reply=' + esc(complianceSummary.reply_enabled || false) + ' / DM=' + esc(complianceSummary.dm_enabled || false) + ' / follow=' + esc(complianceSummary.follow_enabled || false) + ' / like=' + esc(complianceSummary.like_enabled || false) + '</span></div><span class="badge ' + (item.status === 'blocked' ? 'b-red' : item.status === 'watch' ? 'b-amber' : 'b-green') + '">' + esc(item.status || 'check') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Collection Compliance Guard pending</strong><span>AGOS will check rate limits, repeated queries, suspicious patterns, write API usage, excessive polling, automated login scraping, platform-limit bypass, and automated interaction.</span></div><span class="badge b-amber">pending</span></div>';
      const liveDataNormalizationSummary = wr.liveDataNormalizationSummary || {};
      el('runtime-live-data-normalization').innerHTML = (wr.normalizedLiveDataFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.normalized_id || '') + ' / ' + esc(item.platform || '') + '</time><div class="feed-main"><strong>' + esc(item.source_type || '') + ' / training ' + esc(item.training_value_score || 0) + ' / strength ' + esc(item.trend_strength || 0) + '</strong><span>source_url: ' + esc(item.source_url || '') + '</span><span>Language: ' + esc(item.language || '') + ' / Market: ' + esc(item.market || '') + ' / Confidence: ' + esc(item.source_confidence || 0) + '</span><span>Pain points: ' + esc((item.pain_points || []).join(' / ')) + '</span><span>Emotion tags: ' + esc((item.emotion_tags || []).join(' / ')) + '</span><span>Items normalized: ' + esc(liveDataNormalizationSummary.items_normalized || 0) + ' / Highest training value: ' + esc(liveDataNormalizationSummary.highest_training_value || 0) + ' / Write ops enabled: ' + esc(liveDataNormalizationSummary.write_operations_enabled || false) + '</span></div><span class="badge ' + ((item.training_value_score || 0) >= 90 ? 'b-green' : 'b-cyan') + '">' + esc(item.language || 'normalized') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Live Data Normalization Pipeline pending</strong><span>AGOS will normalize platform, source_url, language, market, pain_points, emotion_tags, trend_strength, training_value_score, and source_confidence.</span></div><span class="badge b-amber">pending</span></div>';
      const memoryImportSummary = wr.memoryImportSummary || {};
      el('runtime-live-memory-import').innerHTML = (wr.memoryImportFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.target || '') + '</time><div class="feed-main"><strong>' + esc(item.result || '') + ' / imported ' + esc(item.imported || 0) + '</strong><span>Trigger: ' + esc(item.trigger || '') + ' / triggered: ' + esc(item.triggered || false) + '</span><span>Imported normalized items: ' + esc(memoryImportSummary.normalized_items_imported || 0) + ' / Question Inbox: ' + esc(memoryImportSummary.question_inbox_items || 0) + ' / Pain points: ' + esc(memoryImportSummary.pain_points_imported || 0) + '</span><span>Pattern Learning: ' + esc(memoryImportSummary.pattern_learning_triggered || false) + ' / Replay Training: ' + esc(memoryImportSummary.replay_training_triggered || false) + ' / Intelligence Ranking: ' + esc(memoryImportSummary.intelligence_ranking_triggered || false) + '</span><span>Write ops enabled: ' + esc(memoryImportSummary.write_operations_enabled || false) + '</span></div><span class="badge ' + (item.triggered ? 'b-green' : 'b-amber') + '">' + esc(item.target || 'memory') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Live Data Import to Memory pending</strong><span>AGOS will import normalized live intelligence into Question Inbox, Pain Point Library, Pattern Memory, Trend Cluster, and Scout Intelligence.</span></div><span class="badge b-amber">pending</span></div>';
      const collectionReviewSummary = wr.collectionReviewSummary || {};
      el('runtime-api-collection-review').innerHTML = (wr.collectionCorrectionFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.review_id || '') + ' / ' + esc(item.platform || '') + '</time><div class="feed-main"><strong>' + esc(item.action || '') + ' / ' + esc(item.training_route || '') + '</strong><span>Source: ' + esc(item.source_question_id || '') + ' / Correction type: ' + esc((item.correction_type || []).join(' / ')) + '</span><span>Reason: ' + esc(item.correction_reason || '') + '</span><span>Review items: ' + esc(collectionReviewSummary.review_items || 0) + ' / high value: ' + esc(collectionReviewSummary.marked_high_value || 0) + ' / low value: ' + esc(collectionReviewSummary.marked_low_value || 0) + ' / rejected: ' + esc(collectionReviewSummary.rejected || 0) + ' / corrected records: ' + esc(collectionReviewSummary.corrected_records || 0) + '</span><span>Pain corrections: ' + esc(collectionReviewSummary.pain_point_corrections || 0) + ' / Emotion corrections: ' + esc(collectionReviewSummary.emotion_corrections || 0) + ' / Trend corrections: ' + esc(collectionReviewSummary.trend_corrections || 0) + ' / Confidence corrections: ' + esc(collectionReviewSummary.source_confidence_corrections || 0) + '</span><span>Write ops enabled: ' + esc(collectionReviewSummary.write_operations_enabled || false) + '</span></div><span class="badge ' + (item.action === 'reject' ? 'b-red' : item.human_review_required ? 'b-amber' : 'b-green') + '">' + esc(item.action || 'review') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>API Collection Review & Correction pending</strong><span>AGOS will batch approve, reject, classify, mark low value, mark high value, and correct pain point, emotion, trend, and source confidence fields.</span></div><span class="badge b-amber">pending</span></div>';
      const controlledGateSummary = wr.controlledAPICollectionSummary || {};
      const platformSafetyReview = wr.platformIntelligenceSafetyReview || {};
      el('runtime-controlled-api-collection-gate').innerHTML = (wr.controlledAPICollectionChecks || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.check_id || '') + '</time><div class="feed-main"><strong>' + esc(item.capability || '') + ' / ' + esc(item.status || '') + '</strong><span>' + esc(item.result || '') + '</span><span>Gate passed: ' + esc(controlledGateSummary.passed || 0) + '/' + esc(controlledGateSummary.checks || 0) + ' / ready for next phase: ' + esc(controlledGateSummary.ready_for_next_phase || false) + '</span><span>Safety review: ' + esc(platformSafetyReview.overall_risk || '') + ' / blocking risk: ' + esc(platformSafetyReview.blocking_risk || false) + ' / recommendation: ' + esc(platformSafetyReview.phaseExitRecommendation || '') + '</span><span>Write ops: ' + esc(controlledGateSummary.write_operations_enabled || false) + ' / login scraping: ' + esc(controlledGateSummary.automatic_login_scraping_enabled || false) + ' / external interaction: ' + esc(controlledGateSummary.automatic_external_interaction_enabled || false) + '</span></div><span class="badge ' + (item.status === 'passed' ? 'b-green' : 'b-amber') + '">' + esc(item.status || 'gate') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Controlled API Collection Gate pending</strong><span>AGOS will validate Platform Connection Center, Credential Vault, Live Collection Runner, Compliance Guard, Normalization Pipeline, Live Memory Import, and Collection Review & Correction.</span></div><span class="badge b-amber">pending</span></div>';
      const seasonalSummary = wr.seasonalDemandSummary || {};
      el('runtime-seasonal-demand-calendar').innerHTML = (wr.seasonalCalendar || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.season_id || '') + '</time><div class="feed-main"><strong>' + esc(item.season_name || '') + ' / ' + esc(item.time_window || '') + '</strong><span>Likely locations: ' + esc((item.likely_locations || []).join(' / ')) + '</span><span>Demand keywords: ' + esc((item.demand_keywords || []).slice(0, 4).join(' / ')) + '</span><span>Mobility demand: ' + esc((item.predicted_demand_types || []).join(' / ')) + '</span><span>Pain points: ' + esc((item.mobility_pain_points || []).join(' / ')) + '</span><span>Data source: ' + esc(item.data_origin || seasonalSummary.data_source || '') + ' / Google Trends API connected: ' + esc(item.real_api_connected || false) + ' / Review: ' + esc(item.human_review_required || false) + ' / Write ops: ' + esc(item.write_operations_enabled || false) + '</span></div><span class="badge b-cyan">' + esc(item.monitoring_frequency || 'monitor') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Seasonal Demand Calendar pending</strong><span>AGOS will build Japan tourism seasons, holidays, event placeholders, and Google Trends keyword monitoring structure.</span></div><span class="badge b-amber">pending</span></div>';
      const locationHeatmapSummary = wr.locationHeatmapSummary || {};
      el('runtime-location-demand-heatmap').innerHTML = (wr.locationHeatmap || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.location_id || '') + '</time><div class="feed-main"><strong>' + esc(item.location_name || '') + ' / ' + esc(item.location_type || '') + ' / heat ' + esc(item.demand_heat_score || 0) + '</strong><span>Hot reason: ' + esc(item.hot_reason || '') + '</span><span>Related seasons: ' + esc((item.related_seasons || []).join(' / ')) + '</span><span>Mobility demand: ' + esc((item.mobility_demand_types || []).join(' / ')) + '</span><span>Pain points: ' + esc((item.common_pain_points || []).join(' / ')) + '</span><span>Risk score: crowd ' + esc(item.crowd_risk_score || 0) + ' / transfer ' + esc(item.transfer_complexity_score || 0) + ' / luggage ' + esc(item.luggage_difficulty_score || 0) + '</span><span>Driver/vehicle prep: ' + esc(item.driver_vehicle_preparation_required || false) + ' / Real-time crowd data: ' + esc(item.real_time_crowd_data_connected || false) + ' / GPS dispatch: ' + esc(locationHeatmapSummary.gps_dispatch_enabled || false) + ' / Write ops: ' + esc(item.write_operations_enabled || false) + '</span></div><span class="badge ' + ((item.demand_heat_score || 0) >= 80 ? 'b-green' : (item.demand_heat_score || 0) >= 65 ? 'b-amber' : 'b-cyan') + '">' + esc(item.region || 'location') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Location Demand Heatmap pending</strong><span>AGOS will link Japan locations with seasonal demand, mobility pain points, venue/event pressure, and driver/vehicle preparation signals.</span></div><span class="badge b-amber">pending</span></div>';
      const trendConnectorSummary = wr.trendConnectorSummary || {};
      el('runtime-read-only-trends').innerHTML = (wr.platformTrendFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.trend_id || '') + ' / ' + esc(item.platform || '') + '</time><div class="feed-main"><strong>' + esc(item.query || '') + ' / heat ' + esc(item.heat_score || 0) + '</strong><span>Keyword: ' + esc(item.keyword || '') + ' / Hashtag: ' + esc(item.hashtag || '') + '</span><span>' + esc(item.trend_text || '') + '</span><span>Read: ' + esc(item.read_status || '') + ' / Write: ' + esc(item.write_status || '') + ' / Write ops enabled: ' + esc(trendConnectorSummary.write_operations_enabled || false) + '</span></div><span class="badge ' + (item.write_status === 'blocked' ? 'b-green' : 'b-red') + '">' + esc(item.read_status || 'read') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Read-Only Trend Connector pending</strong><span>AGOS will read trend, keyword, hashtag, and public analytics signals without write operations.</span></div><span class="badge b-amber">pending</span></div>';
      const apiRiskSummary = wr.apiRiskSummary || {};
      el('runtime-api-risk-feed').innerHTML = (wr.apiRiskFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.risk_id || '') + ' / ' + esc(item.platform || '') + '</time><div class="feed-main"><strong>' + esc(item.risk_type || '') + ' / ' + esc(item.status || '') + '</strong><span>Usage: ' + esc(item.current_count || 0) + ' / ' + esc(item.limit || 0) + ' (' + esc(item.bucket || '') + ')</span><span>' + esc(item.why || '') + '</span><span>Action: ' + esc(item.recommended_action || '') + '</span><span>Approaching platform risk: ' + esc(apiRiskSummary.approaching_platform_risk || false) + ' / Write ops enabled: ' + esc(apiRiskSummary.write_operations_enabled || false) + '</span></div><span class="badge ' + (item.status === 'safe' ? 'b-green' : item.status === 'blocked' || item.status === 'near_platform_risk' ? 'b-red' : 'b-amber') + '">' + esc(item.status || 'watch') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>API Safety Guard pending</strong><span>AGOS will monitor request frequency, repeated queries, and suspicious read patterns before API use approaches platform risk.</span></div><span class="badge b-amber">pending</span></div>';
      const normalizationSummary = wr.normalizationSummary || {};
      el('runtime-api-normalized-signals').innerHTML = (wr.apiNormalizedSignalFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.signal_id || '') + ' / ' + esc(item.platform || '') + '</time><div class="feed-main"><strong>' + esc(item.source_signal_type || '') + ' / strength ' + esc(item.trend_strength || 0) + '</strong><span>Language: ' + esc(item.language || '') + ' / Market: ' + esc(item.market || '') + ' / Emotion: ' + esc(item.emotion || '') + '</span><span>Engagement: ' + esc(item.engagement_potential || '') + ' / Content: ' + esc(item.content_potential || '') + ' / Reply: ' + esc(item.reply_potential || '') + '</span><span>Topic: ' + esc(item.topic || '') + '</span><span>' + esc(item.why_unified || '') + '</span><span>Signals normalized: ' + esc(normalizationSummary.signals_normalized || 0) + ' / Write ops enabled: ' + esc(normalizationSummary.write_operations_enabled || false) + '</span></div><span class="badge ' + (item.engagement_potential === 'high' ? 'b-green' : 'b-cyan') + '">' + esc(item.language || 'normalized') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>API Signal Normalization pending</strong><span>AGOS will unify TikTok trends, Reddit hot topics, YouTube search, and X trend data into shared language, emotion, platform, strength, and engagement fields.</span></div><span class="badge b-amber">pending</span></div>';
      const apiScoutSummary = wr.apiScoutPipelineSummary || {};
      el('runtime-api-scout-feed').innerHTML = (wr.apiScoutFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.stage || '') + '</time><div class="feed-main"><strong>' + esc(item.status || '') + ' / items ' + esc(item.items || 0) + '</strong><span>' + esc(item.result || '') + '</span><span>Evidence: ' + esc((item.evidence || []).join(' / ')) + '</span><span>API trends entered Scout: ' + esc(apiScoutSummary.api_trends_entered_scout || false) + ' / Strategic interpretations: ' + esc(apiScoutSummary.strategic_interpretations || 0) + ' / Write ops enabled: ' + esc(apiScoutSummary.write_operations_enabled || false) + '</span></div><span class="badge ' + (item.status === 'completed' || item.status === 'active' ? 'b-green' : 'b-amber') + '">' + esc(item.stage || 'Scout') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>API Scout Pipeline pending</strong><span>AGOS will route normalized API trends through Patrol Groups, Keyword Expansion, Topic Discovery, Trend Clustering, Heat Detection, and Strategic Interpretation.</span></div><span class="badge b-amber">pending</span></div>';
      const apiScoutGateSummary = wr.apiScoutGateSummary || {};
      el('runtime-api-scout-gate').innerHTML = (wr.apiScoutGateChecks || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.check_id || '') + '</time><div class="feed-main"><strong>' + esc(item.capability || '') + ' / ' + esc(item.status || '') + '</strong><span>' + esc(item.result || '') + '</span><span>Ready for next phase: ' + esc(apiScoutGateSummary.ready_for_next_phase || false) + ' / Safe trend intelligence ready: ' + esc(apiScoutGateSummary.safe_trend_intelligence_ready || false) + '</span><span>Next phase: ' + esc(apiScoutGateSummary.next_phase || '') + ' / Write ops enabled: ' + esc(apiScoutGateSummary.write_operations_enabled || false) + '</span></div><span class="badge ' + (item.status === 'passed' ? 'b-green' : 'b-amber') + '">' + esc(item.status || 'check') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>API Scout Gate pending</strong><span>AGOS will validate API Registry, Credential Vault, Trend Connector, API Safety Guard, Signal Normalization, and API Scout Pipeline.</span></div><span class="badge b-amber">pending</span></div>';
      const platformApiRiskReview = wr.platformApiRiskReview || {};
      el('runtime-platform-api-risk-review').innerHTML = (platformApiRiskReview.riskItems || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.risk_id || '') + '</time><div class="feed-main"><strong>' + esc(item.risk || '') + ' / ' + esc(item.status || '') + '</strong><span>Evidence: ' + esc(typeof item.evidence === 'string' ? item.evidence : JSON.stringify(item.evidence || {})) + '</span><span>Mitigation: ' + esc(item.mitigation || '') + '</span><span>Overall risk: ' + esc(platformApiRiskReview.overall_risk || '') + ' / Blocking risk: ' + esc(platformApiRiskReview.blocking_risk || false) + '</span></div><span class="badge ' + (item.status === 'blocked' || item.status === 'controlled' ? 'b-green' : 'b-amber') + '">' + esc(item.status || 'risk') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Platform API Risk Review pending</strong><span>AGOS will show write-side automation, credential, rate-limit, signal interpretation, and Scout escalation risks.</span></div><span class="badge b-amber">pending</span></div>';
      const externalSandboxSummary = wr.externalActionSandboxSummary || {};
      el('runtime-external-action-sandbox').innerHTML = (wr.externalActionFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.external_action_id || '') + ' / ' + esc(item.target_platform || '') + '</time><div class="feed-main"><strong>' + esc(item.external_action_type || '') + ' / ' + esc(item.status || '') + '</strong><span>Action: ' + esc(item.suggested_action || '') + '</span><span>Why: ' + esc(item.why_suggested || '') + '</span><span>Risk: ' + esc(item.risk_level || '') + ' / Human Gate: ' + esc(item.human_gate_status || '') + ' / External execution allowed: ' + esc(item.external_execution_allowed || false) + '</span><span>Blocked reason: ' + esc(item.blocked_reason || '') + '</span><span>Total blocked: ' + esc(externalSandboxSummary.blocked_actions || 0) + ' / Write API calls enabled: ' + esc(externalSandboxSummary.write_api_calls_enabled || false) + '</span></div><span class="badge ' + (item.external_execution_allowed ? 'b-red' : 'b-green') + '">' + esc(item.external_execution_allowed ? 'allowed' : 'blocked') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>External Action Sandbox pending</strong><span>AGOS will prepare simulated-only external replies, content publishing, trend follow-up, and expansion actions. All external execution remains blocked by default.</span></div><span class="badge b-amber">pending</span></div>';
      const batchScoutSummary = wr.batchScoutSummary || {};
      el('runtime-batch-scout').innerHTML = (wr.batchScoutFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.event || '') + '</time><div class="feed-main"><strong>' + (item.question_id ? esc(item.question_id + ' / rank ' + item.rank + ' / score ' + item.priority_score) : esc('Batch processed: ' + (item.questions_processed || 0))) + '</strong><span>' + (item.topic ? esc('Topic: ' + item.topic + ' / Class: ' + item.class + ' / Platform: ' + item.platform) : esc('Scout: ' + (item.scout_completed || 0) + ' / Analyze: ' + (item.analyze_completed || 0) + ' / Classify: ' + (item.classify_completed || 0) + ' / Priority ranked: ' + (item.priority_ranked || 0))) + '</span><span>' + esc(item.why_important || 'Batch Scout Runtime completed local batch processing.') + '</span><span>' + esc(item.recommended_runtime_action || 'AGOS can now process 50-500 questions in one batch.') + '</span><span>Total: ' + esc(batchScoutSummary.questions_processed || 0) + ' / Top score: ' + esc(batchScoutSummary.top_priority_score || 0) + ' / Runtime ready: ' + esc(batchScoutSummary.batch_runtime_ready || false) + '</span></div><span class="badge ' + ((item.priority_band === 'critical' || item.status === 'batch_processed') ? 'b-green' : 'b-cyan') + '">' + esc(item.priority_band || item.status || 'batch') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Batch Scout Runtime pending</strong><span>AGOS will process 50-500 questions through Scout, Analyze, Classify, and Priority Ranking.</span></div><span class="badge b-amber">pending</span></div>';
      const batchClusterSummary = wr.batchClusterSummary || {};
      el('runtime-batch-clusters').innerHTML = (wr.batchClusterFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.cluster_id || '') + '</time><div class="feed-main"><strong>Rank ' + esc(item.rank || 0) + ' / ' + esc(item.cluster_name || '') + ' / score ' + esc(item.growth_signal_score || 0) + '</strong><span>Category: ' + esc(item.category || '') + ' / Frequency: ' + esc(item.frequency || 0) + ' / Platforms: ' + esc((item.platforms || []).join(' / ')) + '</span><span>High frequency: ' + esc(item.high_frequency || false) + ' / High emotion: ' + esc(item.high_emotion || false) + ' / High growth signal: ' + esc(item.high_growth_signal || false) + '</span><span>' + esc(item.recommended_cluster_action || '') + '</span><span>Clusters: ' + esc(batchClusterSummary.clusters_created || 0) + ' / High growth clusters: ' + esc(batchClusterSummary.high_growth_signal_clusters || 0) + ' / Questions clustered: ' + esc(batchClusterSummary.questions_clustered || 0) + '</span></div><span class="badge ' + (item.high_growth_signal ? 'b-green' : 'b-cyan') + '">' + esc(item.high_growth_signal ? 'high_growth' : 'clustered') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Batch Topic Clustering pending</strong><span>AGOS will cluster similar, frequent, high-emotion, and high-growth questions from batch runtime output.</span></div><span class="badge b-amber">pending</span></div>';
      const batchReviewSummary = wr.batchHumanReviewSummary || {};
      el('runtime-batch-human-review').innerHTML = (wr.batchReviewFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.review_id || '') + '</time><div class="feed-main"><strong>' + esc(item.decision || '') + ' / ' + esc(item.label || '') + ' / ' + esc(item.cluster_name || '') + '</strong><span>Category: ' + esc(item.category || '') + ' / Questions: ' + esc(item.question_count || 0) + ' / Human Gate: ' + esc(item.human_gate_status || '') + '</span><span>Training signal: ' + esc(item.training_signal || '') + ' / Risk: ' + esc(item.risk_flag || '') + '</span><span>' + esc(item.human_note || '') + '</span><span>' + esc(item.human_modified_cluster_name ? ('Modified: ' + item.human_modified_cluster_name) : 'Modified: none') + '</span><span>Approve: ' + esc(batchReviewSummary.approve_count || 0) + ' / Reject: ' + esc(batchReviewSummary.reject_count || 0) + ' / Modify: ' + esc(batchReviewSummary.modify_count || 0) + ' / Classify: ' + esc(batchReviewSummary.classify_count || 0) + ' / Batch training ready: ' + esc(batchReviewSummary.batch_training_ready || false) + '</span></div><span class="badge ' + ((item.label === 'spam' || item.label === 'dangerous') ? 'b-red' : (item.decision === 'modify' ? 'b-amber' : 'b-green')) + '">' + esc(item.label || 'review') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Batch Human Review pending</strong><span>AGOS will batch approve, reject, modify, classify, and label clustered questions for local training.</span></div><span class="badge b-amber">pending</span></div>';
      const patternSummary = wr.patternLearningSummary || {};
      el('runtime-pattern-learning').innerHTML = (wr.runtimePatternFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.pattern_id || '') + '</time><div class="feed-main"><strong>' + esc(item.pattern_type || '') + ' / weight ' + esc(item.learning_weight || 0) + '</strong><span>Question combination: ' + esc(item.question_combination || '') + '</span><span>Result pattern: ' + esc(item.result_pattern || '') + '</span><span>Next action: ' + esc(item.recommended_next_action || '') + '</span><span>Patterns learned: ' + esc(patternSummary.patterns_learned || 0) + ' / High value: ' + esc(patternSummary.high_value_patterns || 0) + ' / Engagement: ' + esc(patternSummary.high_engagement_patterns || 0) + ' / Conversion: ' + esc(patternSummary.high_conversion_patterns || 0) + ' / Risk: ' + esc(patternSummary.high_risk_patterns || 0) + '</span></div><span class="badge ' + (item.pattern_type === 'high_risk' ? 'b-red' : (item.pattern_type === 'high_value' ? 'b-green' : 'b-cyan')) + '">' + esc(item.pattern_type || 'pattern') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Runtime Pattern Learning pending</strong><span>AGOS will learn question-combination to result patterns from batch human review signals.</span></div><span class="badge b-amber">pending</span></div>';
      const replaySummary = wr.replayTrainingSummary || {};
      el('runtime-replay-training').innerHTML = (wr.runtimeReplayFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.replay_id || '') + '</time><div class="feed-main"><strong>' + esc(item.source_type || '') + ' / ' + esc(item.replay_result || '') + ' / weight ' + esc(item.training_weight || 0) + '</strong><span>Topic: ' + esc(item.topic || '') + ' / Previous signal: ' + esc(item.previous_signal || '') + '</span><span>Updated intelligence: ' + esc(item.updated_intelligence || '') + '</span><span>Replay items: ' + esc(replaySummary.replay_items || 0) + ' / Questions: ' + esc(replaySummary.historical_questions || 0) + ' / Replies: ' + esc(replaySummary.historical_replies || 0) + ' / Feedback: ' + esc(replaySummary.historical_feedback || 0) + ' / Failures: ' + esc(replaySummary.historical_failures || 0) + '</span><span>Replay learning ready: ' + esc(replaySummary.replay_training_ready || false) + '</span></div><span class="badge ' + (item.source_type === 'historical_failure' ? 'b-red' : (item.source_type === 'historical_feedback' ? 'b-green' : 'b-cyan')) + '">' + esc(item.status || 'replay') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Runtime Replay Training pending</strong><span>AGOS will replay historical questions, replies, feedback, and failures into updated intelligence.</span></div><span class="badge b-amber">pending</span></div>';
      const syntheticSummary = wr.syntheticTrainingSummary || {};
      el('runtime-synthetic-training').innerHTML = (wr.syntheticTrainingFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.synthetic_id || '') + '</time><div class="feed-main"><strong>' + esc(item.synthetic_type || '') + ' / ' + esc(item.platform || '') + ' / weight ' + esc(item.training_weight || 0) + '</strong><span>Topic: ' + esc(item.topic || '') + ' / Feedback: ' + esc(item.simulated_feedback || '') + ' / Interaction: ' + esc(item.simulated_interaction || '') + '</span><span>Risk: ' + esc(item.simulated_risk || '') + ' / Objective: ' + esc(item.training_objective || '') + '</span><span>Synthetic items: ' + esc(syntheticSummary.synthetic_items || 0) + ' / Questions: ' + esc(syntheticSummary.simulated_user_questions || 0) + ' / Feedback: ' + esc(syntheticSummary.simulated_user_feedback || 0) + ' / Interactions: ' + esc(syntheticSummary.simulated_user_interactions || 0) + ' / Risks: ' + esc(syntheticSummary.simulated_user_risks || 0) + '</span><span>Synthetic training ready: ' + esc(syntheticSummary.synthetic_training_ready || false) + '</span></div><span class="badge ' + (item.simulated_risk === 'high' ? 'b-red' : (item.synthetic_type === 'user_interaction' ? 'b-green' : 'b-cyan')) + '">' + esc(item.synthetic_type || 'synthetic') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Synthetic Feedback Training pending</strong><span>AGOS will generate simulated user questions, feedback, interactions, and risk samples for local training.</span></div><span class="badge b-amber">pending</span></div>';
      const accelerationReview = wr.runtimeIntelligenceEvolutionReview || {};
      el('runtime-intelligence-acceleration-gate').innerHTML = (wr.intelligenceAccelerationFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.event || '') + '</time><div class="feed-main"><strong>' + esc(item.check || item.status || '') + ' / ' + esc(item.status || '') + '</strong><span>' + esc(item.evidence || item.evolution_summary || '') + '</span><span>Acceleration score: ' + esc(item.acceleration_score || accelerationReview.acceleration_score || 0) + ' / Ready next stage: ' + esc(accelerationReview.readiness_to_next_stage || false) + '</span><span>Next stage: ' + esc(item.next_stage || accelerationReview.next_stage || '') + '</span><span>Questions: ' + esc(accelerationReview.questions_processed || 0) + ' / Clusters: ' + esc(accelerationReview.clusters_created || 0) + ' / Patterns: ' + esc(accelerationReview.patterns_learned || 0) + ' / Replay: ' + esc(accelerationReview.replay_items || 0) + ' / Synthetic: ' + esc(accelerationReview.synthetic_items || 0) + '</span></div><span class="badge ' + ((item.status === 'passed' || accelerationReview.gate_status === 'passed') ? 'b-green' : 'b-amber') + '">' + esc(item.status || accelerationReview.gate_status || 'gate') + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Intelligence Acceleration Gate pending</strong><span>AGOS will validate Batch Scout, Clustering, Review, Pattern, Replay, and Synthetic Training.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-personality-isolation').innerHTML = (wr.personalityIsolationFeed || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.dimension) + '</time><div class="feed-main"><strong>' + esc(item.status) + '</strong><span>Scopes: ' + esc((item.scopes || []).join(' / ')) + '</span><span>Contexts checked: ' + esc(item.contexts_checked) + ' | Violations: ' + esc(item.violations) + '</span></div><span class="badge ' + (item.status === 'clear' ? 'b-green' : 'b-amber') + '">' + esc(item.status) + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Personality Isolation Report pending</strong><span>Runtime will verify workspace, market, and platform personalities do not cross-pollute.</span></div><span class="badge b-amber">pending</span></div>';
      const reviewSession = wr.personalityReviewSession || {};
      el('runtime-personality-review-session').innerHTML = (wr.personalityReviewTrend || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.signal) + '</time><div class="feed-main"><strong>' + esc(item.status) + '</strong><span>' + esc(item.summary) + '</span><span>Count: ' + esc(item.count) + ' | Window: ' + esc(reviewSession.window_hours || 24) + 'h</span></div><span class="badge ' + (item.status === 'clear' || item.status === 'improving' ? 'b-green' : 'b-amber') + '">' + esc(item.status) + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>Personality Review Session pending</strong><span>Runtime will summarize recent drift, best personality, failed tone, and personality trend.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-personality-timeline').innerHTML = ((personality.personalityTimeline || []).slice(-8)).map(item =>
        '<div class="feed-item"><time>' + esc(item.type) + '</time><div class="feed-main"><strong>' + esc(item.tone || 'tone') + ' · ' + esc(item.platform || 'platform') + '</strong><span>' + esc(item.reason || '') + '</span></div><span class="badge ' + (item.type === 'failed_personality' ? 'b-amber' : 'b-blue') + '">' + esc(item.type) + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>No personality timeline yet</strong><span>Approve or reject personality to build long-term operating memory.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-personality-drift-alerts').innerHTML = (wr.personalityDriftAlerts || []).map(item =>
        '<div class="correction-card"><strong>' + esc(item.issue) + '</strong><span class="badge b-amber">' + esc(item.status) + '</span><p>' + esc(item.reason) + '</p><p>' + esc(item.action) + '</p></div>'
      ).join('') || '<div class="correction-card"><strong>Personality Drift</strong><span class="badge b-green">clear</span><p>AGOS 当前人格未检测到新增漂移。</p><p>继续监控过度营销、过度情绪化、平台人格错乱、clickbait、机械回复、内容重复。</p></div>';
      document.querySelectorAll('[data-personality-decision]').forEach(button => {
        if (!button.dataset.bound) {
          button.dataset.bound = "1";
          button.addEventListener('click', () => submitPersonalityTraining(button.dataset.personalityDecision));
        }
      });
      const personalityTraining = wr.humanPersonalityTraining || {};
      el('runtime-human-personality-training').innerHTML = ((personalityTraining.events || []).slice(-5)).map(item =>
        '<div class="feed-item"><time>' + esc(item.decision) + '</time><div class="feed-main"><strong>' + esc(item.platform) + ' · ' + esc(item.tone) + '</strong><span>' + esc(item.reason) + '</span></div><span class="badge b-blue">' + esc(item.decision) + '</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>No human personality training yet</strong><span>Approve, reject, or modify a personality to train AGOS operating style.</span></div><span class="badge b-amber">pending</span></div>';
      el('runtime-opportunity-ranking').innerHTML = (wr.opportunityRanking || []).map(item =>
        '<div class="feed-item"><time>' + esc(item.verdict) + '</time><div class="feed-main"><strong>' + esc(item.question_id) + ' · score ' + esc(item.total_score) + '</strong><span>' + esc((item.reasons || []).join(' / ')) + '</span></div><span class="badge b-green">训练判断</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>等待训练评分</strong><span>Runtime Training 尚未写入 opportunityRanking。</span></div><span class="badge b-amber">pending</span></div>';
      const intelligence = wr.runtimeIntelligenceFeed || {};
      const intelligenceItems = ['best_answer', 'best_hook', 'best_platform_style', 'best_timing', 'failed_strategy', 'failed_reply', 'failed_hook'].map(key => ({
        key,
        value: intelligence[key]
      })).filter(item => item.value && item.value.length !== 0);
      el('runtime-intelligence-feed').innerHTML = intelligenceItems.map(item =>
        '<div class="feed-item"><time>' + esc(item.key) + '</time><div class="feed-main"><strong>' + esc(item.key.replaceAll('_', ' ')) + '</strong><span>' + esc(JSON.stringify(item.value)) + '</span></div><span class="badge b-blue">deposit</span></div>'
      ).join('') || '<div class="feed-item"><time>WAIT</time><div class="feed-main"><strong>等待 Intelligence Deposit</strong><span>Best Answer / Best Hook / Failed Strategy 尚未写入。</span></div><span class="badge b-amber">pending</span></div>';
      el('war-room-intelligence-trace').textContent = JSON.stringify(wr.intelligenceCollectionTrace || []);
      el('war-room-learning-deposit').textContent = JSON.stringify(wr.learningDepositTrace || []);
    }

    async function fetchRuntimeBridgeState() {
      if (location.protocol !== "http:" && location.protocol !== "https:") return;
      if (runtimeApiState.connected) return;
      try {
        const response = await fetch(`runtime/runtime_state/ui_state.json?runtime_bridge=${Date.now()}`, { cache: "no-store" });
        if (!response.ok) return;
        const runtimeData = await response.json();
        mergeRuntimeBridgeData(runtimeData);
        renderWarRoomGrowth();
      } catch (error) {
        console.warn("Runtime bridge state fetch failed", error);
      }
    }


    function renderGit() {
      const git = state.git;
      el("git-status-badge").className = `badge ${statusClass[git.status] || "b-blue"}`;
      el("git-status-badge").textContent = statusLabel[git.status] || git.status;
      el("git-location").textContent = `repository: ${git.repositoryUrl || git.uploadLocationLabel}`;
      el("git-branch").textContent = `branch: ${git.branch || "pending"}`;
      el("git-commit").textContent = `commit: ${git.latestCommit || "pending"}`;
      el("git-note").innerHTML = esc(git.note);
      if (git.latestCommitUrl) {
        el("git-link").href = git.latestCommitUrl;
        el("git-link").textContent = "打开当前 commit";
      }
    }

    function renderModules() {
      el("module-grid").innerHTML = state.modules.map(item => `
        <article class="card">
          <div class="topline">
            <h3>${esc(item.name)}</h3>
            ${badge(item.status)}
          </div>
          <div class="bar" style="--value:${Number(item.progress) || 0}%"><i></i></div>
          <p><strong>${Number(item.progress) || 0}%</strong> · <code>${esc(item.ownerPath)}</code></p>
          <p>${esc(item.next)}</p>
        </article>
      `).join("");
    }

    function isGateRound(roundId) {
      return ["R012", "R020", "R030", "R040", "R048", "R054", "R060"].includes(roundId);
    }

    function previousRoundId(roundId) {
      const index = state.rounds.findIndex(item => item.id === roundId);
      return index > 0 ? state.rounds[index - 1].id : "无";
    }

    function roundActionLabel(round) {
      if (round.status === "done") return "本轮已完成，摘要应记录实际修改、验证结果、Git 版本和剩余风险。";
      if (round.status === "in_progress") return "本轮正在执行，摘要用于追踪当前目标、已完成部分、待验证项目和下一步动作。";
      if (round.status === "blocked") return "本轮当前阻塞，摘要应优先说明阻塞原因、所需决策和恢复条件。";
      return "本轮尚未开始，摘要说明即将建设的能力、允许改动范围、验证方式和完成标准。";
    }

    function roundSummary(round) {
      if (round.summary) return round.summary;
      const gateText = isGateRound(round.id)
        ? "这是阶段验收 Round，完成后必须停止继续推进，并通知用户人工验收。"
        : `执行前必须先验证上一轮 ${previousRoundId(round.id)} 的报告、测试结果、控制中心状态和 Git 状态。`;
      return `${round.name} 属于 ${round.phase}。本轮核心交付是：${round.deliverable}。${roundActionLabel(round)} 验证重点包括报告路径 ${round.report} 是否生成或更新、控制中心状态是否同步、相关 smoke test 是否通过。${gateText}`;
    }

    function renderRoundDetail(round) {
      if (!round) return;
      el("round-detail").innerHTML = `
        <div class="topline">
          <div>
            <h3>${esc(round.id)} · ${esc(round.name)}</h3>
            <p>${esc(roundSummary(round))}</p>
          </div>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
            ${badge(round.status)}
            <button class="detail-close" type="button" aria-label="关闭 Round 摘要">关闭</button>
          </div>
        </div>
        <div class="round-detail-grid">
          <div class="detail-box">
            <h3>${round.status === "done" ? "本轮已做" : "本轮要做"}</h3>
            <ul>
              <li>围绕 ${esc(round.deliverable)} 建立可验证交付物。</li>
              <li>执行前检查上一轮结果，执行后更新控制中心和 Round 报告。</li>
              <li>${isGateRound(round.id) ? "本轮是阶段验收点，需要用户确认后再继续。" : "本轮不是阶段门，完成验证后可以进入下一轮。"}</li>
            </ul>
          </div>
          <div class="detail-box">
            <h3>验证与报告</h3>
            <ul>
              <li>前置验证：${esc(previousRoundId(round.id))}</li>
              <li>报告路径：<code>${esc(round.report)}</code></li>
              <li>进度：${Number(round.progress) || 0}%</li>
              <li>验收：${isGateRound(round.id) ? "需要用户阶段验收" : "协作验收记录写入报告"}</li>
            </ul>
          </div>
        </div>
      `;
      el("round-detail").classList.add("open");
      el("round-detail").querySelector(".detail-close").addEventListener("click", () => {
        el("round-detail").classList.remove("open");
      });
    }

    function renderRounds(filter = "all") {
      const rounds = state.rounds.filter(r => filter === "all" || r.status === filter || r.phase === filter);
      el("round-list").innerHTML = rounds.map(r => `
        <article class="round-card" data-round-id="${esc(r.id)}" tabindex="0" role="button" aria-label="查看 ${esc(r.id)} 摘要">
          <div class="round-top">
            <h3 class="round-title">${esc(r.id)} · ${esc(r.name)}</h3>
            ${badge(r.status)}
          </div>
          <div class="bar" style="--value:${Number(r.progress) || 0}%"><i></i></div>
          <ul>
            <li>${esc(r.phase)}</li>
            <li>交付物：${esc(r.deliverable)}</li>
            <li>报告：<code>${esc(r.report)}</code></li>
          </ul>
        </article>
      `).join("");
      document.querySelectorAll(".round-card").forEach(card => {
        const open = () => {
          const round = state.rounds.find(item => item.id === card.dataset.roundId);
          if (!round) return;
          document.querySelectorAll(".round-card").forEach(item => item.classList.remove("active"));
          card.classList.add("active");
          renderRoundDetail(round);
        };
        card.addEventListener("click", open);
        card.addEventListener("keydown", event => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            open();
          }
        });
      });
      el("round-detail").classList.remove("open");
    }

    function renderReports() {
      el("report-list").innerHTML = state.reports.map(report => `
        <article class="card" style="margin-bottom:12px">
          <div class="topline">
            <h3>${esc(report.id)} · ${esc(report.title)}</h3>
            ${badge(report.status)}
          </div>
          <p>${esc(report.date)} · ${esc(report.summary)}</p>
          <div class="table-wrap">
            <table>
              <tbody>
                <tr><th>修改文件</th><td>${report.files.map(f => `<code>${esc(f)}</code>`).join(" ")}</td></tr>
                <tr><th>验证结果</th><td>${report.verification.map(v => esc(v)).join("；")}</td></tr>
              </tbody>
            </table>
          </div>
        </article>
      `).join("");
    }

    function renderVersions() {
      el("version-list").innerHTML = state.versions.map((version, index) => `
        <div class="version-row">
          <div>
            <h3>${esc(version.label)}</h3>
            <p>${esc(version.date)} · Git: <code>${esc(version.gitRef)}</code> · 位置：<code>${esc(version.location)}</code></p>
            <p>${esc(version.notes)}</p>
          </div>
          <div class="version-actions">
            <button class="action primary" data-version="${index}">保存快照</button>
            <button class="copy-btn" data-copy="${esc(version.location)}">复制位置</button>
          </div>
        </div>
      `).join("");
      document.querySelectorAll("[data-version]").forEach(btn => {
        btn.addEventListener("click", () => saveSnapshot(state.versions[Number(btn.dataset.version)]));
      });
      document.querySelectorAll("[data-copy]").forEach(btn => {
        btn.addEventListener("click", () => copyText(btn.dataset.copy));
      });
    }

    function renderPaths() {
      el("path-table").innerHTML = state.paths.map(item => `
        <tr>
          <td><code>${esc(item.path)}</code></td>
          <td>${esc(item.purpose)}</td>
          <td><button class="copy-btn" data-copy="${esc(item.path)}">复制路径</button></td>
        </tr>
      `).join("");
      document.querySelectorAll("#path-table [data-copy]").forEach(btn => {
        btn.addEventListener("click", () => copyText(btn.dataset.copy));
      });
    }

    function bindFilters() {
      el("round-filters").addEventListener("click", event => {
        const button = event.target.closest("button[data-filter]");
        if (!button) return;
        document.querySelectorAll("#round-filters button").forEach(btn => btn.classList.remove("active"));
        button.classList.add("active");
        renderRounds(button.dataset.filter);
      });
    }

    function bindRoundTemplate() {
      el("generate-round").addEventListener("click", () => {
        const data = {
          id: el("new-id").value.trim(),
          phase: el("new-phase").value.trim(),
          name: el("new-name").value.trim(),
          status: el("new-status").value,
          progress: el("new-status").value === "done" ? 100 : 0,
          deliverable: el("new-deliverable").value.trim(),
          report: el("new-report").value.trim()
        };
        el("round-output").value = JSON.stringify(data, null, 2);
      });
    }

    renderOverview();
    renderRealGrowth();
    renderSeasonalDemandCalendar();
    renderPhaseBlueprint();
    renderWarRoomGrowth();
    fetchRuntimeApiStatus();
    fetchRuntimeBridgeState();
    renderGit();
    renderModules();
    renderRounds();
    renderReports();
    renderVersions();
    renderPaths();
    bindFilters();
    bindRoundTemplate();

    async function checkForControlCenterUpdate() {
      if (location.protocol !== "http:" && location.protocol !== "https:") return;
      try {
        const response = await fetch(`${location.pathname}?control_center_check=${Date.now()}`, { cache: "no-store" });
        const html = await response.text();
        const match = html.match(/<script id="project-state" type="application\/json">([\s\S]*?)<\/script>/);
        if (!match) return;
        const latest = JSON.parse(match[1]);
        if (latest.project?.controlCenterVersion && latest.project.controlCenterVersion !== state.project.controlCenterVersion) {
          location.reload();
        }
      } catch (error) {
        console.warn("Control center auto-refresh check failed", error);
      }
    }

    setInterval(checkForControlCenterUpdate, 5000);
    setInterval(fetchRuntimeApiStatus, 2500);
    setInterval(fetchRuntimeBridgeState, 2500);