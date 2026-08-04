const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";


export function App() {
  return (
    <main>
      <p className="eyebrow">Gangnam Change Agent</p>
      <h1>관리자 통합 화면 준비 완료</h1>
      <p>
        이 앱은 Agent가 만든 검토 대기 정책 패키지를 보여주고 승인 흐름을 연결합니다.
      </p>
      <p className="environment">API: {apiBaseUrl}</p>
    </main>
  );
}
