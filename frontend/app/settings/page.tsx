"use client";

import { FormEvent, useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { authApi, reportApi, type ReportSettings } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";

const defaults: ReportSettings = {
  enabled: false, cadence: "weekly", timezone: "Asia/Seoul", sendHour: 9, weekday: 0, monthDay: 1,
  emailEnabled: true, emailAddress: "", slackEnabled: false, slackWebhookMasked: "", discordEnabled: false, discordWebhookMasked: "",
};

export default function SettingsPage() {
  const { user } = useAuth();
  const [settings, setSettings] = useState<ReportSettings>(defaults);
  const [slackWebhook, setSlackWebhook] = useState("");
  const [discordWebhook, setDiscordWebhook] = useState("");
  const [linkCode, setLinkCode] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { reportApi.settings().then(setSettings).catch(() => undefined); }, []);

  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setMessage("");
    try {
      const updated = await reportApi.updateSettings({
        enabled: settings.enabled,
        cadence: settings.cadence,
        timezone: settings.timezone,
        sendHour: settings.sendHour,
        weekday: settings.weekday,
        monthDay: settings.monthDay,
        emailEnabled: settings.emailEnabled,
        emailAddress: settings.emailAddress || user?.email || null,
        slackEnabled: settings.slackEnabled,
        slackWebhook: slackWebhook || null,
        discordEnabled: settings.discordEnabled,
        discordWebhook: discordWebhook || null,
      });
      setSettings(updated); setSlackWebhook(""); setDiscordWebhook(""); setMessage("리포트 설정을 저장했습니다.");
    } catch (err) { setMessage(err instanceof Error ? err.message : "설정을 저장하지 못했습니다."); }
    finally { setBusy(false); }
  }

  async function generateCode() {
    try { const result = await authApi.linkCode(); setLinkCode(result.code); setMessage("10분 안에 확장 프로그램에 코드를 입력하세요."); }
    catch (err) { setMessage(err instanceof Error ? err.message : "연결 코드를 만들지 못했습니다."); }
  }

  async function testDelivery() {
    setBusy(true); setMessage("");
    try {
      const results = await reportApi.testDelivery();
      setMessage(results.map((item) => `${item.channel}: ${item.success ? "성공" : `실패 (${item.detail})`}`).join(" · "));
    } catch (err) { setMessage(err instanceof Error ? err.message : "테스트 전송에 실패했습니다."); }
    finally { setBusy(false); }
  }

  return (
    <AuthGate>
      <main className="page-shell settings-page">
        <section className="report-heading"><div><p className="eyebrow">ACCOUNT & DELIVERY</p><h1>계정 연결과 리포트 전송</h1><p>확장 프로그램을 계정에 연결하고, 주간 또는 월간 리포트를 이메일·Slack·Discord로 받을 수 있습니다.</p></div></section>
        {message && <div className="info-banner">{message}</div>}
        <section className="settings-grid">
          <article className="panel">
            <p className="panel-kicker">CHROME EXTENSION</p><h2>확장 프로그램 연결</h2>
            <p className="settings-copy">웹에서 만든 6자리 코드를 유튜브의 CrossView 패널에 입력하면 demo-user 대신 현재 계정으로 기록됩니다.</p>
            <button className="primary-button inline-button" onClick={generateCode}>연결 코드 만들기</button>
            {linkCode && <div className="link-code">{linkCode}</div>}
          </article>
          <form className="panel settings-form" onSubmit={save}>
            <p className="panel-kicker">SCHEDULED REPORT</p><h2>정기 리포트</h2>
            <label className="toggle-line"><input type="checkbox" checked={settings.enabled} onChange={(event) => setSettings({ ...settings, enabled: event.target.checked })} />정기 전송 사용</label>
            <div className="form-two">
              <label>주기<select value={settings.cadence} onChange={(event) => setSettings({ ...settings, cadence: event.target.value as "weekly" | "monthly" })}><option value="weekly">매주</option><option value="monthly">매월</option></select></label>
              <label>시간<select value={settings.sendHour} onChange={(event) => setSettings({ ...settings, sendHour: Number(event.target.value) })}>{Array.from({ length: 24 }, (_, hour) => <option value={hour} key={hour}>{hour}:00</option>)}</select></label>
            </div>
            {settings.cadence === "weekly" ? <label>요일<select value={settings.weekday} onChange={(event) => setSettings({ ...settings, weekday: Number(event.target.value) })}>{["월", "화", "수", "목", "금", "토", "일"].map((day, index) => <option value={index} key={day}>{day}요일</option>)}</select></label> : <label>매월 날짜<input type="number" min={1} max={28} value={settings.monthDay} onChange={(event) => setSettings({ ...settings, monthDay: Number(event.target.value) })} /></label>}
            <label>시간대<input value={settings.timezone} onChange={(event) => setSettings({ ...settings, timezone: event.target.value })} /></label>

            <div className="channel-box">
              <label className="toggle-line"><input type="checkbox" checked={settings.emailEnabled} onChange={(event) => setSettings({ ...settings, emailEnabled: event.target.checked })} />이메일</label>
              <input type="email" placeholder="report@example.com" value={settings.emailAddress || ""} onChange={(event) => setSettings({ ...settings, emailAddress: event.target.value })} />
            </div>
            <div className="channel-box">
              <label className="toggle-line"><input type="checkbox" checked={settings.slackEnabled} onChange={(event) => setSettings({ ...settings, slackEnabled: event.target.checked })} />Slack Incoming Webhook</label>
              <input placeholder={settings.slackWebhookMasked || "https://hooks.slack.com/services/..."} value={slackWebhook} onChange={(event) => setSlackWebhook(event.target.value)} />
            </div>
            <div className="channel-box">
              <label className="toggle-line"><input type="checkbox" checked={settings.discordEnabled} onChange={(event) => setSettings({ ...settings, discordEnabled: event.target.checked })} />Discord Webhook</label>
              <input placeholder={settings.discordWebhookMasked || "https://discord.com/api/webhooks/..."} value={discordWebhook} onChange={(event) => setDiscordWebhook(event.target.value)} />
            </div>
            <div className="settings-actions"><button className="primary-button" disabled={busy}>{busy ? "저장 중…" : "설정 저장"}</button><button type="button" className="secondary-button" onClick={testDelivery} disabled={busy}>테스트 전송</button></div>
          </form>
        </section>
      </main>
    </AuthGate>
  );
}
