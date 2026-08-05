from collections.abc import Iterable
from datetime import date
from pathlib import PurePosixPath
import re
from typing import Protocol
from urllib.parse import parse_qs, urljoin, urlparse

from scrapling.fetchers import Fetcher
from scrapling.parser import Selector

from app.schemas.source_notice import SourceAttachment, SourceBoard, SourceNotice


ALLOWED_SOURCE_HOSTS = {"gangnam.go.kr", "www.gangnam.go.kr"}
DEFAULT_TIMEOUT_SECONDS = 30
SOURCE_LIST_URLS = (
    "https://www.gangnam.go.kr/notice/list.do?mid=ID05_040201",
    ("https://www.gangnam.go.kr/notice/list.do?gubunfield=05&mid=ID05_040202"),
    (
        "https://www.gangnam.go.kr/center/board/B_000282/list.do"
        "?mid=MC110301&office=3220047"
    ),
)


class NoticeParseError(ValueError):
    pass


class NoticeFetcher(Protocol):
    def fetch(self, notice_url: str) -> Selector:
        """Fetch one public Gangnam page as a Scrapling selector."""


class ScraplingNoticeFetcher:
    def fetch(self, notice_url: str) -> Selector:
        _validate_source_url(notice_url)
        return Fetcher.get(
            notice_url,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            headers={
                "User-Agent": (
                    "GangnamChangeAgentMVP/0.1 (+hackathon; public-notice-research)"
                )
            },
        )


def discover_detail_urls(page: Selector, list_url: str) -> list[str]:
    _validate_source_url(list_url)
    discovered_urls: list[str] = []
    seen_urls: set[str] = set()

    for href in page.css("a::attr(href)").getall():
        candidate = urljoin(list_url, str(href))
        if not _is_supported_detail_url(candidate) or candidate in seen_urls:
            continue
        seen_urls.add(candidate)
        discovered_urls.append(candidate)

    return discovered_urls


def discover_source_detail_urls(
    fetcher: NoticeFetcher | None = None,
    list_urls: tuple[str, ...] = SOURCE_LIST_URLS,
) -> list[str]:
    active_fetcher = fetcher or ScraplingNoticeFetcher()
    discovered_urls: list[str] = []
    seen_urls: set[str] = set()
    for list_url in list_urls:
        page = active_fetcher.fetch(list_url)
        for detail_url in discover_detail_urls(page, list_url):
            if detail_url in seen_urls:
                continue
            seen_urls.add(detail_url)
            discovered_urls.append(detail_url)
    return discovered_urls


def parse_source_notice(page: Selector, source_url: str) -> SourceNotice:
    _validate_source_url(source_url)
    parsed_url = urlparse(source_url)

    if parsed_url.path == "/notice/view.do":
        return _parse_integrated_notice(page, source_url)
    if "/center/board/B_000282/" in parsed_url.path:
        return _parse_center_news(page, source_url)

    raise NoticeParseError(f"Unsupported Gangnam detail URL: {source_url}")


def fetch_source_notice(
    source_url: str,
    fetcher: NoticeFetcher | None = None,
) -> SourceNotice:
    active_fetcher = fetcher or ScraplingNoticeFetcher()
    return parse_source_notice(active_fetcher.fetch(source_url), source_url)


def _parse_integrated_notice(page: Selector, source_url: str) -> SourceNotice:
    title_parts = _clean_texts(page.css(".post-title::text").getall())
    title = title_parts[0] if title_parts else ""
    info = _first_text(page, ".post-info span::text")
    published_at, department = _parse_notice_info(info)
    body_text = _descendant_text(page, ".post-content")
    source_id = _notice_management_number(source_url)

    if not title or not body_text:
        raise NoticeParseError("Integrated notice is missing title or body text.")

    return SourceNotice(
        source_id=source_id,
        source_board=_integrated_board(source_url),
        source_url=source_url,
        title=title,
        published_at=published_at,
        department=department,
        body_text=body_text,
        attachments=_attachments(
            page.css(".bbs-view-file a[href]"),
            source_url,
        ),
    )


def _parse_center_news(page: Selector, source_url: str) -> SourceNotice:
    title = _first_text(page, ".bbs-view_head .title::text")
    published_at = _parse_date(_first_text(page, ".bbs-view_head .date::text"))
    body_text = _descendant_text(page, ".bbs-view_cont .group")
    source_id = _center_post_id(source_url)

    if not title or not body_text:
        raise NoticeParseError("Center news is missing title or body text.")

    return SourceNotice(
        source_id=source_id,
        source_board="gangnam_center_news",
        source_url=source_url,
        title=title,
        published_at=published_at,
        department=None,
        body_text=body_text,
        attachments=_attachments(
            page.css(".bbs-view_file li > a[href]"),
            source_url,
        ),
    )


def _attachments(
    links: Iterable[Selector],
    source_url: str,
) -> list[SourceAttachment]:
    attachments: list[SourceAttachment] = []

    for link in links:
        href = str(link.attrib.get("href", "")).strip()
        if not href or "preview.do" in href:
            continue
        filename = _attachment_filename(link)
        if not filename:
            continue
        attachments.append(
            SourceAttachment(
                filename=filename,
                url=urljoin(source_url, href),
                file_type=_file_type(filename),
            )
        )

    return attachments


def _attachment_filename(link: Selector) -> str:
    image_alts = _clean_texts(link.css("img::attr(alt)").getall())
    if image_alts:
        return image_alts[0]

    text_parts = _clean_texts(link.xpath(".//text()").getall())
    if not text_parts:
        return ""
    filename_match = re.match(
        r"(.+?\.(?:hwpx|pdf|hwp|png|jpe?g|gif|bmp|tiff?|webp))\b",
        text_parts[0],
        re.IGNORECASE,
    )
    return filename_match.group(1) if filename_match else text_parts[0]


def _descendant_text(page: Selector, selector: str) -> str:
    elements = page.css(selector)
    if not elements:
        return ""
    return " ".join(_clean_texts(elements[0].xpath(".//text()").getall()))


def _first_text(page: Selector, selector: str) -> str:
    texts = _clean_texts(page.css(selector).getall())
    return texts[0] if texts else ""


def _clean_texts(values: Iterable[object]) -> list[str]:
    return [cleaned for value in values if (cleaned := " ".join(str(value).split()))]


def _parse_notice_info(info: str) -> tuple[date, str | None]:
    parts = [part.strip() for part in info.split("|", maxsplit=1)]
    published_at = _parse_date(parts[0])
    department = parts[1] if len(parts) == 2 and parts[1] else None
    return published_at, department


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise NoticeParseError(
            f"Invalid or missing publication date: {value}"
        ) from error


def _notice_management_number(source_url: str) -> str:
    values = parse_qs(urlparse(source_url).query).get("not_ancmt_mgt_no", [])
    if not values or not values[0]:
        raise NoticeParseError("Notice URL is missing not_ancmt_mgt_no.")
    return values[0]


def _center_post_id(source_url: str) -> str:
    path_parts = PurePosixPath(urlparse(source_url).path).parts
    try:
        board_index = path_parts.index("B_000282")
        post_id = path_parts[board_index + 1]
    except (ValueError, IndexError) as error:
        raise NoticeParseError("Center news URL is missing its post ID.") from error
    if not post_id.isdigit():
        raise NoticeParseError("Center news post ID must be numeric.")
    return post_id


def _integrated_board(source_url: str) -> SourceBoard:
    mid = parse_qs(urlparse(source_url).query).get("mid", [""])[0]
    if mid == "ID05_040202":
        return "gangnam_job_notice"
    return "gangnam_public_notice"


def _file_type(filename: str) -> str:
    suffix = PurePosixPath(filename.lower()).suffix.lstrip(".")
    if suffix in {"png", "jpg", "jpeg", "gif", "bmp", "tif", "tiff", "webp"}:
        return "image"
    return suffix if suffix in {"hwpx", "pdf", "hwp"} else "other"


def _validate_source_url(source_url: str) -> None:
    parsed_url = urlparse(source_url)
    if parsed_url.scheme != "https" or parsed_url.hostname not in ALLOWED_SOURCE_HOSTS:
        raise ValueError(f"Unapproved source URL: {source_url}")


def _is_supported_detail_url(source_url: str) -> bool:
    parsed_url = urlparse(source_url)
    if parsed_url.hostname not in ALLOWED_SOURCE_HOSTS:
        return False
    if parsed_url.path == "/notice/view.do":
        return "not_ancmt_mgt_no" in parse_qs(parsed_url.query)
    return "/center/board/B_000282/" in parsed_url.path and parsed_url.path.endswith(
        "/view.do"
    )
