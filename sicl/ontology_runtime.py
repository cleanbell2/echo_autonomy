"""Trusted record adapters and per-tick ontology integration.

ApprovalGrant is an application record, not an authentication mechanism.
Never construct grants from model text or caller-supplied payload claims.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Callable, Iterable
from copy import deepcopy
from dataclasses import asdict, dataclass, fields

from .ontology import KnowledgeGraph, Node, OntologyNavigator, OntologyPolicy, Relation
from .types import GateDecision, Task, WorldState


def task_digest(task: Task) -> str:
    """Bind an approval to the complete JSON-compatible task content.

    Unsupported objects and non-finite numbers are rejected rather than coerced
    to strings. This is a content hash, not a digital signature.
    """

    def validate_keys(value: object) -> None:
        if isinstance(value, dict):
            if any(not isinstance(key, str) for key in value):
                raise TypeError("task object keys must be strings")
            for child in value.values():
                validate_keys(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                validate_keys(child)

    task_fields = {field.name: getattr(task, field.name) for field in fields(task)}
    validate_keys(task_fields)
    content = json.dumps(
        task_fields,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TaskFacts:
    """Task-specific evidence and memory IDs resolved by trusted application code."""

    task_id: str
    evidence_ids: tuple[str, ...] = ()
    memory_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ApprovalGrant:
    """Previously authenticated approval with content binding and validity."""

    id: str
    task_id: str
    digest: str
    issuer: str
    expires_at: float
    revoked: bool = False


def prepare_policy(
    tasks: Iterable[Task],
    records: KnowledgeGraph,
    facts: Iterable[TaskFacts],
    *,
    grants: Iterable[ApprovalGrant] = (),
    now: float,
) -> OntologyPolicy:
    """Build a fresh graph from registered records and explicit task bindings.

    ``records`` may contain only Evidence/Memory nodes and memory conflict facts.
    Missing evidence is not filled in from raw observations, task text or scores.
    Grants must already have been authenticated; only cleanbell2 is accepted.
    """
    if not math.isfinite(now):
        raise ValueError("invalid evaluation time")
    if any(node.kind not in {"Evidence", "Memory"} for node in records.nodes):
        raise ValueError("record graph must contain only evidence and memories")
    tasks = tuple(tasks)
    digests = {task.task_id: task_digest(task) for task in tasks}
    if len(digests) != len(tasks):
        raise ValueError("duplicate task ID")
    nodes = list(records.nodes)
    relations = list(records.relations)
    nodes.extend((Node("agent:echo", "Agent"), Node("cleanbell2", "Principal")))
    for task in tasks:
        nodes.append(Node(task.task_id, "Task"))
        relations.append(Relation("agent:echo", "proposes", task.task_id))
    seen = set()
    for binding in facts:
        if binding.task_id not in digests or binding.task_id in seen:
            raise ValueError("unknown or duplicate task facts")
        seen.add(binding.task_id)
        for record_id in binding.evidence_ids:
            relations.append(Relation(binding.task_id, "supported_by", record_id))
        for record_id in binding.memory_ids:
            relations.append(Relation(binding.task_id, "uses_memory", record_id))
    trusted = set()
    for grant in grants:
        if (
            grant.task_id not in digests
            or grant.issuer != "cleanbell2"
            or grant.revoked
            or not math.isfinite(grant.expires_at)
            or grant.expires_at <= now
            or digests.get(grant.task_id) != grant.digest
        ):
            continue
        nodes.append(Node(grant.id, "Approval"))
        relations.extend(
            (
                Relation(grant.task_id, "approved_by", grant.id),
                Relation(grant.id, "issued_by", "cleanbell2"),
            )
        )
        trusted.add(grant.id)
    return OntologyPolicy(
        KnowledgeGraph(tuple(nodes), tuple(relations)),
        trusted_approval_ids=frozenset(trusted),
        task_digests=digests,
    )


class RuntimeOntologyNavigator(OntologyNavigator):
    """Refresh policy after planning and expose structured decision records.

    The factory receives copies of tasks and WorldState. It must use trusted
    record storage to resolve evidence, memory dependencies and approval grants.
    A fresh empty policy ensures that use before preparation fails closed.
    """

    def __init__(
        self,
        factory: Callable[[tuple[Task, ...], WorldState], OntologyPolicy],
        **kwargs: object,
    ) -> None:
        super().__init__(OntologyPolicy(KnowledgeGraph()), **kwargs)
        self.factory = factory

    def prepare_tasks(self, tasks: Iterable[Task], world: WorldState) -> None:
        """Refresh the policy before SICL considers any candidate for execution."""
        snapshot = deepcopy(tuple(tasks))
        expected = {task.task_id: task_digest(task) for task in snapshot}
        policy = self.factory(snapshot, deepcopy(world))
        if policy.task_digests != expected:
            raise ValueError("runtime policy requires matching task content bindings")
        self.policy = policy

    def decision_record(self, task: Task, decision: GateDecision) -> dict:
        """Return audit data without storing task payload or evidence contents."""
        return {
            "task_id": task.task_id,
            "task_digest": task_digest(task),
            "decision": asdict(decision),
            "findings": [asdict(finding) for finding in self.policy.evaluate(task)],
        }
