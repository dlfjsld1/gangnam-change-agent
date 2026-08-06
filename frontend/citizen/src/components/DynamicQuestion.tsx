import { type FormEvent, useState } from "react";

import type { FieldDefinition } from "../profile/dynamicProfile";

const BUS_STOP_SUGGESTIONS = [
  "강남역.강남역사거리",
  "역삼역.포스코P&S타워",
  "포스코빌딩",
  "한국무역센터.삼성역",
  "코엑스아티움",
  "봉은사.삼성1파출소",
  "강남구청역",
  "강남을지병원",
  "차병원사거리",
  "신사역.푸른저축은행",
  "논현역",
  "학동역",
];

interface DynamicQuestionProps {
  field: FieldDefinition;
  reason: "unknown" | "stale";
  onAnswer: (value: unknown) => void;
  pending: boolean;
}


export function DynamicQuestion(props: DynamicQuestionProps) {
  const [input, setInput] = useState("");
  const [residenceError, setResidenceError] = useState("");
  const [isBusStopSuggestionOpen, setIsBusStopSuggestionOpen] = useState(false);
  const busStopSuggestions = props.field.key === "frequent_bus_stops" && isBusStopSuggestionOpen && input.trim()
    ? BUS_STOP_SUGGESTIONS.filter((stop) => stop.replace(/\s/g, "").includes(input.replace(/\s/g, ""))).slice(0, 5)
    : [];

  function submitAnswer(value: unknown) {
    props.onAnswer(value);
  }

  function submitResidence(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const dongName = input.replace(/\s/g, "").replace(/^강남구/, "");
    const gangnamDongs = [
      "개포동", "논현동", "대치동", "도곡동", "삼성동", "세곡동", "수서동",
      "신사동", "압구정동", "역삼동", "일원동", "청담동", "율현동", "자곡동",
    ];

    if (!gangnamDongs.includes(dongName)) {
      setResidenceError("강남구에 속한 동을 입력해 주세요. 예: 역삼동");
      return;
    }

    setResidenceError("");
    submitAnswer("강남구");
  }

  if (props.field.key === "residence") {
    return (
      <section className="question-card residence-question">
        <h2>살고 있는 동을 선택하세요</h2>
        <p>강남구 어느 동에 거주하시나요?</p>
        <form onSubmit={submitResidence} noValidate>
          <label className="sr-only" htmlFor="residence-dong">살고 있는 동</label>
          <input
            aria-describedby="residence-help residence-error"
            aria-invalid={Boolean(residenceError)}
            className="answer-input"
            id="residence-dong"
            onChange={(event) => {
              setInput(event.target.value);
              if (residenceError) {
                setResidenceError("");
              }
            }}
            placeholder="예: 역삼동"
            required
            type="text"
            value={input}
          />
          <button className="answer-button" disabled={props.pending} type="submit">확인</button>
          <p className="input-help" id="residence-help">강남구에 속한 동만 입력할 수 있어요.</p>
          {residenceError && <p aria-live="polite" className="input-error" id="residence-error">{residenceError}</p>}
        </form>
      </section>
    );
  }

  if (props.field.data_type === "enum" && props.field.allowed_values) {
    return (
      <section className="question-card">
        {props.reason === "stale" && <p className="question-notice">이전에 입력한 정보를 다시 확인해 주세요.</p>}
        <h2>{props.field.label}</h2>
        <p>{props.field.question}</p>
        {props.field.allowed_values.map((option) => (
          <button
            disabled={props.pending}
            className="answer-button"
            key={String(option.value)}
            onClick={() => submitAnswer(option.value)}
            type="button"
          >
            {option.label}
          </button>
        ))}
      </section>
    );
  }

  if (props.field.data_type === "boolean") {
    return (
      <section className="question-card">
        {props.reason === "stale" && <p className="question-notice">이전에 입력한 정보를 다시 확인해 주세요.</p>}
        <h2>{props.field.label}</h2>
        <p>{props.field.question}</p>
        <button className="answer-button" disabled={props.pending} onClick={() => submitAnswer(true)} type="button">
          예
        </button>
        <button className="answer-button" disabled={props.pending} onClick={() => submitAnswer(false)} type="button">
          아니요
        </button>
      </section>
    );
  }

  return (
    <section className="question-card">
      {props.reason === "stale" && <p className="question-notice">이전에 입력한 정보를 다시 확인해 주세요.</p>}
      <h2>{props.field.label}</h2>
      <p>{props.field.question}</p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          const value = props.field.data_type === "number"
            ? Number(input)
            : props.field.data_type === "list"
              ? input.split(",").map((item) => item.trim()).filter(Boolean)
              : input;
          submitAnswer(value);
        }}
      >
        <input
          onChange={(event) => {
            setInput(event.target.value);
            if (props.field.key === "frequent_bus_stops") {
              setIsBusStopSuggestionOpen(true);
            }
          }}
          className="answer-input"
          placeholder={props.field.data_type === "list" ? "예: 강남역.강남역사거리" : undefined}
          required
          type={props.field.data_type === "number" ? "number" : "text"}
          value={input}
        />
        {busStopSuggestions.length > 0 && (
          <div className="bus-stop-suggestions" role="listbox" aria-label="비슷한 정류장">
            <p>비슷한 정류장</p>
            {busStopSuggestions.map((stop) => (
              <button className="bus-stop-suggestion" key={stop} onClick={() => {
                setInput(stop);
                setIsBusStopSuggestionOpen(false);
              }} role="option" type="button">
                {stop}
              </button>
            ))}
          </div>
        )}
        <button className="answer-button" disabled={props.pending} type="submit">답변 저장</button>
        {props.field.data_type === "list" && <p className="input-help">여러 곳이면 쉼표로 구분해 입력해 주세요.</p>}
      </form>
    </section>
  );
}
