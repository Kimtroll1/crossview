const CROSSVIEW_BACKEND_URL = window.CROSSVIEW_BACKEND_URL || "http://localhost:8000/api/analyze";

let currentUrl = location.href;
let currentVideoId = "";
let activeTheme = "auto";
let analysisInFlight = false;
let lastAutoAnalyzedVideoId = "";
let bootTimer = null;
let autoAnalyzeTimer = null;

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getText(selector) {
  const element = document.querySelector(selector);
  return element ? element.innerText.trim() : "";
}

function getVideoId() {
  return new URLSearchParams(window.location.search).get("v") || "";
}

function isYouTubeDarkMode() {
  return (
    document.documentElement.hasAttribute("dark") ||
    document.querySelector("html[dark]") !== null ||
    document.body.getAttribute("dark") === "true" ||
    window.matchMedia?.("(prefers-color-scheme: dark)")?.matches
  );
}

function getResolvedTheme() {
  if (activeTheme === "dark") return "dark";
  if (activeTheme === "light") return "light";
  return isYouTubeDarkMode() ? "dark" : "light";
}

function applyTheme(panel = document.querySelector("#crossview-panel")) {
  if (!panel) return;
  panel.classList.remove("cv-theme-light", "cv-theme-dark");
  panel.classList.add(`cv-theme-${getResolvedTheme()}`);
}

function cycleTheme() {
  if (activeTheme === "auto") activeTheme = "light";
  else if (activeTheme === "light") activeTheme = "dark";
  else activeTheme = "auto";

  localStorage.setItem("crossview-theme", activeTheme);
  applyTheme();
  updateThemeButton();
}

function updateThemeButton() {
  const btn = document.querySelector("#cv-theme-btn");
  if (!btn) return;
  btn.textContent = activeTheme === "auto" ? "A" : activeTheme === "light" ? "L" : "D";
  btn.title = activeTheme === "auto" ? "테마: 자동" : activeTheme === "light" ? "테마: 라이트" : "테마: 다크";
}

function loadUserSettings() {
  activeTheme = localStorage.getItem("crossview-theme") || "auto";
}

function toggleCollapse() {
  const panel = document.querySelector("#crossview-panel");
  const btn = document.querySelector("#cv-collapse-btn");
  if (!panel || !btn) return;

  panel.classList.toggle("cv-collapsed");
  const collapsed = panel.classList.contains("cv-collapsed");
  localStorage.setItem("crossview-collapsed", collapsed ? "true" : "false");
  btn.textContent = collapsed ? "펼치기" : "접기";
}

function restoreCollapse() {
  const panel = document.querySelector("#crossview-panel");
  const btn = document.querySelector("#cv-collapse-btn");
  if (!panel || !btn) return;

  const collapsed = localStorage.getItem("crossview-collapsed") === "true";
  panel.classList.toggle("cv-collapsed", collapsed);
  btn.textContent = collapsed ? "펼치기" : "접기";
}

function getVisibleTranscriptText() {
  const transcriptSelectors = [
    "ytd-transcript-segment-renderer",
    "ytd-transcript-body-renderer",
    "#segments-container",
    "ytd-engagement-panel-section-list-renderer[target-id='engagement-panel-searchable-transcript']"
  ];

  const chunks = [];

  for (const selector of transcriptSelectors) {
    document.querySelectorAll(selector).forEach((node) => {
      const text = node.innerText?.trim();
      if (text && text.length > 20) chunks.push(text);
    });
  }

  return Array.from(new Set(chunks)).join("\n").slice(0, 12000);
}


function getVisibleCommentsText() {
  const selectors = [
    "ytd-comment-thread-renderer #content-text",
    "ytd-comment-renderer #content-text",
    "#comments #content-text"
  ];

  const comments = [];

  for (const selector of selectors) {
    document.querySelectorAll(selector).forEach((node) => {
      const text = node.innerText?.trim();
      if (text && text.length > 3) {
        comments.push(text);
      }
    });
  }

  return Array.from(new Set(comments)).slice(0, 80);
}

function getPageDescription() {
  return (
    getText("#description-inline-expander") ||
    getText("ytd-text-inline-expander") ||
    getText("#description") ||
    ""
  ).slice(0, 8000);
}

function getYouTubeContext() {
  const title =
    getText("h1 yt-formatted-string") ||
    getText("h1") ||
    document.title.replace(" - YouTube", "");

  const channelName =
    getText("ytd-channel-name a") ||
    getText("#owner #channel-name a") ||
    getText("#channel-name a") ||
    "채널 정보 없음";

  const transcript = getVisibleTranscriptText();
  const description = getPageDescription();
  const comments = getVisibleCommentsText();
  const commentsText = comments.map((comment, index) => `${index + 1}. ${comment}`).join("\n");

  const sourceParts = [];
  if (transcript) sourceParts.push("transcript");
  if (commentsText) sourceParts.push("comments");
  if (description) sourceParts.push("description");
  if (sourceParts.length === 0) sourceParts.push("metadata");

  return {
    videoId: getVideoId(),
    url: window.location.href,
    title,
    channelName,
    description,
    transcript,
    commentsText,
    commentsCount: comments.length,
    analysisSource: sourceParts.join("+"),
    collectedAt: new Date().toISOString()
  };
}

function createSearchResource(title, kind, index, resourceType) {
  const encoded = encodeURIComponent(title || "뉴스 이슈");
  const queryMap = {
    similar: `${encoded}+관련+분석`,
    opposite: `${encoded}+다른+관점`,
    verify: `${encoded}+팩트체크+기사`
  };

  const typeIcons = {
    youtube: "▶",
    article: "📰",
    ai_answer: "AI"
  };

  const labelMap = {
    similar: "비슷한 관점",
    opposite: "다른 관점일 수 있는 자료",
    verify: "검증용 자료"
  };

  const url =
    resourceType === "youtube"
      ? `https://www.youtube.com/results?search_query=${queryMap[kind]}`
      : `https://www.google.com/search?q=${queryMap[kind]}`;

  return {
    type: resourceType,
    title: `${labelMap[kind]} ${index}: 현재 이슈를 비교해볼 자료`,
    source: resourceType === "youtube" ? "YouTube 검색" : "웹/기사 검색",
    url,
    summary: resourceType === "article" ? "관련 기사 또는 웹 자료 검색 결과로 연결됩니다." : "",
    icon: typeIcons[resourceType]
  };
}

function guessPoliticalByTitle(context) {
  const text = `${context.title} ${context.description} ${context.transcript}`.toLowerCase();
  const keywords = [
    "정치", "대통령", "국회", "정부", "여당", "야당", "보수", "진보", "좌파", "우파",
    "선거", "정당", "의원", "민주당", "국민의힘", "정책", "탄핵", "외교", "안보"
  ];
  return keywords.some((keyword) => text.includes(keyword.toLowerCase()));
}

function getFallbackAnalysis(context) {
  const seed = Array.from(context.title || "CrossView").reduce(
    (sum, char) => sum + char.charCodeAt(0),
    0
  );

  const isPolitical = guessPoliticalByTitle(context);
  const biasScore = isPolitical ? (seed % 11) - 5 : 0;
  const aiRiskOptions = ["low", "medium", "high"];
  const aiRisk = aiRiskOptions[seed % aiRiskOptions.length];

  const sourceUsed = context.analysisSource || "metadata";
  const sourceLabelText = sourceLabel(sourceUsed, context.commentsCount || 0);
  const hasComments = Boolean(context.commentsText);

  return {
    summary: `이 영상은 "${context.title || "현재 영상"}"을 중심으로 특정 이슈나 관점을 설명하는 콘텐츠입니다. 현재는 백엔드 연결 실패로 mock 분석을 표시하며, 실제 분석에서는 스크립트·댓글·설명을 함께 사용합니다.`,
    mainClaims: [
      "영상의 핵심 주장이 무엇인지 확인해야 합니다.",
      "영상 안에서 제시된 근거가 충분한지 확인해야 합니다.",
      "반대 관점이나 검증 자료가 함께 제시되는지 확인해야 합니다."
    ],
    evidenceSummary: "mock 분석에서는 실제 근거 추출을 수행하지 않습니다. Gemini 연결 시 스크립트와 설명을 바탕으로 근거를 요약합니다.",
    cautionPoints: [
      "감정적인 표현이 판단에 영향을 줄 수 있습니다.",
      "출처가 없는 단정적 표현은 추가 확인이 필요합니다.",
      "댓글 분위기만으로 사실 여부를 판단하면 안 됩니다."
    ],

    sourceUsed,
    sourceLabel: sourceLabelText,
    commentsIncluded: hasComments,
    commentsCount: context.commentsCount || 0,

    commentMood: hasComments ? "댓글 일부를 감지했습니다." : "댓글 정보 부족",
    commentIntensity: hasComments ? "보통" : "정보 부족",
    commentLeaning: hasComments ? "일부 댓글만으로는 단정하기 어렵습니다." : "정보 부족",
    commentWarningSignals: hasComments
      ? ["비난성 표현 또는 단정적 표현 여부 확인 필요", "동조 댓글이 반복되는지 확인 필요"]
      : ["댓글이 아직 충분히 수집되지 않았습니다."],

    isPolitical,
    biasScore,
    biasLabel:
      biasScore < 0
        ? `좌측 성향 ${Math.abs(biasScore)}`
        : biasScore > 0
          ? `우측 성향 ${biasScore}`
          : "중립에 가까움",
    biasSummary:
      isPolitical
        ? "현재는 mock 분석입니다. 실제 연결 후 스크립트, 설명, 댓글을 기반으로 정치 성향도를 추정합니다."
        : "정치·시사 영상으로 강하게 판단되지 않아 정치 성향도 바를 기본 표시하지 않습니다.",
    aiRisk,
    aiSummary:
      aiRisk === "high"
        ? "AI 음성 또는 합성 콘텐츠일 가능성을 추가 확인해야 합니다."
        : aiRisk === "medium"
          ? "일부 자동 생성 콘텐츠 패턴이 의심됩니다."
          : "현재 기준 뚜렷한 AI 생성 징후는 낮습니다.",
    issue: "현재 영상의 핵심 이슈",
    similarResources: [
      createSearchResource(context.title, "similar", 1, "youtube"),
      createSearchResource(context.title, "similar", 2, "article")
    ],
    oppositeResources: [
      createSearchResource(context.title, "opposite", 1, "youtube"),
      createSearchResource(context.title, "opposite", 2, "article")
    ],
    verificationResources: [
      createSearchResource(context.title, "verify", 1, "article"),
      {
        type: "ai_answer",
        title: "검증용 AI 요약",
        source: "CrossView AI",
        url: "",
        summary: "관련 기사나 공식 자료가 부족할 경우, AI가 확인해야 할 쟁점과 질문을 먼저 정리합니다.",
        icon: "AI"
      }
    ],
    checklist: [
      "스크립트에서 핵심 주장의 근거가 직접 제시되었는가?",
      "다른 출처도 같은 내용을 말하는가?",
      "반대 관점에서는 이 이슈를 어떻게 설명하는가?",
      "댓글 분위기가 판단에 영향을 주고 있지 않은가?",
      "AI 음성·합성 콘텐츠 가능성을 확인했는가?"
    ]
  };
}

async function requestAnalysis(context) {
  try {
    console.debug("CrossView: starting direct fetch", CROSSVIEW_BACKEND_URL);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const response = await fetch(CROSSVIEW_BACKEND_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(context),
      signal: controller.signal
    }).finally(() => clearTimeout(timeoutId));

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    console.debug("CrossView: direct fetch succeeded");
    return await response.json();
  } catch (directFetchError) {
    console.warn("CrossView: direct fetch failed, trying background bridge", directFetchError);
    try {
      console.debug("CrossView: starting background sendMessage fallback");
      const response = await new Promise((resolve, reject) => {
        chrome.runtime.sendMessage(
          {
            action: "analyze",
            url: CROSSVIEW_BACKEND_URL,
            data: context
          },
          (response) => {
            if (chrome.runtime.lastError) {
              reject(new Error(chrome.runtime.lastError.message));
            } else if (!response.success) {
              reject(new Error(response.error));
            } else {
              resolve(response.data);
            }
          }
        );
      });
      console.debug("CrossView: background fallback succeeded");
      return response;
    } catch (messagingError) {
      console.warn(
        "CrossView backend unavailable. Using mock analysis.",
        directFetchError,
        messagingError
      );
      return getFallbackAnalysis(context);
    }
  }
}

function biasToPercent(score) {
  const clamped = Math.max(-5, Math.min(5, Number(score) || 0));
  return ((clamped + 5) / 10) * 100;
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function resourceTypeLabel(type) {
  if (type === "youtube") return "영상";
  if (type === "article") return "기사/웹";
  if (type === "ai_answer") return "AI 답변";
  return "자료";
}

function resourceIcon(type) {
  if (type === "youtube") return "▶";
  if (type === "article") return "📰";
  if (type === "ai_answer") return "AI";
  return "↗";
}

function renderResources(items) {
  if (!items || items.length === 0) {
    return `
      <div class="cv-ai-answer">
        관련 자료를 찾지 못했습니다. AI가 대신 확인할 질문을 정리합니다:
        이 주장의 출처는 무엇인지, 반대 관점은 무엇인지, 통계나 공식 자료가 있는지 확인해보세요.
      </div>
    `;
  }

  return items
    .map((item) => {
      if (item.type === "ai_answer" || !item.url) {
        return `
          <div class="cv-ai-answer">
            <strong>${escapeHtml(item.title || "AI 요약")}</strong><br/>
            ${escapeHtml(item.summary || "확인할 쟁점을 AI가 요약합니다.")}
          </div>
        `;
      }

      return `
        <a class="cv-rec-item" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">
          <div class="cv-resource-icon">${resourceIcon(item.type)}</div>
          <div>
            <span class="cv-resource-type">${resourceTypeLabel(item.type)}</span>
            <p class="cv-rec-title">${escapeHtml(item.title)}</p>
            <p class="cv-rec-meta">${escapeHtml(item.source || "자료")}</p>
          </div>
        </a>
      `;
    })
    .join("");
}

function renderTextList(items) {
  return (items || [])
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
}

function renderChecklist(items) {
  return (items || [])
    .map((item) => `
      <label>
        <input type="checkbox" />
        <span>${escapeHtml(item)}</span>
      </label>
    `)
    .join("");
}

function aiRiskClass(risk) {
  if (risk === "high") return "high";
  if (risk === "medium") return "medium";
  return "low";
}

function aiRiskTitle(risk) {
  if (risk === "high") return "⚠ AI 생성 가능성 높음";
  if (risk === "medium") return "⚠ AI 생성 가능성 일부 의심";
  return "✅ AI 생성 징후 낮음";
}

function sourceLabel(source, commentsCount = 0) {
  const labels = [];
  const sourceText = String(source || "");

  if (sourceText.includes("transcript")) labels.push("스크립트");
  if (sourceText.includes("comments")) labels.push(`댓글 ${commentsCount}개`);
  if (sourceText.includes("description")) labels.push("영상 설명");

  if (labels.length === 0) labels.push("제목·채널 메타데이터");

  return labels.join(" + ");
}

function buildPanel(context) {
  const panel = document.createElement("div");
  panel.id = "crossview-panel";

  panel.innerHTML = `
    <div class="cv-shell">
      <div class="cv-header" id="cv-header">
        <div class="cv-title-row">
          <div class="cv-logo">CrossView</div>
          <div class="cv-controls">
            <button class="cv-icon-btn" id="cv-theme-btn" title="테마 변경">A</button>
            <button class="cv-icon-btn" id="cv-collapse-btn" title="접기">접기</button>
          </div>
        </div>
        <p class="cv-subtitle">스크립트 기반 분석 · 균형 추천 · AI 생성 의심 감지</p>
      </div>

      <div class="cv-body">
        <div class="cv-card">
          <p class="cv-section-title">현재 영상</p>
          <p class="cv-video-title" id="cv-current-title">${escapeHtml(context.title || "제목 없음")}</p>
          <p class="cv-video-meta" id="cv-current-channel">${escapeHtml(context.channelName || "채널 정보 없음")}</p>
          <p class="cv-source-note">
            분석 기준: <strong id="cv-source-used">${sourceLabel(context.analysisSource, context.commentsCount || 0)}</strong><br/>
            영상이 바뀌면 CrossView가 자동으로 새 영상을 인식합니다.
          </p>
          <button class="cv-button" id="cv-analyze-btn">다시 분석하기</button>
          <p class="cv-status" id="cv-status">새 영상 인식 완료. 자동 분석을 준비 중입니다.</p>
        </div>

        <div id="cv-result" class="cv-hidden">
          <div class="cv-card">
            <p class="cv-section-title">분석 기준</p>
            <p class="cv-analysis-text" id="cv-source-detail"></p>
          </div>

          <div class="cv-card cv-hidden" id="cv-bias-card">
            <p class="cv-section-title">정치 편향도</p>
            <div class="cv-bias-scale">
              <div class="cv-scale-labels-top">
                <span>좌</span>
                <span>중립</span>
                <span>우</span>
              </div>
              <div class="cv-gradient-bar-wrap">
                <div class="cv-bias-marker" id="cv-bias-marker"></div>
              </div>
              <div class="cv-scale-numbers">
                <span>5</span><span>4</span><span>3</span><span>2</span><span>1</span>
                <span>0</span>
                <span>1</span><span>2</span><span>3</span><span>4</span><span>5</span>
              </div>
            </div>
            <p class="cv-analysis-text" id="cv-bias-text"></p>
          </div>

          <div class="cv-card cv-hidden" id="cv-nonpolitical-card">
            <p class="cv-section-title">정치 편향도</p>
            <p class="cv-analysis-text" id="cv-nonpolitical-text">
              이 영상은 정치·시사 영상으로 강하게 판단되지 않아 정치 성향도 바를 기본 표시하지 않습니다.
            </p>
            <button class="cv-button cv-secondary" id="cv-force-bias-btn">
              정치 성향도 참고로 보기
            </button>
          </div>

          <div class="cv-card">
            <p class="cv-section-title">💬 댓글 흐름</p>
            <p class="cv-analysis-text" id="cv-comment-summary"></p>
            <ul class="cv-text-list" id="cv-comment-warning-list"></ul>
          </div>

          <div class="cv-card">
            <p class="cv-section-title">📌 영상 요약</p>
            <p class="cv-analysis-text" id="cv-summary-text"></p>

            <div class="cv-divider"></div>

            <p class="cv-section-title">주요 주장</p>
            <ul class="cv-text-list" id="cv-main-claims"></ul>

            <p class="cv-section-title">근거 요약</p>
            <p class="cv-analysis-text" id="cv-evidence-summary"></p>

            <p class="cv-section-title">주의해서 볼 표현/구조</p>
            <ul class="cv-text-list" id="cv-caution-points"></ul>
          </div>

          <div class="cv-card">
            <p class="cv-section-title">AI 생성 의심 여부</p>
            <div class="cv-ai-warning low" id="cv-ai-box"></div>
          </div>

          <div class="cv-card">
            <p class="cv-section-title">비슷한 관점의 자료</p>
            <div class="cv-rec-list" id="cv-similar-list"></div>
          </div>

          <div class="cv-card">
            <p class="cv-section-title">다른 관점일 수 있는 자료</p>
            <div class="cv-rec-list" id="cv-opposite-list"></div>
          </div>

          <div class="cv-card">
            <p class="cv-section-title">검증용 영상 / 기사 / AI 답변</p>
            <div class="cv-rec-list" id="cv-verify-list"></div>
          </div>

          <div class="cv-card">
            <p class="cv-section-title">판단 체크리스트</p>
            <div class="cv-checklist" id="cv-checklist"></div>
            <a class="cv-mini-link" href="http://localhost:3000" target="_blank">
              내 시청 편향 리포트 보기
            </a>
          </div>
        </div>
      </div>
    </div>
  `;

  return panel;
}

function showBiasCard(analysis, forced = false) {
  const biasCard = document.querySelector("#cv-bias-card");
  const nonPoliticalCard = document.querySelector("#cv-nonpolitical-card");
  const marker = document.querySelector("#cv-bias-marker");
  const biasText = document.querySelector("#cv-bias-text");

  if (!biasCard || !nonPoliticalCard || !marker || !biasText) return;

  biasCard.classList.remove("cv-hidden");
  nonPoliticalCard.classList.add("cv-hidden");

  const biasPercent = biasToPercent(analysis.biasScore);
  marker.style.left = `${biasPercent}%`;

  const prefix = forced ? "사용자 요청으로 참고 표시 · " : "";
  biasText.textContent = `${prefix}${analysis.biasLabel || "분석 결과 없음"} · ${analysis.biasSummary || ""}`;
}

function updatePanelWithAnalysis(analysis) {
  const result = document.querySelector("#cv-result");

  const summaryText = document.querySelector("#cv-summary-text");
  const mainClaims = document.querySelector("#cv-main-claims");
  const evidenceSummary = document.querySelector("#cv-evidence-summary");
  const cautionPoints = document.querySelector("#cv-caution-points");
  const sourceDetail = document.querySelector("#cv-source-detail");

  const commentSummary = document.querySelector("#cv-comment-summary");
  const commentWarningList = document.querySelector("#cv-comment-warning-list");

  const biasCard = document.querySelector("#cv-bias-card");
  const nonPoliticalCard = document.querySelector("#cv-nonpolitical-card");
  const nonPoliticalText = document.querySelector("#cv-nonpolitical-text");
  const aiBox = document.querySelector("#cv-ai-box");
  const similarList = document.querySelector("#cv-similar-list");
  const oppositeList = document.querySelector("#cv-opposite-list");
  const verifyList = document.querySelector("#cv-verify-list");
  const checklist = document.querySelector("#cv-checklist");
  const forceBiasBtn = document.querySelector("#cv-force-bias-btn");
  const sourceUsed = document.querySelector("#cv-source-used");

  sourceUsed.textContent = sourceLabel(analysis.sourceUsed || "metadata", analysis.commentsCount || 0);

  summaryText.textContent = analysis.summary || "영상 요약 정보가 부족합니다.";
  mainClaims.innerHTML = renderTextList(analysis.mainClaims || []);
  evidenceSummary.textContent = analysis.evidenceSummary || "근거 정보가 충분하지 않습니다.";
  cautionPoints.innerHTML = renderTextList(analysis.cautionPoints || []);

  sourceDetail.textContent =
    `분석 기준: ${analysis.sourceLabel || sourceLabel(analysis.sourceUsed, analysis.commentsCount || 0)} · 댓글 포함: ${analysis.commentsIncluded ? "예" : "아니오"}`;

  commentSummary.textContent =
    `전체 분위기: ${analysis.commentMood || "정보 부족"} · 감정 강도: ${analysis.commentIntensity || "정보 부족"} · 의견 쏠림: ${analysis.commentLeaning || "정보 부족"}`;
  commentWarningList.innerHTML = renderTextList(analysis.commentWarningSignals || []);

  if (analysis.isPolitical) {
    showBiasCard(analysis);
  } else {
    biasCard.classList.add("cv-hidden");
    nonPoliticalCard.classList.remove("cv-hidden");
    nonPoliticalText.textContent =
      analysis.biasSummary ||
      "정치·시사 영상으로 강하게 판단되지 않아 정치 성향도 바를 기본 표시하지 않습니다.";

    forceBiasBtn.onclick = () => showBiasCard(analysis, true);
  }

  aiBox.className = `cv-ai-warning ${aiRiskClass(analysis.aiRisk)}`;
  aiBox.innerHTML = `<strong>${aiRiskTitle(analysis.aiRisk)}</strong><br>${escapeHtml(analysis.aiSummary || "")}`;

  similarList.innerHTML = renderResources(analysis.similarResources || []);
  oppositeList.innerHTML = renderResources(analysis.oppositeResources || []);
  verifyList.innerHTML = renderResources(analysis.verificationResources || []);
  checklist.innerHTML = renderChecklist(analysis.checklist || []);

  result.classList.remove("cv-hidden");
}


function updateCurrentVideoCard(context) {
  const titleEl = document.querySelector("#cv-current-title");
  const channelEl = document.querySelector("#cv-current-channel");
  const sourceUsedEl = document.querySelector("#cv-source-used");

  if (titleEl) {
    titleEl.textContent = context.title || "제목 없음";
  }

  if (channelEl) {
    channelEl.textContent = context.channelName || "채널 정보 없음";
  }

  if (sourceUsedEl) {
    sourceUsedEl.textContent = sourceLabel(
      context.analysisSource || "metadata",
      context.commentsCount || 0
    );
  }
}

async function getFreshYouTubeContextWithRetry() {
  let latestContext = getYouTubeContext();

  for (let i = 0; i < 10; i += 1) {
    await wait(250);

    const nextContext = getYouTubeContext();

    const hasTitle =
      Boolean(nextContext.title) &&
      nextContext.title !== "YouTube" &&
      nextContext.title !== "제목 없음";

    const hasChannel =
      Boolean(nextContext.channelName) &&
      nextContext.channelName !== "채널 정보 없음";

    const sameVideo =
      !latestContext.videoId ||
      !nextContext.videoId ||
      latestContext.videoId === nextContext.videoId;

    latestContext = nextContext;

    if (hasTitle && hasChannel && sameVideo) {
      break;
    }
  }

  return latestContext;
}


async function runAnalysis() {
  const analyzeButton = document.querySelector("#cv-analyze-btn");
  const status = document.querySelector("#cv-status");
  if (!analyzeButton || !status) return;
  if (analysisInFlight) return;

  analysisInFlight = true;
  analyzeButton.disabled = true;

  try {
    status.textContent = "최신 영상 정보를 다시 불러오는 중입니다...";

    const freshContext = await getFreshYouTubeContextWithRetry();
    updateCurrentVideoCard(freshContext);
    status.textContent = `"${freshContext.title || "현재 영상"}"을 스크립트/설명 기반으로 분석하는 중입니다...`;

    const analysis = await requestAnalysis(freshContext);

    updatePanelWithAnalysis(analysis);

    const usedSource = String(analysis.sourceUsed || "");
    status.textContent =
      usedSource.includes("transcript")
        ? "스크립트 기반 분석 완료. 결과는 참고용이며 추가 확인이 필요합니다."
        : "스크립트가 감지되지 않아 설명/메타데이터 중심으로 분석했습니다.";
  } finally {
    analyzeButton.disabled = false;
    analysisInFlight = false;
  }
}

async function injectCrossViewPanel({ autoAnalyze = true } = {}) {
  if (!location.href.includes("youtube.com/watch")) return;

  const secondary =
    document.querySelector("#secondary-inner") ||
    document.querySelector("#secondary");

  if (!secondary) return;

  const existing = document.querySelector("#crossview-panel");
  if (existing) existing.remove();

  const context = getYouTubeContext();
  currentVideoId = context.videoId;

  const panel = buildPanel(context);
  secondary.prepend(panel);

  setTimeout(async () => {
    const refreshedContext = await getFreshYouTubeContextWithRetry();
    updateCurrentVideoCard(refreshedContext);
  }, 500);

  applyTheme(panel);
  updateThemeButton();
  restoreCollapse();

  document.querySelector("#cv-theme-btn").addEventListener("click", (event) => {
    event.stopPropagation();
    cycleTheme();
  });

  document.querySelector("#cv-collapse-btn").addEventListener("click", (event) => {
    event.stopPropagation();
    toggleCollapse();
  });

  document.querySelector("#cv-header").addEventListener("dblclick", () => {
    toggleCollapse();
  });

  document.querySelector("#cv-analyze-btn").addEventListener("click", runAnalysis);

  if (autoAnalyze && currentVideoId !== lastAutoAnalyzedVideoId) {
    lastAutoAnalyzedVideoId = currentVideoId;
    if (autoAnalyzeTimer) clearTimeout(autoAnalyzeTimer);
    autoAnalyzeTimer = setTimeout(runAnalysis, 600);
  }
}

async function boot() {
  loadUserSettings();

  for (let i = 0; i < 24; i += 1) {
    await injectCrossViewPanel({ autoAnalyze: true });
    if (document.querySelector("#crossview-panel")) break;
    await wait(500);
  }
}

boot();

const observer = new MutationObserver(() => {
  const nextVideoId = getVideoId();

  if (location.href !== currentUrl || nextVideoId !== currentVideoId) {
    currentUrl = location.href;
    currentVideoId = nextVideoId;
    lastAutoAnalyzedVideoId = "";
    if (bootTimer) clearTimeout(bootTimer);
    bootTimer = setTimeout(boot, 900);
    return;
  }

  applyTheme();
});

observer.observe(document.body, {
  childList: true,
  subtree: true
});
