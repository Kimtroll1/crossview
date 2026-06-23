const DEFAULT_API_BASE = "http://localhost:8000";

chrome.runtime.onInstalled.addListener(() => console.log("CrossView v2.0.0 installed"));

async function readAuth() {
  const data = await chrome.storage.local.get(["crossviewAccessToken", "crossviewUser", "crossviewDeviceId", "crossviewApiBase"]);
  return {
    token: data.crossviewAccessToken || "",
    user: data.crossviewUser || null,
    deviceId: data.crossviewDeviceId || "",
    apiBase: data.crossviewApiBase || DEFAULT_API_BASE
  };
}

async function apiRequest({ url, path, method = "GET", body, auth = true, timeout = 30000 }) {
  const state = await readAuth();
  const target = url || `${state.apiBase}${path}`;
  const headers = { "Content-Type": "application/json" };
  if (auth && state.token) headers.Authorization = `Bearer ${state.token}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(target, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal
    });
    let data = null;
    try { data = await response.json(); } catch { data = { detail: await response.text() }; }
    if (!response.ok) throw new Error(data?.detail || `HTTP ${response.status}`);
    return data;
  } finally {
    clearTimeout(timer);
  }
}

chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
  (async () => {
    if (request.action === "getAuth") {
      sendResponse({ success: true, data: await readAuth() });
      return;
    }
    if (request.action === "logout") {
      await chrome.storage.local.remove(["crossviewAccessToken", "crossviewUser", "crossviewDeviceId"]);
      sendResponse({ success: true });
      return;
    }
    if (request.action === "exchangeCode") {
      const data = await apiRequest({
        url: `${request.apiBase || DEFAULT_API_BASE}/api/auth/extension/exchange`,
        method: "POST",
        auth: false,
        body: { code: request.code, deviceLabel: "Chrome Extension" }
      });
      await chrome.storage.local.set({
        crossviewAccessToken: data.accessToken,
        crossviewUser: data.user,
        crossviewDeviceId: data.deviceId,
        crossviewApiBase: request.apiBase || DEFAULT_API_BASE
      });
      sendResponse({ success: true, data });
      return;
    }
    if (request.action === "apiRequest") {
      const data = await apiRequest(request);
      sendResponse({ success: true, data });
      return;
    }
    sendResponse({ success: false, error: "Unknown CrossView action" });
  })().catch((error) => {
    console.error("CrossView background error", error);
    sendResponse({ success: false, error: error.message || String(error) });
  });
  return true;
});
