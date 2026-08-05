import { useState } from "react";

import type { FieldDefinition } from "../profile/dynamicProfile";


interface DynamicQuestionProps {
  field: FieldDefinition;
  reason: "unknown" | "stale";
  onAnswer: (value: unknown) => void;
  pending: boolean;
}


export function DynamicQuestion(props: DynamicQuestionProps) {
  const [input, setInput] = useState("");

  function submitAnswer(value: unknown) {
    props.onAnswer(value);
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
          submitAnswer(props.field.data_type === "number" ? Number(input) : input);
        }}
      >
        <input
          onChange={(event) => setInput(event.target.value)}
          className="answer-input"
          required
          type={props.field.data_type === "number" ? "number" : props.field.data_type}
          value={input}
        />
        <button className="answer-button" disabled={props.pending} type="submit">답변 저장</button>
      </form>
    </section>
  );
}
