# 공개 근거 첨부 프론트 통합 계약

이 문서는 승인 전 비공개 검토 첨부와 승인된 공개 근거 첨부를 관리자 화면과 시민 PWA에서 표시하는 최소 계약이다.
첨부 archive 결정은 `docs/DECISIONS.md`의 D-008과 D-009, endpoint 상세는
`docs/contracts/api.md`를 따른다.

## 공통 원칙

- 브라우저가 S3에 파일을 직접 업로드하지 않는다.
- 공고 수집 후 백엔드는 공식 첨부를 비공개 `review-attachments/`에 저장한다.
- 정책 최종 승인 시 백엔드가 evidence로 사용한 첨부만 `public-attachments/`에 공개 archive한다.
- 시민 프로필과 시민별 판정 결과는 첨부 버킷에 저장하지 않는다.
- 승인 전 Admin은 단기 presigned `review_url`을 사용하고, 승인 후에는 고정 공개 URL을 사용한다.
- 파일명만으로 개인정보 가능성이 감지되면 백엔드는 공개 archive와 Publish를 409로
  차단한다.

## 관리자 화면

관리자 담당과 Codex는 다음 순서로 구현한다.

1. `GET /api/agent-runs?review_required=true`로 검토할 실행을 찾는다.
2. `GET /api/admin/agent-runs/{run_id}`로 실행 상세를 가져온다.
3. `source_notice.source_url`을 원본 공고 링크로 표시한다.
4. `source_notice.attachments`에서 파일명과 `review_url ?? public_url ?? url` 링크를 표시한다.
5. FieldDefinitionReview 승인·수정·반려를 완료한다.
6. `POST /api/policy-packages/{policy_id}/approve`로 정책을 최종 승인한다.
7. 승인 성공 후 실행 상세를 다시 조회해 attachment `public_url`과 PolicyPackage
   evidence `source_url`을 갱신한다.

관리자 실행 상세의 attachment 예시는 다음과 같다.

```json
{
  "filename": "지원사업 안내.pdf",
  "url": "https://www.gangnam.go.kr/original.pdf",
  "file_type": "pdf",
  "storage_key": "public-attachments/gangnam_public_notice/61922/abc123-지원사업 안내.pdf",
  "review_url": "https://s3.ap-northeast-2.amazonaws.com/...signed...",
  "public_url": "https://files.example.com/public-attachments/...",
  "sha256": "..."
}
```

S3 검토 저장소가 설정된 환경에서는 승인 전 `storage_key`, `review_url`, `sha256`이
존재하고 `public_url`은 null이다. `review_url`은 만료되므로 화면을 다시 열 때 실행
상세를 재조회한다. 로컬 fallback에서는 이 값들이 null일 수 있다.

Policy Publish가 409를 반환하면 필드 검토 미완료 또는 개인정보 가능 첨부 차단 사유를
관리자에게 보여준다. 503이면 첨부 다운로드 또는 S3 업로드 실패이므로 정책은 공개되지
않으며 재시도 상태를 표시한다.

## 시민 PWA

시민 PWA는 별도 S3 API를 호출하지 않는다.

1. 기존 `GET /api/policy-packages` 또는 상세 endpoint로 승인 정책을 가져온다.
2. `policy.evidence[].source_url`을 근거 첨부 또는 공식 원문 링크로 렌더링한다.
3. 링크는 새 탭에서 열고 `rel="noopener noreferrer"`를 적용한다.
4. evidence 링크가 없어도 정책 판정과 IndexedDB 로컬 프로필 흐름은 계속 동작해야 한다.

승인 후 evidence `source_url`은 S3 또는 CloudFront 고정 URL일 수 있고, HTML 본문 근거는
기존 공식 공고 URL일 수 있다. PWA는 URL의 host를 가정하지 않고 그대로 사용한다.

## 담당별 완료 조건

관리자 화면:

- 검토 상세에서 원본 공고와 첨부 링크를 볼 수 있다.
- 정책 승인 후 공개 URL로 표시가 갱신된다.
- 409와 503 오류가 사용자에게 구분되어 보인다.

시민 PWA:

- 승인 정책의 evidence 링크를 열 수 있다.
- 첨부 링크 처리가 시민 프로필을 서버로 전송하지 않는다.
- 첨부 접근 실패가 로컬 정책 판정을 막지 않는다.

각 담당은 구현과 실제 build 결과를 자신의 Work log에 기록한다.
