from __future__ import annotations

from dataclasses import asdict
from hashlib import sha1
from typing import Any

from relationship_os.application.policy_registry import (
    PolicyRegistry,
    get_default_compiled_policy_set,
)
from relationship_os.application.stream_service import StreamService
from relationship_os.domain.contracts.autonomy import (
    ActionIntent,
    ActionPlan,
    ExecutionGateDecision,
    ExecutionReceipt,
)
from relationship_os.domain.event_types import (
    ENTITY_ACTION_EXECUTION_DECIDED,
    ENTITY_ACTION_EXECUTION_RECORDED,
    ENTITY_ACTION_INTENT_UPDATED,
    ENTITY_ACTION_PLANNED,
    ENTITY_GOAL_UPDATED,
    SYSTEM_ACTION_SURFACE_UPDATED,
    SYSTEM_WORLD_STATE_UPDATED,
)
from relationship_os.domain.events import NewEvent, utc_now


def _entity_stream_id(entity_id: str) -> str:
    return f"entity:{entity_id}"


def _stable_id(*parts: str) -> str:
    digest = sha1("::".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


class _BaseActionAdapter:
    name = "base"

    def execute(self, *, plan: ActionPlan) -> dict[str, Any]:
        return {
            "status": "executed",
            "surface": plan.surface,
            "adapter": self.name,
            "result": {
                "action_type": plan.action_type,
                "target": plan.target,
                "payload": dict(plan.payload),
            },
        }


class _DeviceActionAdapter(_BaseActionAdapter):
    name = "device_adapter"

    def execute(self, *, plan: ActionPlan) -> dict[str, Any]:
        artifact_id = f"artifact-{_stable_id(plan.action_id, plan.action_type, plan.target)}"
        if plan.action_type == "create_reminder":
            result = {
                "action_type": plan.action_type,
                "target": plan.target,
                "payload": dict(plan.payload),
                "artifact_id": artifact_id,
                "artifact_kind": "reminder",
                "label": "提醒已排进设备待办",
            }
        elif plan.action_type == "create_task":
            result = {
                "action_type": plan.action_type,
                "target": plan.target,
                "payload": dict(plan.payload),
                "artifact_id": artifact_id,
                "artifact_kind": "task",
                "label": "待办已进入行动队列",
            }
        elif plan.action_type == "schedule_block":
            result = {
                "action_type": plan.action_type,
                "target": plan.target,
                "payload": dict(plan.payload),
                "artifact_id": artifact_id,
                "artifact_kind": "calendar_block",
                "label": "时间块已加入日程意图",
            }
        elif plan.action_type == "organize_files":
            result = {
                "action_type": plan.action_type,
                "target": plan.target,
                "payload": dict(plan.payload),
                "artifact_id": artifact_id,
                "artifact_kind": "workspace_cleanup",
                "label": "文件整理已加入环境动作",
                "touched_areas": ["workspace", "files"],
            }
        else:
            return super().execute(plan=plan)
        return {
            "status": "executed",
            "surface": plan.surface,
            "adapter": self.name,
            "result": result,
        }


class _CommunicationActionAdapter(_BaseActionAdapter):
    name = "communication_adapter"

    def execute(self, *, plan: ActionPlan) -> dict[str, Any]:
        draft_id = f"draft-{_stable_id(plan.action_id, plan.target, plan.surface)}"
        preview = str(plan.payload.get("user_message_excerpt") or plan.why_now or "")[:120]
        return {
            "status": "executed",
            "surface": plan.surface,
            "adapter": self.name,
            "result": {
                "action_type": plan.action_type,
                "target": plan.target,
                "payload": dict(plan.payload),
                "artifact_id": draft_id,
                "artifact_kind": "draft",
                "channel": "email" if plan.action_type == "draft_email" else "direct_message",
                "preview": preview,
            },
        }


class ActionService:
    def __init__(
        self,
        *,
        stream_service: StreamService,
        policy_registry: PolicyRegistry | None = None,
        runtime_profile: str = "default",
    ) -> None:
        self._stream = stream_service
        self._policy_registry = policy_registry
        self._runtime_profile = runtime_profile or "default"
        self._adapters = {
            "device": _DeviceActionAdapter(),
            "communication": _CommunicationActionAdapter(),
        }

    def _compiled_policy_set(self, *, archetype: str = "default") -> Any | None:
        if self._policy_registry is not None:
            return self._policy_registry.compile_policy_set(
                runtime_profile=self._runtime_profile,
                archetype=archetype or "default",
            )
        return get_default_compiled_policy_set(
            runtime_profile=self._runtime_profile,
            archetype=archetype or "default",
        )

    def _action_policy(self, *, archetype: str = "default") -> dict[str, Any]:
        compiled = self._compiled_policy_set(archetype=archetype)
        if compiled is None:
            return {}
        return dict(compiled.persona_policy.get("action_policy") or {})

    async def get_action_state(self, *, entity_id: str) -> dict[str, Any]:
        projection = await self._stream.project_stream(
            stream_id=_entity_stream_id(entity_id),
            projector_name="entity-actions",
            projector_version="v1",
        )
        return projection.get("state", {})

    async def plan_and_execute(
        self,
        *,
        entity_id: str,
        user_id: str | None,
        session_id: str,
        user_message: str,
        assistant_response: str | None,
        archetype: str,
        goal_state: dict[str, Any],
        world_state: dict[str, Any],
    ) -> dict[str, Any]:
        action_policy = self._action_policy(archetype=archetype)
        max_actions = max(0, int(action_policy.get("max_actions_per_turn", 0) or 0))
        if max_actions <= 0:
            return {"intents": [], "plans": [], "receipts": []}

        intents: list[ActionIntent] = []
        plans: list[ActionPlan] = []
        gates: list[ExecutionGateDecision] = []
        receipts: list[ExecutionReceipt] = []
        active_goals = [
            dict(item)
            for item in list(goal_state.get("active_goals") or [])
            if str(item.get("status") or "active") in {"active", "proposed"}
        ]
        if not active_goals:
            return {"intents": [], "plans": [], "receipts": []}

        surface_by_action_type = dict(action_policy.get("surface_by_action_type") or {})
        direct_risks = {
            str(value) for value in list(action_policy.get("direct_execution_risk_levels") or [])
        }
        confirmation_risks = {
            str(value) for value in list(action_policy.get("confirmation_risk_levels") or [])
        }
        confirmation_action_types = {
            str(value)
            for value in list(action_policy.get("confirmation_required_action_types") or [])
        }

        now = utc_now().isoformat()
        updated_goals = [dict(item) for item in active_goals]
        for goal in updated_goals[:max_actions]:
            action_type = str(goal.get("action_type") or "").strip()
            if not action_type:
                continue
            target = str(goal.get("target") or user_id or "personal_workspace")
            surface = str(surface_by_action_type.get(action_type, "device") or "device")
            risk_level = str(goal.get("risk_level") or "low")
            reversibility = str(goal.get("reversibility") or "high")
            why_now = str(goal.get("why_now") or "goal_active_and_ready")
            payload = dict(goal.get("payload") or {})
            payload.setdefault("goal_title", str(goal.get("title") or ""))
            intent = ActionIntent(
                intent_id=f"intent-{_stable_id(goal.get('goal_id', ''), session_id, action_type)}",
                goal_id=str(goal.get("goal_id") or ""),
                action_type=action_type,
                target=target,
                why_now=why_now,
                payload=payload,
                risk_level=risk_level,
                reversibility=reversibility,
                surface=surface,
            )
            plan = ActionPlan(
                action_id=f"action-{_stable_id(intent.intent_id, target, surface)}",
                intent_id=intent.intent_id,
                goal_id=intent.goal_id,
                action_type=action_type,
                target=target,
                payload=payload,
                why_now=why_now,
                risk_level=risk_level,
                reversibility=reversibility,
                surface=surface,
            )
            gate = self._build_gate_decision(
                plan=plan,
                direct_risks=direct_risks,
                confirmation_risks=confirmation_risks,
                confirmation_action_types=confirmation_action_types,
            )
            receipt = self._execute_plan(plan=plan, gate=gate)
            if receipt.status == "executed":
                goal["status"] = "completed"
                goal["updated_at"] = now
                goal["result"] = dict(receipt.result)
            intents.append(intent)
            plans.append(plan)
            gates.append(gate)
            receipts.append(receipt)

        if not plans:
            return {"intents": [], "plans": [], "receipts": []}

        updated_goal_state = self._build_goal_state_after_actions(
            goal_state=goal_state,
            active_goals=updated_goals,
            receipts=receipts,
            occurred_at=now,
        )
        updated_world_state = self._build_world_state_after_actions(
            world_state=world_state,
            receipts=receipts,
            occurred_at=now,
        )
        action_surface = dict(updated_world_state.get("action_surface") or {})

        events: list[NewEvent] = []
        for intent in intents:
            events.append(
                NewEvent(
                    event_type=ENTITY_ACTION_INTENT_UPDATED,
                    payload={
                        "entity_id": entity_id,
                        "user_id": user_id,
                        "session_id": session_id,
                        "occurred_at": now,
                        "assistant_response_excerpt": (assistant_response or "")[:280],
                        "intent": asdict(intent),
                    },
                )
            )
        for plan, gate, receipt in zip(plans, gates, receipts, strict=False):
            events.extend(
                [
                    NewEvent(
                        event_type=ENTITY_ACTION_PLANNED,
                        payload={
                            "entity_id": entity_id,
                            "user_id": user_id,
                            "session_id": session_id,
                            "occurred_at": now,
                            "plan": asdict(plan),
                        },
                    ),
                    NewEvent(
                        event_type=ENTITY_ACTION_EXECUTION_DECIDED,
                        payload={
                            "entity_id": entity_id,
                            "user_id": user_id,
                            "session_id": session_id,
                            "occurred_at": now,
                            "gate": asdict(gate),
                        },
                    ),
                    NewEvent(
                        event_type=ENTITY_ACTION_EXECUTION_RECORDED,
                        payload={
                            "entity_id": entity_id,
                            "user_id": user_id,
                            "session_id": session_id,
                            "occurred_at": now,
                            "receipt": asdict(receipt),
                        },
                    ),
                ]
            )

        events.extend(
            [
                NewEvent(
                    event_type=ENTITY_GOAL_UPDATED,
                    payload={
                        "entity_id": entity_id,
                        "occurred_at": now,
                        "source": "action_execution",
                        **updated_goal_state,
                    },
                ),
                NewEvent(
                    event_type=SYSTEM_WORLD_STATE_UPDATED,
                    payload={
                        "entity_id": entity_id,
                        "occurred_at": now,
                        "source": "action_execution",
                        "time_of_day": updated_world_state.get("time_of_day"),
                        "circadian_phase": updated_world_state.get("circadian_phase"),
                        "sleep_pressure": updated_world_state.get("sleep_pressure"),
                        "device": updated_world_state.get("device"),
                        "communication": updated_world_state.get("communication"),
                        "tasks": updated_world_state.get("tasks"),
                    },
                ),
                NewEvent(
                    event_type=SYSTEM_ACTION_SURFACE_UPDATED,
                    payload={
                        "entity_id": entity_id,
                        "occurred_at": now,
                        "source": "action_execution",
                        "action_surface": action_surface,
                    },
                ),
            ]
        )
        await self._stream.append_events(
            stream_id=_entity_stream_id(entity_id),
            expected_version=None,
            events=events,
        )
        return {
            "intents": [asdict(item) for item in intents],
            "plans": [asdict(item) for item in plans],
            "receipts": [asdict(item) for item in receipts],
        }

    def _build_gate_decision(
        self,
        *,
        plan: ActionPlan,
        direct_risks: set[str],
        confirmation_risks: set[str],
        confirmation_action_types: set[str],
    ) -> ExecutionGateDecision:
        confirmation_required = (
            plan.risk_level in confirmation_risks or plan.action_type in confirmation_action_types
        )
        if confirmation_required:
            return ExecutionGateDecision(
                action_id=plan.action_id,
                approved=False,
                status="pending_confirmation",
                reason="risk_requires_confirmation",
                confirmation_required=True,
                risk_level=plan.risk_level,
            )
        approved = plan.risk_level in direct_risks
        return ExecutionGateDecision(
            action_id=plan.action_id,
            approved=approved,
            status="approved" if approved else "withheld",
            reason="direct_execution_allowed" if approved else "risk_not_allowed",
            confirmation_required=False,
            risk_level=plan.risk_level,
        )

    def _execute_plan(
        self,
        *,
        plan: ActionPlan,
        gate: ExecutionGateDecision,
    ) -> ExecutionReceipt:
        now = utc_now().isoformat()
        if not gate.approved:
            return ExecutionReceipt(
                action_id=plan.action_id,
                status=gate.status,
                surface=plan.surface,
                adapter="execution_gate",
                result={"reason": gate.reason},
                occurred_at=now,
            )
        adapter = self._adapters.get(plan.surface, self._adapters["device"])
        payload = adapter.execute(plan=plan)
        return ExecutionReceipt(
            action_id=plan.action_id,
            status=str(payload.get("status") or "executed"),
            surface=str(payload.get("surface") or plan.surface),
            adapter=str(payload.get("adapter") or adapter.name),
            result=dict(payload.get("result") or {}),
            occurred_at=now,
        )

    def _build_goal_state_after_actions(
        self,
        *,
        goal_state: dict[str, Any],
        active_goals: list[dict[str, Any]],
        receipts: list[ExecutionReceipt],
        occurred_at: str,
    ) -> dict[str, Any]:
        open_goals = [
            item
            for item in active_goals
            if str(item.get("status") or "active") not in {"completed", "cancelled"}
        ]
        digest_titles = [
            str(item.get("title") or "") for item in open_goals[:3] if item.get("title")
        ]
        if not digest_titles and receipts:
            digest_titles = [
                str(receipt.result.get("action_type") or "") for receipt in receipts[:2]
            ]
        goal_digest = " | ".join(filter(None, digest_titles))
        return {
            "latent_drives": list(goal_state.get("latent_drives") or []),
            "active_goals": active_goals,
            "unresolved_tensions": list(goal_state.get("unresolved_tensions") or []),
            "goal_digest": goal_digest,
            "updated_at": occurred_at,
        }

    def _build_world_state_after_actions(
        self,
        *,
        world_state: dict[str, Any],
        receipts: list[ExecutionReceipt],
        occurred_at: str,
    ) -> dict[str, Any]:
        updated = {
            "time_of_day": world_state.get("time_of_day", "unknown"),
            "circadian_phase": world_state.get("circadian_phase", "day"),
            "sleep_pressure": float(world_state.get("sleep_pressure", 0.36) or 0.36),
            "device": dict(world_state.get("device") or {}),
            "communication": dict(world_state.get("communication") or {}),
            "tasks": dict(world_state.get("tasks") or {}),
            "action_surface": dict(world_state.get("action_surface") or {}),
            "environment_appraisal": dict(world_state.get("environment_appraisal") or {}),
            "updated_at": occurred_at,
        }
        executed = [receipt for receipt in receipts if receipt.status == "executed"]
        pending_confirmations = [
            receipt for receipt in receipts if receipt.status == "pending_confirmation"
        ]
        if executed:
            task_increment = 0
            outbox_increment = 0
            recent_execution_types: list[str] = []
            for receipt in executed:
                action_type = str(receipt.result.get("action_type") or "")
                recent_execution_types.append(action_type)
                if action_type in {
                    "create_reminder",
                    "create_task",
                    "schedule_block",
                    "organize_files",
                }:
                    task_increment += 1
                if action_type in {"draft_message", "draft_email", "relationship_ping"}:
                    outbox_increment += 1
            updated["tasks"]["pending_count"] = (
                int(updated["tasks"].get("pending_count", 0) or 0) + task_increment
            )
            updated["tasks"]["due_soon_count"] = int(
                updated["tasks"].get("due_soon_count", 0) or 0
            ) + len(
                [
                    receipt
                    for receipt in executed
                    if str(receipt.result.get("action_type") or "")
                    in {"create_reminder", "schedule_block"}
                ]
            )
            updated["communication"]["outbox_count"] = (
                int(updated["communication"].get("outbox_count", 0) or 0) + outbox_increment
            )
            updated["communication"]["pending_replies"] = max(
                0,
                int(updated["communication"].get("pending_replies", 0) or 0) - outbox_increment,
            )
            updated["communication"]["last_outbound_channel"] = (
                "email"
                if any(
                    str(receipt.result.get("action_type") or "") == "draft_email"
                    for receipt in executed
                )
                else "direct_message"
                if outbox_increment
                else updated["communication"].get("last_outbound_channel")
            )
            updated["device"]["current_surface"] = (
                "mail"
                if outbox_increment
                else "files"
                if task_increment
                else updated["device"].get("current_surface", "chat")
            )
            updated["device"]["output_load"] = round(
                min(1.0, float(updated["device"].get("output_load", 0.2) or 0.2) + 0.08),
                3,
            )
            updated["action_surface"]["recent_execution_types"] = recent_execution_types[-5:]
        updated["action_surface"]["pending_confirmation_count"] = len(pending_confirmations)
        updated["action_surface"]["last_action_at"] = occurred_at
        updated["environment_appraisal"]["focus"] = (
            "communication"
            if int(updated["communication"].get("outbox_count", 0) or 0) > 0
            else "organization"
            if int(updated["tasks"].get("pending_count", 0) or 0) > 0
            else updated["environment_appraisal"].get("focus", "steady")
        )
        return updated
