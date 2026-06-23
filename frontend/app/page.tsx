import Link from "next/link";

export default function HomePage() {
  return (
    <main className="page-shell landing">
      <section className="landing-hero">
        <div>
          <p className="eyebrow">CROSSVIEW · MULTI-PERSPECTIVE MEDIA LITERACY</p>
          <h1>어느 쪽인지보다,<br />어떻게 편향되는지 봅니다.</h1>
          <p className="hero-copy">유튜브 영상의 정치 방향, 감정·선동, 선택적 근거, 관점 누락, 출처 편중을 시각화하고 실제 다른 관점 영상·기사·공식 자료를 연결합니다.</p>
          <div className="hero-actions"><Link className="primary-button" href="/login">계정 만들기</Link><Link className="secondary-button" href="/dashboard">개인 리포트 보기</Link></div>
        </div>
        <aside className="hero-panel">
          <p>CrossView 2.0</p>
          <ol><li><span>1</span>편향 신호를 한눈에 시각화</li><li><span>2</span>실제 다관점 자료 직접 연결</li><li><span>3</span>사용자별 주간·월간 리포트</li><li><span>4</span>이메일·Slack·Discord 전송</li></ol>
        </aside>
      </section>
    </main>
  );
}
