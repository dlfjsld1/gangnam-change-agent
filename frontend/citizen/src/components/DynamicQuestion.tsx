import type { FieldDefinition } from "../profile/dynamicProfile";


interface DynamicQuestionProps {
  field: FieldDefinition;
}


export function DynamicQuestion(props: DynamicQuestionProps) {
  return (
    <section>
      <h2>{props.field.label}</h2>
      <p>{props.field.question}</p>
    </section>
  );
}
