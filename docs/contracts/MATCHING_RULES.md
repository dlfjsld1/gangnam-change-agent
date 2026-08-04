# 시민 판정 규칙

시민 판정은 기기 안의 결정론적 코드만 수행한다.

## 우선순위

AND:

1. 하나라도 NO면 NO
2. 모두 YES면 YES
3. NO 없이 STALE이 있으면 STALE
4. NO와 STALE 없이 UNKNOWN이 있으면 UNKNOWN

OR:

1. 하나라도 YES면 YES
2. 모두 NO면 NO
3. YES 없이 STALE이 있으면 STALE
4. YES와 STALE 없이 UNKNOWN이 있으면 UNKNOWN

STALE 갱신 질문은 신규 UNKNOWN 질문보다 먼저 표시한다. 이미 NO가 확정된 정책에는 추가 질문을 하지 않는다.

## 질문 선택 규칙

판정 결과를 계산한 뒤 별도의 질문 선택 단계에서 처리한다.

1. NO가 확정되면 질문하지 않는다.
2. STALE 필드가 있으면 갱신 질문을 먼저 선택한다.
3. STALE이 없고 UNKNOWN 필드가 있으면 신규 질문을 선택한다.
4. 한 번에 한 질문만 표시한다.
5. 답변하지 않음을 선택하면 현재 상태를 유지한다.

## MVP 연산자

- equals
- in
- between
- contains
- exists
- AND
- OR
