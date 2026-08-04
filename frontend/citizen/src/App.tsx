const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";


export function App() {
  return (
    <main>
      <p className="eyebrow">Gangnam Change Agent</p>
      <h1>시민용 PWA 준비 완료</h1>
      <p>
        이 앱은 승인된 정책 패키지를 받아 기기 안에서 시민별 결과를 표시합니다.
      </p>
      <p className="environment">API: {apiBaseUrl}</p>
    </main>
  );
}
