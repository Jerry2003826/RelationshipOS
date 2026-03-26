import asyncio
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from relationship_os.application.audit_service import AuditService
from relationship_os.application.evaluation_service import EvaluationService
from relationship_os.application.job_executor import JobExecutor
from relationship_os.application.job_service import JobService
from relationship_os.application.llm import LiteLLMClient, MockLLMClient
from relationship_os.application.memory_service import MemoryService
from relationship_os.application.proactive_followup_dispatcher import (
    ProactiveFollowupDispatcher,
)
from relationship_os.application.proactive_followup_service import (
    ProactiveFollowupService,
)
from relationship_os.application.projectors import (
    InnerMonologueBufferProjector,
    SessionMemoryProjector,
    SessionRuntimeProjector,
    SessionSnapshotProjector,
    SessionTemporalKGProjector,
    SessionTranscriptProjector,
)
from relationship_os.application.runtime_events import RuntimeEventBroker
from relationship_os.application.runtime_service import RuntimeService
from relationship_os.application.scenario_evaluation_service import ScenarioEvaluationService
from relationship_os.application.stream_service import StreamService
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
    database_engine: AsyncEngine | None = None
    if settings.event_store_backend == "postgres":
        database_engine = build_async_engine(settings.require_database_url())
        event_store: EventStore = PostgresEventStore(database_engine)
    else:
        event_store = InMemoryEventStore()

    projector_registry = VersionedProjectorRegistry()
    runtime_event_broker = RuntimeEventBroker()
    projector_registry.register(InnerMonologueBufferProjector())
    projector_registry.register(SessionMemoryProjector())
    projector_registry.register(SessionTranscriptProjector())
    projector_registry.register(SessionRuntimeProjector())
    projector_registry.register(SessionSnapshotProjector())
    projector_registry.register(SessionTemporalKGProjector())
    stream_service = StreamService(
        event_store=event_store,
        projector_registry=projector_registry,
        runtime_event_broker=runtime_event_broker,
    )
    evaluation_service = EvaluationService(stream_service=stream_service)
    audit_service = AuditService(stream_service=stream_service)
    memory_service = MemoryService(stream_service=stream_service)
    proactive_followup_service = ProactiveFollowupService(stream_service=stream_service)
    job_service = JobService(
        stream_service=stream_service,
        evaluation_service=evaluation_service,
        default_max_attempts=settings.job_max_attempts,
    )
    job_executor = JobExecutor(
        job_service=job_service,
        worker_id=settings.job_worker_id,
        poll_interval_seconds=settings.job_poll_interval_seconds,
        claim_ttl_seconds=settings.job_claim_ttl_seconds,
        heartbeat_interval_seconds=settings.job_heartbeat_interval_seconds,
    )
    if settings.llm_backend in {"litellm", "minimax"}:
        llm_client = LiteLLMClient(
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
        runtime_quality_doctor_interval_turns=(
            settings.runtime_quality_doctor_interval_turns
        ),
        runtime_quality_doctor_window_turns=settings.runtime_quality_doctor_window_turns,
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
    return RuntimeContainer(
        settings=settings,
        event_store=event_store,
        stream_service=stream_service,
        evaluation_service=evaluation_service,
        scenario_evaluation_service=scenario_evaluation_service,
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
        database_engine=database_engine,
    )
