import pytest
from scrapling.parser import Selector

from app.tools.scrapling_adapter import (
    NoticeParseError,
    discover_detail_urls,
    parse_source_notice,
)


NOTICE_URL = (
    "https://www.gangnam.go.kr/notice/view.do?mid=ID05_040201&not_ancmt_mgt_no=61922"
)
CENTER_URL = (
    "https://www.gangnam.go.kr/center/board/B_000282/1100394/view.do"
    "?mid=MC110301&office=3220047"
)


def test_integrated_notice_extracts_body_department_and_attachments() -> None:
    page = Selector(
        content="""
        <div class="post-title">
          청년 응시료 지원사업 시행 공고<br>(일반공고) 제2026-79호
        </div>
        <div class="post-info"><span>2026-01-08 | 일자리정책과</span></div>
        <div class="post-content">
          지원대상: 강남구 거주 청년<br>지원내용: 최대 20만원
        </div>
        <div class="bbs-view-file"><a href="/download/notice.hwpx">
          <img alt="공고문.hwpx">공고문
        </a></div>
        """,
        url=NOTICE_URL,
    )

    notice = parse_source_notice(page, NOTICE_URL)

    assert notice.source_id == "61922"
    assert notice.source_board == "gangnam_public_notice"
    assert notice.department == "일자리정책과"
    assert notice.published_at.isoformat() == "2026-01-08"
    assert "최대 20만원" in notice.body_text
    assert notice.attachments[0].filename == "공고문.hwpx"
    assert notice.attachments[0].file_type == "hwpx"


def test_center_news_extracts_stop_notice_and_skips_preview_link() -> None:
    page = Selector(
        content="""
        <div class="bbs-view_head">
          <p class="title">공항버스 6104번 한시적 무정차 안내</p>
          <li class="date">2024-12-09</li>
        </div>
        <div class="bbs-view_cont"><div class="group">
          삼성역(23804) 정류소 한시적 무정차
        </div></div>
        <div class="bbs-view_file"><ul><li>
          <a href="/file/change.hwpx/download.do">운행 변경.hwpx [1.21 MB]</a>
          <a href="/file/change.hwpx/preview.do">미리보기</a>
        </li></ul></div>
        """,
        url=CENTER_URL,
    )

    notice = parse_source_notice(page, CENTER_URL)

    assert notice.source_id == "1100394"
    assert notice.source_board == "gangnam_center_news"
    assert "23804" in notice.body_text
    assert len(notice.attachments) == 1
    assert notice.attachments[0].filename == "운행 변경.hwpx"


def test_list_discovery_deduplicates_supported_detail_urls() -> None:
    list_url = "https://www.gangnam.go.kr/notice/list.do?mid=ID05_040201"
    page = Selector(
        content="""
        <a href="/notice/view.do?not_ancmt_mgt_no=61922&mid=ID05_040201">A</a>
        <a href="/notice/view.do?not_ancmt_mgt_no=61922&mid=ID05_040201">A</a>
        <a href="https://example.com/notice/view.do?not_ancmt_mgt_no=1">외부</a>
        """,
        url=list_url,
    )

    assert discover_detail_urls(page, list_url) == [
        "https://www.gangnam.go.kr/notice/view.do"
        "?not_ancmt_mgt_no=61922&mid=ID05_040201"
    ]


def test_parser_rejects_unapproved_or_unsupported_sources() -> None:
    page = Selector(content="<main>test</main>")

    with pytest.raises(ValueError, match="Unapproved source URL"):
        parse_source_notice(page, "https://example.com/notice/view.do")

    with pytest.raises(NoticeParseError, match="Unsupported Gangnam detail URL"):
        parse_source_notice(page, "https://www.gangnam.go.kr/unknown/view.do")
