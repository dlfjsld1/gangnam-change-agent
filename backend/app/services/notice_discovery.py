from collections.abc import Callable

from app.repositories.agent_repository import AgentRepository
from app.schemas.discovery_api import NoticeDiscoveryResponse
from app.services.agent_execution import AgentExecutionService
from app.tools.scrapling_adapter import discover_source_detail_urls


DetailUrlDiscoverer = Callable[[], list[str]]


class NoticeDiscoveryService:
    def __init__(
        self,
        repository: AgentRepository,
        execution_service: AgentExecutionService,
        *,
        discover_urls: DetailUrlDiscoverer = discover_source_detail_urls,
    ) -> None:
        self._repository = repository
        self._execution_service = execution_service
        self._discover_urls = discover_urls

    def run(self, *, max_new_notices: int = 1) -> NoticeDiscoveryResponse:
        try:
            urls = self._discover_urls()
        except Exception as error:
            raise NoticeDiscoveryUnavailable(
                "Gangnam notice boards are unavailable."
            ) from error

        already_processed_count = 0
        processed_runs = []
        for url in urls:
            if self._repository.has_source_url(url):
                already_processed_count += 1
                continue
            response = self._execution_service.run(url)
            processed_runs.append(response.agent_run)
            if len(processed_runs) >= max_new_notices:
                break

        return NoticeDiscoveryResponse(
            discovered_count=len(urls),
            already_processed_count=already_processed_count,
            processed_runs=processed_runs,
        )


class NoticeDiscoveryUnavailable(RuntimeError):
    pass
