"use client";

import { useEffect, useState } from "react";
import { AuthGate } from "@/components/AuthGate";
import { HistoryTable } from "@/components/HistoryTable";
import { reportApi, type HistoryResponse } from "@/lib/api";

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryResponse>({ userId: "", items: [] });
  const [error, setError] = useState("");
  useEffect(() => {
    reportApi.history().then(setHistory).catch((err) => setError(err instanceof Error ? err.message : "기록을 불러오지 못했습니다."));
  }, []);
  return (
    <AuthGate>
      <main className="page-shell">
        <section className="report-heading"><div><p className="eyebrow">CROSSVIEW HISTORY</p><h1>영상별 분석 기록</h1><p>정치 방향뿐 아니라 감정·선동, 선택적 근거, 관점 누락, 출처 편중을 영상마다 확인합니다.</p></div><div className="connection-badge online">{history.items.length}개 기록</div></section>
        {error && <div className="error-banner">{error}</div>}
        <section className="panel"><HistoryTable items={history.items} /></section>
      </main>
    </AuthGate>
  );
}
