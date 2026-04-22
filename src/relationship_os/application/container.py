import asyncio
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine

from relationship_os.application.action_service import ActionService
from relationship_os.application.audit_service import AuditService
from relationship_os.application.entity_service import EntityService
from relationship_os.application.evaluation_service import EvaluationService
from relationship_os.application.factual_memory_backends import (
    Mem0FactualMemoryBackend,
    NativeFactualMemoryBackend,
)
from relationship_os.application.job_executor import JobExecutor
from relationship_os.application.job_service import JobService
from relationship_os.application.llm import LiteLLMClient, MiniMaxClient, MockLLMClient
from relationship_os.application.memory_index import build_memory_index
from relationship_os.application.memory_service import MemoryService
from relationship_os.application.policy_registry import (
    PolicyRegistry,
    configure_default_policy_registry,
)
from relationship_os.application.proactive_followup_dispatcher import (
    ProactiveFollowupDispatcher,
)
from relationship_os.application.proactive_followup_service import (
    ProactiveFollowupService,
)
from relationship_os.application.projectors import (
    ActionStateProjector,
    EntityDriveProjector,
    EntityPersonaProjector,
    InnerMonologueBufferProjector,
    SelfNarrativeProjector,
    SelfStateProjector,
    SessionMemoryProjector,
    SessionRuntimeProjector,
    SessionSnapshotProjector,
    SessionTemporalKGProjector,
    SessionTranscriptProjector,
    SocialWorldProjector,
    UserIndexProjector,
    WorldStateProjector,
)
from relationship_os.application.runtime_events import RuntimeEventBroker
from relationship_os.application.runtime_service import RuntimeService
from relationship_os.application.scenario_evaluation_service import ScenarioEvaluationService
from relationship_os.application.scenario_evaluation_service.simulation import (
    LongitudinalSimulationService,
)
from relationship_os.application.stream_service import StreamService
from relationship_os.application.user_service import UserService
from relationship_os.core.config import Settings
from relationship_os.core.logging import get_logger
from relationship_os.domain.event_store import EventStore
from relationship_os.domain.llm import LLMClient
from relationship_os.domain.projectors import VersionedProjectorRegistry
from relationship_os.infrastructure.db.engine import build_async_engine
from relationship_os.infrastructure.event_store.memory import InMemoryEventStore
from relationship_os.infrastructure.event_store.postgres import PostgresEventStore

_shutdown_logger = get_logger("relationship_os.container")


@dataclass(slots=True)
class RuntimeContainer:
    settings: Settings
    event_store: EventStore
    stream_service: StreamService
    evaluation_service: EvaluationService
    scenario_evaluation_service: ScenarioEvaluationService
    longitudinal_simulation_service: LongitudinalSimulationService
    audit_service: AuditService
    memory_service: MemoryService
    proactive_followup_service: ProactiveFollowupService
    proactive_followup_dispatcher: ProactiveFollowupDispatcher
    job_service: JobService
    job_executor: JobExecutor
    llm_client: LLMClient
    runtime_service: RuntimeService
    projector_registry: VersionedProjectorRegistry
    runtime_event_broker: RuntimeEventBroker
    policy_registry: PolicyRegistry
    action_service: ActionService | None = None
    user_service: UserService | None = None
    entity_service: EntityService | None = None
    database_engine: AsyncEngine | None = None

    async def shutdown(self) -> None:
        results = await asyncio.gather(
            self.proactive_followup_dispatcher.shutdown(),
            self.job_executor.shutdown(),
            self.runtime_event_broker.shutdown(),
            return_exceptions=True,
        )
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                _shutdown_logger.error(
                    "shutdown_component_failed",
                    component=("dispatcher", "job_executor", "broker")[idx],
                    error=str(result),
                    error_type=type(result).__name__,
                )
        if self.database_engine is not None:
            await self.database_engine.dispose()


def build_container(settings: Settings) -> RuntimeContainer:
    policy_registry = PolicyRegistry(root_path=settings.policy_root_path)
    configure_default_policy_registry(
        registry=policy_registry,
        runtime_profile=settings.runtime_profile,
    )
    database_engine: AsyncEngine | None = None
    if settings.event_store_backend == "postgres":
        database_engine = build_async_engine(settings.require_database_url())
        event_store: EventStore = PostgresEventStore(database_engine)
    else:
        event_store = InMemoryEventStore()

    projector_registry = VersionedProjectorRegistry()
    runtime_event_broker = RuntimeEventBroker()
    projector_registry.register(InnerMonologueBufferProjector())
    projector_registry.register(EntityDriveProjector())
    projector_registry.register(EntityPersonaProjector())
    projector_registry.register(SelfNarrativeProjector())
    projector_registry.register(SessionMemoryProjector())
    projector_registry.register(SessionTranscriptProjector())
    projector_registry.register(SessionRuntimeProjector())
    projector_registry.register(SessionSnapshotProjector())
    projector_registry.register(SessionTemporalKGProjector())
    projector_registry.register(SocialWorldProjector())
    projector_registry.register(UserIndexProjector())
    projector_registry.register(WorldStateProjector())
    projector_registry.register(ActionStateProjector())
    projector_registry.register(SelfStateProjector())
    stream_service = StreamService(
        event_store=event_store,
        projector_registry=projector_registry,
        runtime_event_broker=runtime_event_broker,
    )
    evaluation_service = EvaluationService(stream_service=stream_service)
    audit_service = AuditService(
        stream_service=stream_service,
        runtime_projector_version=settings.default_projector_version,
    )
    memory_index = build_memory_index(
        enabled=settings.memory_index_enabled,
        root_path=settings.memory_index_store_path,
        text_provider=settings.memory_index_text_provider,
        text_model=settings.memory_index_text_model,
        text_api_key=settings.memory_index_text_api_key or settings.llm_api_key,
        text_api_base=settings.memory_index_text_api_base or settings.llm_api_base,
        text_dimensions=settings.memory_index_text_dimensions,
        multimodal_provider=settings.memory_index_multimodal_provider,
        multimodal_model=settings.memory_index_multimodal_model,
        multimodal_api_key=settings.memory_index_multimodal_api_key or settings.llm_api_key,
        multimodal_api_base=settings.memory_index_multimodal_api_base or settings.llm_api_base,
        reranker_enabled=settings.memory_index_reranker_enabled,
        reranker_provider=settings.memory_index_reranker_provider,
        reranker_model=settings.memory_index_reranker_model,
        reranker_api_key=settings.memory_index_reranker_api_key or settings.llm_api_key,
        reranker_api_base=settings.memory_index_reranker_api_base or settings.llm_api_base,
    )
    mem0_factual_backend = None
    if settings.fact_memory_backend in {"mem0_shadow", "mem0_primary"}:
        mem0_factual_backend = Mem0FactualMemoryBackend(
            qdrant_path=settings.mem0_qdrant_path,
            history_db_path=settings.mem0_history_db_path,
            embed_model=settings.mem0_embed_model,
            retrieval_limit=settings.mem0_retrieval_limit,
            llm_model=settings.llm_model,
            llm_api_base=settings.llm_api_base,
            llm_api_key=settings.llm_api_key,
        )
    memory_service = MemoryService(
        stream_service=stream_service,
        memory_index=memory_index,
        memory_index_enabled=settings.memory_index_enabled,
        policy_registry=policy_registry,
        runtime_profile=settings.runtime_profile,
        factual_backend_mode=settings.fact_memory_backend,
        native_factual_backend=NativeFactualMemoryBackend(
            memory_index=memory_index,
            enabled=settings.memory_index_enabled,
        ),
        mem0_factual_backend=mem0_factual_backend,
    )
    user_service = UserService(stream_service=stream_service)
    persona_text = ""
    persona_path = Path(settings.entity_persona_seed_file or settings.persona_file)
    if persona_path.is_file():
        persona_text = persona_path.read_text(encoding="utf-8").strip()
    entity_service = EntityService(
        stream_service=stream_service,
        entity_id=settings.entity_id,
        entity_name=settings.entity_name,
        persona_seed_text=persona_text,
        policy_registry=policy_registry,
        runtime_profile=settings.runtime_profile,
    )
    action_service = ActionService(
        stream_service=stream_service,
        policy_registry=policy_registry,
        runtime_profile=settings.runtime_profile,
    )
    proactive_followup_service = ProactiveFollowupService(
        stream_service=stream_service,
        runtime_projector_version=settings.default_projector_version,
    )
    job_service = JobService(
        stream_service=stream_service,
        evaluation_service=evaluation_service,
        default_max_attempts=settings.job_max_attempts,
        runtime_projector_version=settings.default_projector_version,
        entity_service=entity_service,
    )
    job_executor = JobExecutor(
        job_service=job_service,
        worker_id=settings.job_worker_id,
        poll_interval_seconds=settings.job_poll_interval_seconds,
        claim_ttl_seconds=settings.job_claim_ttl_seconds,
        heartbeat_interval_seconds=settings.job_heartbeat_interval_seconds,
    )
    if settings.llm_backend == "litellm":
        llm_client = LiteLLMClient(
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            api_base=settings.llm_api_base,
            api_key=settings.llm_api_key,
        )
    elif settings.llm_backend == "minimax":
        llm_client = MiniMaxClient(
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            api_base=settings.llm_api_base,
            api_key=settings.llm_api_key,
        )
    else:
        llm_client = MockLLMClient(model=settings.llm_model)
    runtime_service = RuntimeService(
        stream_service=stream_service,
        memory_service=memory_service,
        evaluation_service=evaluation_service,
        llm_client=llm_client,
        llm_model=settings.llm_model,
        llm_temperature=settings.llm_temperature,
        runtime_quality_doctor_interval_turns=(settings.runtime_quality_doctor_interval_turns),
        runtime_quality_doctor_window_turns=settings.runtime_quality_doctor_window_turns,
        runtime_projector_version=settings.default_projector_version,
        persona_text=persona_text,
        search_enabled=settings.search_enabled,
        user_service=user_service,
        entity_service=entity_service,
        entity_id=settings.entity_id,
        entity_name=settings.entity_name,
        runtime_profile=settings.runtime_profile,
        action_service=action_service,
        edge_allow_cloud_escalation=settings.edge_allow_cloud_escalation,
        edge_target_latency_seconds=settings.edge_target_latency_seconds,
        edge_hard_latency_seconds=settings.edge_hard_latency_seconds,
        edge_max_memory_items=settings.edge_max_memory_items,
        edge_max_prompt_tokens=settings.edge_max_prompt_tokens,
        edge_max_completion_tokens=settings.edge_max_completion_tokens,
    )
    proactive_followup_dispatcher = ProactiveFollowupDispatcher(
        proactive_followup_service=proactive_followup_service,
        runtime_service=runtime_service,
        worker_id=settings.proactive_followup_worker_id,
        poll_interval_seconds=settings.proactive_followup_poll_interval_seconds,
        max_dispatch_per_cycle=settings.proactive_followup_max_dispatch_per_cycle,
    )
    scenario_evaluation_service = ScenarioEvaluationService(
        stream_service=stream_service,
        runtime_service=runtime_service,
        evaluation_service=evaluation_service,
        audit_service=audit_service,
        job_service=job_service,
        job_executor=job_executor,
        projector_registry=projector_registry,
    )
    longitudinal_simulation_service = LongitudinalSimulationService(
        runtime_service=runtime_service,
        scenario_evaluation_service=scenario_evaluation_service,
    )
    return RuntimeContainer(
        settings=settings,
        event_store=event_store,
        stream_service=stream_service,
        evaluation_service=evaluation_service,
        scenario_evaluation_service=scenario_evaluation_service,
        longitudinal_simulation_service=longitudinal_simulation_service,
        audit_service=audit_service,
        memory_service=memory_service,
        proactive_followup_service=proactive_followup_service,
        proactive_followup_dispatcher=proactive_followup_dispatcher,
        job_service=job_service,
        job_executor=job_executor,
        llm_client=llm_client,
        runtime_service=runtime_service,
        projector_registry=projector_registry,
        runtime_event_broker=runtime_event_broker,
        policy_registry=policy_registry,
        action_service=action_service,
        user_service=user_service,
        entity_service=entity_service,
        database_engine=database_engine,
    )
