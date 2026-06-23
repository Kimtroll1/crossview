const CV_API_BASE = window.CROSSVIEW_API_BASE_URL || "http://localhost:8000";
const CV_REPORT_URL = window.CROSSVIEW_REPORT_URL || "http://localhost:3000";

let currentVideoId = "";
let analysisInFlight = false;
let lastAutoAnalyzedVideoId = "";
let activeTheme = localStorage.getItem("crossview-theme") || "auto";
let lastAnalysis = null;
let authState = { token: "", user: null };
let bootTimer = null;

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const byId = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;").replaceAll("'", "&#039;");

function sendMessage(payload) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(payload, (response) => {
      if (chrome.runtime.lastError) return reject(new Error(chrome.runtime.lastError.message));
      if (!response?.success) return reject(new Error(response?.error || "CrossView background error"));
      resolve(response.data);
    });
  });
}

async function refreshAuth() {
  const data = await sendMessage({ action: "getAuth" });
  authState = data || { token: "", user: null };
  updateAccountUI();
  return authState;
}

async function apiRequest(path, { method = "GET", body, auth = true, timeout = 45000 } = {}) {
  return sendMessage({ action: "apiRequest", url: `${CV_API_BASE}${path}`, method, body, auth, timeout });
}

function getText(selector) {
  const node = document.querySelector(selector);
  return node?.innerText?.trim() || "";
}
function getVideoId() { return new URLSearchParams(location.search).get("v") || ""; }
function getDescription() {
  return (getText("#description-inline-expander") || getText("ytd-text-inline-expander") || getText("#description") || "").slice(0, 8000);
}
function getTranscript() {
  const chunks = [];
  ["ytd-transcript-segment-renderer", "#segments-container", "ytd-engagement-panel-section-list-renderer[target-id='engagement-panel-searchable-transcript']"].forEach((selector) => {
    document.querySelectorAll(selector).forEach((node) => {
      const text = node.innerText?.trim();
      if (text && text.length > 20) chunks.push(text);
    });
  });
  return [...new Set(chunks)].join("\n").slice(0, 16000);
}
function getComments() {
  const values = [];
  ["ytd-comment-thread-renderer #content-text", "ytd-comment-renderer #content-text", "#comments #content-text"].forEach((selector) => {
    document.querySelectorAll(selector).forEach((node) => {
      const text = node.innerText?.trim();
      if (text && text.length > 3) values.push(text);
    });
  });
  return [...new Set(values)].slice(0, 80);
}
function getContext() {
  const comments = getComments();
  const transcript = getTranscript();
  const description = getDescription();
  const source = [transcript && "transcript", comments.length && "comments", description && "description"].filter(Boolean);
  return {
    userId: authState.user?.externalId || "demo-user",
    videoId: getVideoId(),
    url: location.href,
    title: getText("h1 yt-formatted-string") || getText("h1") || document.title.replace(" - YouTube", ""),
    channelName: getText("ytd-channel-name a") || getText("#owner #channel-name a") || "채널 정보 없음",
    description,
    transcript,
    commentsText: comments.map((item, index) => `${index + 1}. ${item}`).join("\n"),
    commentsCount: comments.length,
    analysisSource: source.length ? source.join("+") : "metadata",
    collectedAt: new Date().toISOString(),
    forceRefresh: false,
    refreshResources: false
  };
}

function sourceLabel(source, count) {
  const output = [];
  if (source?.includes("transcript")) output.push("스크립트");
  if (source?.includes("comments")) output.push(`댓글 ${count || 0}개`);
  if (source?.includes("description")) output.push("영상 설명");
  return output.join(" + ") || "제목·채널 메타데이터";
}
function scoreLabel(score) { return score <= 1 ? "낮음" : score <= 3 ? "보통" : score === 4 ? "높음" : "매우 높음"; }
function biasPercent(score) { return ((Math.max(-5, Math.min(5, Number(score) || 0)) + 5) / 10) * 100; }
function isDark() { return document.documentElement.hasAttribute("dark") || document.querySelector("html[dark]") || matchMedia("(prefers-color-scheme:dark)").matches; }
function applyTheme() {
  const panel = byId("crossview-panel"); if (!panel) return;
  const resolved = activeTheme === "auto" ? (isDark() ? "dark" : "light") : activeTheme;
  panel.classList.toggle("cv-theme-dark", resolved === "dark");
  panel.classList.toggle("cv-theme-light", resolved !== "dark");
  const button = byId("cv-theme-btn"); if (button) button.textContent = activeTheme === "auto" ? "A" : activeTheme === "dark" ? "D" : "L";
}
function cycleTheme() {
  activeTheme = activeTheme === "auto" ? "light" : activeTheme === "light" ? "dark" : "auto";
  localStorage.setItem("crossview-theme", activeTheme); applyTheme();
}

function signalRow(icon, label, item) {
  const score = Number(item?.score) || 0;
  const dots = Array.from({ length: 5 }, (_, index) => `<i class="${index < score ? "active" : ""}"></i>`).join("");
  const reasons = (item?.reasons || []).slice(0, 2).map((reason) => `<li>${escapeHtml(reason)}</li>`).join("");
  return `<div class="cv-signal-row"><div class="cv-signal-head"><span>${icon} ${label}</span><strong>${escapeHtml(item?.label || scoreLabel(score))}</strong></div><div class="cv-dots">${dots}</div>${reasons ? `<ul>${reasons}</ul>` : ""}</div>`;
}
function flowMeter(label, score, left, right) {
  return `<div class="cv-flow-meter"><div><span>${label}</span><strong>${scoreLabel(score)}</strong></div><div class="cv-flow-labels"><span>${left}</span><span>${right}</span></div><div class="cv-flow-track"><i style="width:${Math.max(0, Math.min(5, score)) / 5 * 100}%"></i></div></div>`;
}
function renderList(items) { return (items || []).map((item) => `<li>${escapeHtml(item)}</li>`).join(""); }
function categoryLabel(category) { return category === "opposite" ? "다른 관점" : category === "neutral" ? "중립 해설" : category === "verification" ? "검증·원문" : "비슷한 관점"; }
function renderResources(items) {
  if (!items?.length) return `<div class="cv-empty">실제 검색 자료가 없습니다. YouTube API와 Gemini 검색 설정을 확인해주세요.</div>`;
  return items.map((item) => `
    <a class="cv-resource" data-resource-id="${item.id || ""}" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">
      <div class="cv-resource-thumb">${item.thumbnailUrl ? `<img src="${escapeHtml(item.thumbnailUrl)}" alt=""/>` : `<span>${item.type === "youtube" ? "▶" : item.type === "official" ? "📄" : "📰"}</span>`}</div>
      <div><div class="cv-resource-badges"><span>${escapeHtml(item.stanceLabel || categoryLabel(item.category))}</span>${item.verifiedUrl ? "<em>실제 링크</em>" : ""}</div><h4>${escapeHtml(item.title)}</h4><p>${escapeHtml(item.recommendationReason || item.summary || "")}</p><small>${escapeHtml(item.source || "")}${item.publishedAt ? ` · ${escapeHtml(item.publishedAt.slice(0, 10))}` : ""}</small></div>
    </a>`).join("");
}

function fallbackAnalysis(context) {
  const political = /(정치|대통령|정부|국회|선거|정책|외교|안보)/.test(`${context.title} ${context.description}`);
  const signal = (score, reason) => ({ score, label: scoreLabel(score), reasons: [reason] });
  return {
    summary: `현재 백엔드 연결이 되지 않아 "${context.title}"에 대한 브라우저 예시 결과를 표시합니다.`,
    mainClaims: ["핵심 주장을 확인하세요.", "출처와 반론을 비교하세요."], evidenceSummary: "백엔드 연결 후 실제 근거를 분석합니다.", cautionPoints: ["현재 결과는 mock입니다."],
    sourceUsed: context.analysisSource, sourceLabel: sourceLabel(context.analysisSource, context.commentsCount), commentsIncluded: !!context.commentsCount, commentsCount: context.commentsCount,
    commentMood: "댓글 정보 예시", commentIntensity: "보통", commentLeaning: "약간 쏠림", commentWarningSignals: [],
    commentFlow: { opinionConcentration: context.commentsCount ? 3 : 0, emotionIntensity: context.commentsCount ? 2 : 0, summary: context.commentsCount ? "동조 의견이 일부 집중된 예시입니다." : "댓글이 충분하지 않습니다.", sampleSize: context.commentsCount },
    isPolitical: political, biasScore: political ? 1 : 0, biasLabel: political ? "중립에 가까운 보수" : "비정치 영상", biasSummary: "mock 결과입니다.", biasCriteria: political ? ["백엔드 연결 후 실제 판단 근거 제공"] : [], biasConfidence: political ? .2 : 0,
    biasSignals: { emotionalManipulation: signal(2, "mock 예시"), evidenceSelection: signal(3, "mock 예시"), viewpointOmission: signal(2, "mock 예시"), sourceConcentration: signal(1, "mock 예시") },
    aiRisk: "low", aiSummary: "텍스트만으로 AI 생성 여부를 확정할 수 없습니다.", issue: context.title, similarResources: [], oppositeResources: [], neutralResources: [], verificationResources: [], checklist: ["원문 출처가 있는가?", "반대 관점이 소개되는가?"], cached: false, analysisProvider: "browser-mock", warnings: ["백엔드 연결 실패"]
  };
}

function buildPanel(context) {
  const panel = document.createElement("div"); panel.id = "crossview-panel";
  panel.innerHTML = `<div class="cv-shell">
    <header class="cv-header"><div class="cv-title-row"><div><b>CrossView</b><span id="cv-account-badge">게스트</span></div><div class="cv-controls"><button id="cv-theme-btn">A</button><button id="cv-collapse-btn">접기</button></div></div><p>편향 신호 · 댓글 흐름 · 실제 다관점 탐색</p></header>
    <main class="cv-body">
      <section class="cv-account-card" id="cv-account-card"><div id="cv-account-copy"></div><div class="cv-link-form" id="cv-link-form"><input id="cv-link-code" maxlength="6" placeholder="6자리 연결 코드"/><button id="cv-link-btn">계정 연결</button></div></section>
      <section class="cv-current"><div><small>현재 영상</small><h3 id="cv-current-title">${escapeHtml(context.title)}</h3><p id="cv-current-meta">${escapeHtml(context.channelName)} · ${sourceLabel(context.analysisSource, context.commentsCount)}</p></div><button id="cv-analyze-btn">다시 분석</button><p id="cv-status">자동 분석을 준비 중입니다.</p></section>
      <div id="cv-results" class="cv-hidden">
        <section class="cv-card cv-politics" id="cv-politics-card"><div class="cv-card-head"><h3>정치 성향 추정</h3><span id="cv-confidence">신뢰도 0%</span></div><div class="cv-bias-labels"><span>진보</span><b id="cv-bias-label">중립</b><span>보수</span></div><div class="cv-bias-track"><i id="cv-bias-marker"></i></div><p id="cv-bias-summary"></p><ul id="cv-bias-reasons"></ul></section>
        <section class="cv-card"><div class="cv-card-head"><h3>편향 신호</h3><span>0 낮음 · 5 높음</span></div><div id="cv-signals"></div></section>
        <section class="cv-card"><div class="cv-card-head"><h3>댓글 흐름</h3><span id="cv-comment-count"></span></div><div id="cv-comment-meters"></div><p id="cv-comment-summary"></p><ul id="cv-comment-warnings"></ul></section>
        <section class="cv-card cv-explore-card"><div class="cv-card-head"><h3>다른 관점에서 보기</h3><button id="cv-refresh-resources">새로 찾기</button></div><p class="cv-lead">검색 페이지가 아니라 CrossView가 실제로 확인한 영상·기사·공식 자료입니다.</p><div class="cv-tabs"><button class="active" data-tab="opposite">다른 관점</button><button data-tab="neutral">중립 해설</button><button data-tab="verification">팩트 확인</button><button data-tab="similar">비슷한 관점</button></div><div id="cv-resource-list"></div></section>
        <section class="cv-card"><h3>영상 요약</h3><p id="cv-summary"></p><h4>주요 주장</h4><ul id="cv-claims"></ul><h4>근거와 주의점</h4><p id="cv-evidence"></p><ul id="cv-cautions"></ul></section>
        <section class="cv-card"><div class="cv-card-head"><h3>AI 생성 의심 신호</h3><span id="cv-ai-risk"></span></div><p id="cv-ai-summary"></p></section>
        <section class="cv-card"><h3>판단 체크리스트</h3><div id="cv-checklist"></div><a class="cv-report-link" href="${CV_REPORT_URL}/dashboard" target="_blank">내 미디어 소비 리포트 보기 →</a></section>
      </div>
    </main></div>`;
  return panel;
}

function updateAccountUI() {
  const badge = byId("cv-account-badge"), copy = byId("cv-account-copy"), form = byId("cv-link-form");
  if (!badge || !copy || !form) return;
  if (authState.user) {
    badge.textContent = authState.user.name || authState.user.email || "연결됨";
    copy.innerHTML = `<strong>계정 연결됨</strong><p>${escapeHtml(authState.user.email || authState.user.externalId)}</p><button id="cv-logout-btn">연결 해제</button>`;
    form.classList.add("cv-hidden");
    byId("cv-logout-btn")?.addEventListener("click", async () => { await sendMessage({ action: "logout" }); authState = { token: "", user: null }; updateAccountUI(); });
  } else {
    badge.textContent = "게스트";
    copy.innerHTML = `<strong>개인 리포트 연결</strong><p>웹 설정에서 만든 6자리 코드를 입력하세요.</p><a href="${CV_REPORT_URL}/settings" target="_blank">연결 코드 만들기</a>`;
    form.classList.remove("cv-hidden");
  }
}

function resourceSet(tab) {
  if (!lastAnalysis) return [];
  return tab === "opposite" ? lastAnalysis.oppositeResources : tab === "neutral" ? lastAnalysis.neutralResources : tab === "verification" ? lastAnalysis.verificationResources : lastAnalysis.similarResources;
}
function showResourceTab(tab) {
  document.querySelectorAll(".cv-tabs button").forEach((button) => button.classList.toggle("active", button.dataset.tab === tab));
  const list = byId("cv-resource-list"); if (!list) return;
  list.innerHTML = renderResources(resourceSet(tab));
  list.querySelectorAll(".cv-resource").forEach((link) => link.addEventListener("click", () => {
    const id = Number(link.dataset.resourceId); if (id && authState.token) apiRequest(`/api/resources/${id}/click`, { method: "POST" }).catch(() => undefined);
  }));
}

function renderAnalysis(analysis) {
  lastAnalysis = analysis;
  byId("cv-results")?.classList.remove("cv-hidden");
  const politics = byId("cv-politics-card");
  politics?.classList.toggle("cv-hidden", !analysis.isPolitical);
  if (analysis.isPolitical) {
    byId("cv-bias-marker").style.left = `${biasPercent(analysis.biasScore)}%`;
    byId("cv-bias-label").textContent = `${analysis.biasLabel} ${analysis.biasScore > 0 ? "+" : ""}${analysis.biasScore}`;
    byId("cv-confidence").textContent = `신뢰도 ${Math.round((analysis.biasConfidence || 0) * 100)}%`;
    byId("cv-bias-summary").textContent = analysis.biasSummary || "";
    byId("cv-bias-reasons").innerHTML = renderList(analysis.biasCriteria);
  }
  const signals = analysis.biasSignals || {};
  byId("cv-signals").innerHTML = [
    signalRow("🔥", "감정·선동", signals.emotionalManipulation), signalRow("🔍", "선택적 근거", signals.evidenceSelection),
    signalRow("👥", "관점 누락", signals.viewpointOmission), signalRow("📚", "출처 편중", signals.sourceConcentration)
  ].join("");
  const flow = analysis.commentFlow || { opinionConcentration: 0, emotionIntensity: 0, summary: "댓글 정보 부족", sampleSize: 0 };
  byId("cv-comment-meters").innerHTML = flowMeter("의견 쏠림", flow.opinionConcentration, "다양함", "한쪽 집중") + flowMeter("감정 강도", flow.emotionIntensity, "차분함", "격앙됨");
  byId("cv-comment-count").textContent = `${flow.sampleSize || analysis.commentsCount || 0}개 표본`;
  byId("cv-comment-summary").textContent = flow.summary || analysis.commentMood || "";
  byId("cv-comment-warnings").innerHTML = renderList(analysis.commentWarningSignals);
  byId("cv-summary").textContent = analysis.summary || "";
  byId("cv-claims").innerHTML = renderList(analysis.mainClaims);
  byId("cv-evidence").textContent = analysis.evidenceSummary || "";
  byId("cv-cautions").innerHTML = renderList(analysis.cautionPoints);
  byId("cv-ai-risk").textContent = analysis.aiRisk === "high" ? "높음" : analysis.aiRisk === "medium" ? "일부 의심" : "낮음";
  byId("cv-ai-risk").className = `cv-risk ${analysis.aiRisk || "low"}`;
  byId("cv-ai-summary").textContent = analysis.aiSummary || "";
  byId("cv-checklist").innerHTML = (analysis.checklist || []).map((item) => `<label><input type="checkbox"/><span>${escapeHtml(item)}</span></label>`).join("");
  showResourceTab("opposite");
}

async function freshContext() {
  let context = getContext();
  for (let index = 0; index < 8; index += 1) {
    if (context.title && context.title !== "YouTube" && context.channelName !== "채널 정보 없음") break;
    await wait(250); context = getContext();
  }
  byId("cv-current-title").textContent = context.title || "제목 없음";
  byId("cv-current-meta").textContent = `${context.channelName} · ${sourceLabel(context.analysisSource, context.commentsCount)}`;
  return context;
}

async function runAnalysis({ forceRefresh = false, refreshResources = false } = {}) {
  if (analysisInFlight || !getVideoId()) return;
  analysisInFlight = true;
  const button = byId("cv-analyze-btn"), status = byId("cv-status");
  if (button) button.disabled = true;
  if (status) status.textContent = refreshResources ? "실제 영상·기사·공식 자료를 다시 찾는 중입니다…" : "스크립트·댓글·근거를 분석하는 중입니다…";
  const context = await freshContext(); context.forceRefresh = forceRefresh; context.refreshResources = refreshResources;
  try {
    const analysis = await apiRequest("/api/analyze", { method: "POST", body: context, timeout: 90000 });
    renderAnalysis(analysis);
    if (status) status.textContent = `${analysis.cached ? "저장된 분석 사용" : "새 분석 완료"}${analysis.warnings?.length ? ` · ${analysis.warnings[0]}` : ""}`;
    lastAutoAnalyzedVideoId = context.videoId;
  } catch (error) {
    console.warn("CrossView API unavailable", error);
    renderAnalysis(fallbackAnalysis(context));
    if (status) status.textContent = `백엔드 연결 실패 · 브라우저 예시 표시 (${error.message})`;
  } finally {
    analysisInFlight = false; if (button) button.disabled = false;
  }
}

async function linkAccount() {
  const input = byId("cv-link-code"), button = byId("cv-link-btn");
  const code = input?.value?.trim(); if (!code) return;
  button.disabled = true;
  try {
    await sendMessage({ action: "exchangeCode", apiBase: CV_API_BASE, code });
    await refreshAuth();
    byId("cv-status").textContent = "계정 연결 완료. 다음 분석부터 개인 기록에 저장됩니다.";
  } catch (error) { byId("cv-status").textContent = error.message; }
  finally { button.disabled = false; }
}

function bindPanel() {
  byId("cv-theme-btn")?.addEventListener("click", cycleTheme);
  byId("cv-collapse-btn")?.addEventListener("click", () => {
    const panel = byId("crossview-panel"); panel.classList.toggle("cv-collapsed");
    const collapsed = panel.classList.contains("cv-collapsed"); byId("cv-collapse-btn").textContent = collapsed ? "펼치기" : "접기";
  });
  byId("cv-analyze-btn")?.addEventListener("click", () => runAnalysis({ forceRefresh: true }));
  byId("cv-refresh-resources")?.addEventListener("click", () => runAnalysis({ refreshResources: true }));
  byId("cv-link-btn")?.addEventListener("click", linkAccount);
  document.querySelectorAll(".cv-tabs button").forEach((button) => button.addEventListener("click", () => showResourceTab(button.dataset.tab)));
}

async function mount() {
  if (!location.pathname.startsWith("/watch") || !getVideoId()) return;
  const target = document.querySelector("#secondary-inner") || document.querySelector("#secondary");
  if (!target) { clearTimeout(bootTimer); bootTimer = setTimeout(mount, 700); return; }
  const existing = byId("crossview-panel");
  if (!existing) {
    await refreshAuth().catch(() => undefined);
    const context = getContext(); target.prepend(buildPanel(context)); bindPanel(); applyTheme(); updateAccountUI();
  }
  const nextVideo = getVideoId();
  if (nextVideo && nextVideo !== currentVideoId) {
    currentVideoId = nextVideo; lastAnalysis = null; byId("cv-results")?.classList.add("cv-hidden");
    await wait(700);
    if (lastAutoAnalyzedVideoId !== nextVideo) runAnalysis();
  }
}

window.addEventListener("yt-navigate-finish", () => { clearTimeout(bootTimer); bootTimer = setTimeout(mount, 400); });
new MutationObserver(() => {
  if (location.href.includes("/watch") && (!byId("crossview-panel") || getVideoId() !== currentVideoId)) {
    clearTimeout(bootTimer); bootTimer = setTimeout(mount, 500);
  }
}).observe(document.documentElement, { childList: true, subtree: true });
mount();
