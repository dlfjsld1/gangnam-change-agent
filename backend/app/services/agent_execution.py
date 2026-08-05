from collections.abc import Callable
from typing import Protocol
from uuid import uuid4

from app.agent.graph import build_change_agent_graph, create_default_runtime
from app.agent.state import ChangeAgentRuntime, ChangeAgentState
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent_api import AgentRunResponse
from app.schemas.agent_run import AgentRun
from app.schemas.field_definition import FieldDefinition
from app.schemas.source_notice import SourceNotice
from app.services.field_registry import FieldRegistry


class InvokableGraph(Protocol):
    def invoke(self, state: ChangeAgentState) -> dict[str, object]: ...


RuntimeFactory = Callable[[FieldRegistry], ChangeAgentRuntime]
GraphBuilder = Callable[[ChangeAgentRuntime], InvokableGraph]


class PreviousPolicyNotFound(LookupError):
    pass


class AgentExecutionService:
    def __init__(
        self,
        repository: AgentRepository,
        *,
        runtime_factory: RuntimeFactory = create_default_runtime,
        graph_builder: GraphBuilder = build_change_agent_graph,
    ) -> None:
        self._repository = repository
        self._runtime_factory = runtime_factory
        self._graph_builder = graph_builder

    def run(
        self,
        notice_url: str,
        *,
        previous_policy_id: str | None = None,
    ) -> AgentRunResponse:
        previous_policy = self._load_previous_policy(previous_policy_id)
        field_registry = FieldRegistry(self._approved_definitions(previous_policy))
        graph = self._graph_builder(self._runtime_factory(field_registry))
        result = graph.invoke(
            {
                "run_id": f"run-{uuid4().hex}",
                "notice_url": notice_url,
                "previous_policy_package": previous_policy,
            }
        )
        agent_run = result.get("agent_run")
        if not isinstance(agent_run, AgentRun):
            raise RuntimeError("Agent graph returned no AgentRun")

        policy_package = result.get("policy_package")
        field_proposals = result.get("field_proposals", [])
        field_reviews = result.get("field_reviews", [])
        evidence_issues = result.get("evidence_issues", [])
        notice = result.get("notice")
        if notice is not None and not isinstance(notice, SourceNotice):
            raise RuntimeError("Agent graph returned an invalid SourceNotice")
        response = AgentRunResponse(
            agent_run=agent_run,
            policy_package=policy_package,
            field_definition_proposals=field_proposals,
            field_definition_reviews=field_reviews,
            evidence_issues=evidence_issues,
        )
        self._repository.save_execution(
            response.agent_run,
            notice=notice,
            policy_package=response.policy_package,
            field_proposals=response.field_definition_proposals,
            field_reviews=response.field_definition_reviews,
        )
        return response

    def _load_previous_policy(
        self,
        previous_policy_id: str | None,
    ) -> dict[str, object] | None:
        if previous_policy_id is None:
            return None
        package = self._repository.get_approved_policy_package(previous_policy_id)
        if package is None:
            raise PreviousPolicyNotFound(previous_policy_id)
        return package

    def _approved_definitions(
        self,
        previous_policy: dict[str, object] | None,
    ) -> list[FieldDefinition]:
        definitions = {
            definition.key: definition
            for definition in self._repository.list_approved_field_definitions()
        }
        if previous_policy is not None:
            for payload in previous_policy.get("required_profile_fields", []):
                if not isinstance(payload, dict):
                    continue
                definition = FieldDefinition.model_validate(payload)
                if definition.review_status == "approved":
                    definitions[definition.key] = definition
        return list(definitions.values())
