import type { AgentRun, FieldDefinitionReview } from "./types";

export const fixtureReviews: FieldDefinitionReview[] = [
  {
    review_id: "review-demo-001",
    run_id: "run-demo-001",
    proposal: {
      proposed_field: {
        key: "military_service_status",
        label: "병역 이행 상태",
        data_type: "enum",
        allowed_values: [
          { value: "completed", label: "이행함" },
          { value: "not_completed", label: "미이행" },
          { value: "exempted", label: "면제" },
        ],
        question: "병역 의무를 이행하셨나요?",
        sensitivity: "medium",
        validity_days: 365,
        review_status: "pending",
      },
      review_required: true,
      review_reason: "기존 canonical field에 없는 신규 자격 조건입니다.",
    },
    status: "pending",
    approved_field: null,
    review_note: null,
    reviewed_at: null,
    evidence: {
      document_name: "demo-notice.hwpx",
      location: "2쪽 지원 대상 표",
      quote: "병역 의무를 이행했거나 면제된 강남구 청년",
      source_url: "https://example.com/demo-policy",
    },
    canonical_candidates: [
      {
        key: "employment_status",
        label: "고용 상태",
        data_type: "enum",
        question: "현재 고용 상태는 무엇인가요?",
        sensitivity: "medium",
        validity_days: 90,
        review_status: "approved",
      },
    ],
  },
];

export const fixtureRun: AgentRun = {
  run_id: "run-demo-001",
  notice_id: "notice-demo-001",
  status: "review_required",
  review_required: true,
  review_reason: "새 동적 필드 정의 검토 필요",
  unresolved_fields: ["military_service_status"],
  policy_id: "demo-policy-v2",
  node_logs: [
    { node: "analyze_html", status: "completed", message: "HTML 핵심 정보가 부족합니다." },
    { node: "route_document_tool", status: "completed", message: "HWPX 분석 도구를 선택했습니다." },
    { node: "analyze_hwpx", status: "completed", message: "지원 대상 표와 근거를 추출했습니다." },
    { node: "validate_evidence", status: "completed", message: "신규 조건은 사람 검토가 필요합니다." },
  ],
};

