const history = [
  { title: "부동산 정책을 둘러싼 정치권 공방 분석", bias: "우측 +3", ai: "AI 낮음" },
  { title: "청년 경제 정책, 누구에게 유리한가", bias: "중립 0", ai: "AI 낮음" },
  { title: "국제 정세 위기론을 둘러싼 다른 시각", bias: "좌측 -2", ai: "AI 의심" }
];

const list = document.getElementById("history-list");
list.innerHTML = history.map((item) => `
  <div class="history-item">
    <div>
      <div class="history-title">${item.title}</div>
      <div class="history-meta">CrossView mock 분석 기록</div>
    </div>
    <div class="pill">${item.bias}</div>
    <div class="pill">${item.ai}</div>
  </div>
`).join("");
