"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { BiasChart } from "@/components/BiasChart";
import { HistoryTable } from "@/components/HistoryTable";
import { RadarProfile } from "@/components/RadarProfile";
import { ReportCard } from "@/components/ReportCard";
import { ResourceCards } from "@/components/ResourceCards";
import { reportApi, type HistoryResponse, type Report } from "@/lib/api";

function biasText(score: number) {
  if (score < -1) return `진보 ${Math.abs(score).toFixed(1)}`;
  if (score > 1) return `보수 +${score.toFixed(1)}`;
  return "중립에 가까움";
}

export default function DashboardPage() {
  const [period, setPeriod] = useState<"weekly" | "monthly">("weekly");
  const [report, setReport] = useState<Report | null>(null);
  const [history, setHistory] = useState<HistoryResponse>({ userId: "", items: [] });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([reportApi.report(period), reportApi.history()])
      .then(([nextReport, nextHistory]) => { if (active) { setReport(nextReport); setHistory(nextHistory); setError(""); } })
      .catch((err) => { if (active) setError(err instanceof Error ? err.message : "리포트를 불러오지 못했습니다."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [period]);

  const radarValues = useMemo(() => report ? [
    { label: "정치 편향", value: Math.min(5, Math.abs(report.averageBiasScore)) },
    { label: "감정 자극", value: report.signalAverages.emotionalManipulation },
    { label: "근거 선택", value: report.signalAverages.evidenceSelection },
    { label: "관점 누락", value: report.signalAverages.viewpointOmission },
    { label: "출처 편중", value: report.signalAverages.sourceConcentration },
  ] : [], [report]);

  return (
    <AuthGate>
      <main className="page-shell">
        <section className="report-heading">
          <div>
            <p className="eyebrow">PERSONAL MEDIA REPORT</p>
            <h1>내 미디어 소비 리포트</h1>
            <p>정치 방향과 편향 신호는 확정 판정이 아니라 영상 표현, 근거 구성, 관점 누락을 바탕으로 한 AI 추정치입니다.</p>
          </div>
          <div className="period-switch">
            <button className={period === "weekly" ? "active" : ""} onClick={() => setPeriod("weekly")}>최근 7일</button>
            <button className={period === "monthly" ? "active" : ""} onClick={() => setPeriod("monthly")}>최근 30일</button>
          </div>
        </section>

        {loading && <div className="empty-state">리포트를 계산하는 중입니다.</div>}
        {error && <div className="error-banner">{error}</div>}
        {report && !loading && <>
          <section className="metric-grid">
            <ReportCard eyebrow="분석 영상" value={`${report.totalVideos}개`} description={`정치·시사 ${report.politicalVideos}개 포함`} tone="blue" />
            <ReportCard eyebrow="평균 정치 방향" value={biasText(report.averageBiasScore)} description="진보 -5 / 중립 0 / 보수 +5" />
            <ReportCard eyebrow="다른 관점 탐색률" value={`${report.alternativeExplorationRate}%`} description={`${report.alternativeResourceClicks}개 자료 열람`} tone="blue" />
            <ReportCard eyebrow="AI 생성 의심" value={`${report.aiRiskCount}개`} description={`전체의 ${report.aiRiskRatio}% · medium/high 기준`} tone="amber" />
          </section>

          <section className="dashboard-grid report-visual-grid">
            <article className="panel wide-panel">
              <div className="panel-heading"><div><p className="panel-kicker">정치 방향</p><h2>진보·중립·보수 시청 분포</h2></div><span>{report.politicalVideos}개 기준</span></div>
              <BiasChart leftRatio={report.leftRatio} neutralRatio={report.neutralRatio} rightRatio={report.rightRatio} />
            </article>
            <article className="panel radar-panel">
              <div><p className="panel-kicker">편향 신호</p><h2>미디어 소비 프로필</h2></div>
              <RadarProfile values={radarValues} />
              <p className="chart-note">바깥쪽일수록 해당 편향 신호에 더 자주 노출됐다는 뜻입니다.</p>
            </article>
          </section>

          <section className="signal-summary-grid">
            {[
              ["🔥", "감정·선동", report.signalAverages.emotionalManipulation],
              ["🔍", "선택적 근거", report.signalAverages.evidenceSelection],
              ["👥", "관점 누락", report.signalAverages.viewpointOmission],
              ["📚", "출처 편중", report.signalAverages.sourceConcentration],
              ["💬", "댓글 의견 쏠림", report.signalAverages.opinionConcentration],
              ["⚡", "댓글 감정 강도", report.signalAverages.commentEmotionIntensity],
            ].map(([icon, label, value]) => (
              <article className="signal-stat" key={String(label)}>
                <span>{String(icon)}</span><div><strong>{String(label)}</strong><b>{Number(value).toFixed(1)} / 5</b><i><em style={{ width: `${Number(value) / 5 * 100}%` }} /></i></div>
              </article>
            ))}
          </section>

          <section className="dashboard-grid">
            <article className="panel">
              <p className="panel-kicker">주요 주제</p><h2>이번 기간 관심 이슈</h2>
              {report.topTopics.length ? <div className="topic-cloud">{report.topTopics.map((topic, index) => <span key={topic}>{index + 1}. {topic}</span>)}</div> : <div className="empty-inline">분석 기록이 쌓이면 주제가 표시됩니다.</div>}
            </article>
            <article className="panel suggestion-panel compact-suggestion">
              <p className="panel-kicker">CROSSVIEW 제안</p><h2>균형을 위한 다음 행동</h2><p>{report.suggestion}</p>
            </article>
          </section>

          <section className="panel recent-panel">
            <div className="panel-heading"><div><p className="panel-kicker">다관점 탐색</p><h2>이번 기간에 함께 볼 자료</h2></div><Link className="text-link" href="/explore">전체 보기 →</Link></div>
            <ResourceCards resources={report.recommendedResources} limit={4} />
          </section>

          <section className="panel recent-panel">
            <div className="panel-heading"><div><p className="panel-kicker">최근 기록</p><h2>최근 분석한 영상</h2></div><Link className="text-link" href="/history">전체 보기 →</Link></div>
            <HistoryTable items={history.items} compact />
          </section>
        </>}
      </main>
    </AuthGate>
  );
}
