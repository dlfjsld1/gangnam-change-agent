import json
import os
from pathlib import Path

from app.tools.document_extractor import (
    ScraplingAttachmentDownloader,
    extract_notice_corpus,
)
from app.tools.openai_ocr import OpenAIImageOcr
from app.tools.scrapling_adapter import fetch_source_notice


NOTICE_URL = (
    "https://www.gangnam.go.kr/center/board/B_000282/1107105/view.do?office=3220141"
)
EXPECTED_TITLE_TERM = "고유가"


def main() -> None:
    _load_local_environment()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required")

    notice = fetch_source_notice(NOTICE_URL)
    corpus = extract_notice_corpus(
        notice,
        ScraplingAttachmentDownloader(),
        image_ocr=OpenAIImageOcr(),
    )
    extraction = corpus.attachment_groups[0].extractions[0]

    print(
        json.dumps(
            {
                "source_id": notice.source_id,
                "title": notice.title,
                "filename": extraction.filename,
                "status": extraction.status,
                "ocr_text": extraction.text,
                "expected_title_term": EXPECTED_TITLE_TERM,
                "expected_term_found": EXPECTED_TITLE_TERM in extraction.text,
                "review_required": corpus.review_required,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _load_local_environment() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", maxsplit=1)
        os.environ.setdefault(name.strip(), value.strip())


if __name__ == "__main__":
    main()
