from typing import Any

from app.repositories.agent_repository import AgentRepository
from app.services.attachment_archive import PublicAttachmentArchive


class PolicyPublishService:
    def __init__(
        self,
        repository: AgentRepository,
        attachment_archive: PublicAttachmentArchive,
    ) -> None:
        self._repository = repository
        self._attachment_archive = attachment_archive

    def approve(self, policy_id: str) -> dict[str, Any]:
        package, notice = self._repository.get_policy_publish_context(policy_id)
        if notice is not None:
            notice, package = self._attachment_archive.archive_policy_evidence(
                notice,
                package,
            )
            self._repository.save_source_notice(notice)
        return self._repository.approve_policy_package(
            policy_id,
            policy_package=package,
        )
