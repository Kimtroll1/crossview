const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const TOKEN_KEY = "crossview_access_token";

export type User = {
  id: number;
  externalId: string;
  email?: string | null;
  name?: string | null;
  avatarUrl?: string | null;
  authProvider: string;
  timezone: string;
};

export type AuthResponse = { accessToken: string; tokenType: string; user: User };
export type SignalDetail = { score: number; label: string; reasons: string[] };
export type BiasSignals = {
  emotionalManipulation: SignalDetail;
  evidenceSelection: SignalDetail;
  viewpointOmission: SignalDetail;
  sourceConcentration: SignalDetail;
};
export type CommentFlow = { opinionConcentration: number; emotionIntensity: number; summary: string; sampleSize: number };
export type Resource = {
  id?: number | null;
  type: string;
  category: string;
  title: string;
  source: string;
  url: string;
  summary: string;
  publishedAt: string;
  thumbnailUrl: string;
  stanceScore: number;
  stanceLabel: string;
  relevanceScore: number;
  credibilityScore: number;
  recommendationReason: string;
  keyPoint: string;
  verifiedUrl: boolean;
};
export type Report = {
  userId: string;
  period: "weekly" | "monthly";
  periodStart: string;
  periodEnd: string;
  totalVideos: number;
  politicalVideos: number;
  averageBiasScore: number;
  averageBiasConfidence: number;
  leftRatio: number;
  neutralRatio: number;
  rightRatio: number;
  aiRiskCount: number;
  aiRiskRatio: number;
  topTopics: string[];
  suggestion: string;
  biasDistribution: { left: number; neutral: number; right: number };
  signalAverages: {
    emotionalManipulation: number;
    evidenceSelection: number;
    viewpointOmission: number;
    sourceConcentration: number;
    opinionConcentration: number;
    commentEmotionIntensity: number;
  };
  resourceClicks: number;
  alternativeResourceClicks: number;
  alternativeExplorationRate: number;
  recommendedResources: Resource[];
};
export type HistoryItem = {
  watchedAt: string;
  videoId: string;
  title: string;
  channelName: string;
  url: string;
  isPolitical: boolean;
  biasScore: number;
  biasLabel: string;
  biasConfidence: number;
  biasCriteria: string[];
  biasSignals: BiasSignals;
  commentFlow: CommentFlow;
  aiRisk: "low" | "medium" | "high";
  issue: string;
  summary: string;
};
export type HistoryResponse = { userId: string; items: HistoryItem[] };
export type ReportSettings = {
  enabled: boolean;
  cadence: "weekly" | "monthly";
  timezone: string;
  sendHour: number;
  weekday: number;
  monthDay: number;
  emailEnabled: boolean;
  emailAddress?: string | null;
  slackEnabled: boolean;
  slackWebhookMasked: string;
  discordEnabled: boolean;
  discordWebhookMasked: string;
};

export function getToken() {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(TOKEN_KEY) || "";
}
export function setToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

export async function apiFetch<T>(path: string, options: RequestInit = {}, auth = true): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body) headers.set("Content-Type", "application/json");
  if (auth) {
    const token = getToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers, cache: "no-store" });
  if (!response.ok) {
    let detail = `CrossView API ${response.status}`;
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const authApi = {
  register: (body: { email: string; password: string; name: string }) => apiFetch<AuthResponse>("/api/auth/register", { method: "POST", body: JSON.stringify(body) }, false),
  login: (body: { email: string; password: string }) => apiFetch<AuthResponse>("/api/auth/login", { method: "POST", body: JSON.stringify(body) }, false),
  google: (credential: string) => apiFetch<AuthResponse>("/api/auth/google", { method: "POST", body: JSON.stringify({ credential }) }, false),
  me: () => apiFetch<User>("/api/auth/me"),
  linkCode: () => apiFetch<{ code: string; expiresInSeconds: number }>("/api/auth/link-code", { method: "POST" }),
};

export const reportApi = {
  report: (period: "weekly" | "monthly") => apiFetch<Report>(`/api/reports/me?period=${period}`),
  history: () => apiFetch<HistoryResponse>("/api/history/me"),
  settings: () => apiFetch<ReportSettings>("/api/settings/report"),
  updateSettings: (body: Record<string, unknown>) => apiFetch<ReportSettings>("/api/settings/report", { method: "PUT", body: JSON.stringify(body) }),
  testDelivery: () => apiFetch<Array<{ channel: string; success: boolean; detail: string }>>("/api/settings/report/test", { method: "POST" }),
  recordClick: (resourceId: number) => apiFetch<{ ok: boolean }>(`/api/resources/${resourceId}/click`, { method: "POST" }),
};
