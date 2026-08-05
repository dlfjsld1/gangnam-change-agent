import { useEffect, useState } from "react";


const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type PolicyPackage = {
  policy_id: string;
  title: string;
  category: string;
  deadline_at: string | null;
  summary: string;
  changes: Array<{ change_id: string; label: string; impact_hint?: string }>;
  required_actions: Array<{ action_id: string; label: string; priority: number }>;
};


export function App() {
  const [policies, setPolicies] = useState<PolicyPackage[]>([]);
  const [message, setMessage] = useState("승인된 정책을 불러오는 중입니다.");

  useEffect(() => {
    const controller = new AbortController();
    void fetch(`${apiBaseUrl}/api/policy-packages`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
        return response.json() as Promise<PolicyPackage[]>;
      })
      .then((data) => {
        setPolicies(data);
        setMessage(data.length ? "승인된 정책을 불러왔습니다." : "현재 공개된 정책이 없습니다.");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setMessage("백엔드에 연결할 수 없습니다. 실행 상태를 확인해 주세요.");
      });
    return () => controller.abort();
  }, []);

  return (
    <main>
      <p className="eyebrow">Gangnam Change Agent</p>
      <h1>내게 필요한 정책 변경</h1>
      <p className="notice" role="status">{message}</p>
      {policies.map((policy) => (
        <article className="policy" key={policy.policy_id}>
          <small>{policy.category}</small>
          <h2>{policy.title}</h2>
          <p>{policy.summary}</p>
          {policy.changes.map((change) => (
            <div className="change" key={change.change_id}>
              <strong>{change.label}</strong>
              {change.impact_hint && <span>{change.impact_hint}</span>}
            </div>
          ))}
          <h3>해야 할 일</h3>
          <ol>{policy.required_actions.map((action) => <li key={action.action_id}>{action.label}</li>)}</ol>
          {policy.deadline_at && <p className="deadline">신청 마감: {policy.deadline_at}</p>}
        </article>
      ))}
      <p className="environment">API: {apiBaseUrl}</p>
      <small className="privacy">개인정보와 판정 결과는 이 API로 전송하지 않습니다.</small>
    </main>
  );
}
