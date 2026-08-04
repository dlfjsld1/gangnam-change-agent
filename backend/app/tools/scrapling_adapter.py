from typing import Protocol


class NoticeFetcher(Protocol):
    def fetch_html(self, notice_url: str) -> str:
        """Fetch notice HTML through the future Scrapling implementation."""
