"""Runtime graph preparation, content binding, and durable decision traces."""

import json
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from sicl.ledger import AuditLedger
from sicl.ontology import KnowledgeGraph, Node, OntologyPolicy, Relation
from sicl.ontology_runtime import (
    ApprovalGrant,
    RuntimeOntologyNavigator,
    TaskFacts,
    prepare_policy,
    task_digest,
)
from sicl.state_machine import SICLStateMachine
from sicl.types import ActResult, DeltaLog, Task, WorldState

RECORDS = KnowledgeGraph(
    (Node("obs", "Evidence"), Node("old", "Memory"), Node("new", "Memory"))
)
TASK = Task("report", "WRITE_REPORT", requires_human=True, payload={"summary": "A"})
FACTS = (TaskFacts("report", ("obs",)),)
GRANT = ApprovalGrant("bel:1", "report", task_digest(TASK), "cleanbell2", 200)


def test_content_digest_is_order_independent_and_binds_entire_task():
    task = Task("x", "WRITE_REPORT", payload={"a": 1, "b": 2})
    assert task_digest(task) == task_digest(replace(task, payload={"b": 2, "a": 1}))
    for changed in (
        replace(task, payload={"a": 2}),
        replace(task, type="TRADE"),
        replace(task, task_id="y"),
        replace(task, requires_human=True),
    ):
        assert task_digest(task) != task_digest(changed)
    assert task_digest(replace(task, payload={"nested": [{"x": "value"}]}))


@pytest.mark.parametrize(
    "payload,error",
    [
        ({"x": float("nan")}, ValueError),
        ({"x": object()}, TypeError),
        ({"nested": [{1: "value"}]}, TypeError),
        ({"nested": TaskFacts("report")}, TypeError),
    ],
)
def test_noncanonical_payload_rejected(payload, error):
    with pytest.raises(error):
        task_digest(replace(TASK, payload=payload))


def test_registered_facts_create_task_graph_and_content_binding():
    policy = prepare_policy((TASK,), RECORDS, FACTS, grants=(GRANT,), now=100)
    assert policy.graph.targets("agent:echo", "proposes") == ("report",)
    assert policy.graph.targets("report", "supported_by") == ("obs",)
    assert policy.evaluate(TASK) == ()
    changed = replace(TASK, payload={"summary": "B"})
    assert policy.evaluate(changed)[0].rule == "O5_TASK_CHANGED"


@pytest.mark.parametrize(
    "grant",
    [
        replace(GRANT, revoked=True),
        replace(GRANT, expires_at=100),
        replace(GRANT, expires_at=float("inf")),
        replace(GRANT, issuer="ai"),
        replace(GRANT, digest="incorrect"),
        replace(GRANT, task_id="other"),
    ],
)
def test_invalid_grants_do_not_authorize(grant):
    policy = prepare_policy((TASK,), RECORDS, FACTS, grants=(grant,), now=100)
    assert policy.evaluate(TASK)[0].rule == "O4_BEL_APPROVAL_REQUIRED"
    assert not policy.graph.contains("bel:1", "Approval")


def test_missing_facts_are_not_inferred_from_payload_claims():
    task = replace(TASK, payload={"evidence": "obs", "approved": True})
    policy = prepare_policy((task,), RECORDS, (), now=100)
    assert [f.rule for f in policy.evaluate(task)] == [
        "O2_MISSING_EVIDENCE",
        "O4_BEL_APPROVAL_REQUIRED",
    ]


def test_memory_dependencies_and_conflicts_are_preserved():
    records = KnowledgeGraph(RECORDS.nodes, (Relation("old", "conflicts_with", "new"),))
    policy = prepare_policy(
        (TASK,),
        records,
        (TaskFacts("report", ("obs",), ("old",)),),
        grants=(GRANT,),
        now=100,
    )
    assert policy.evaluate(TASK)[0].rule == "O3_MEMORY_CONFLICT"


@pytest.mark.parametrize(
    "tasks,records,facts,now",
    [
        ((TASK,), RECORDS, FACTS, float("nan")),
        ((TASK,), KnowledgeGraph((Node("a", "Agent"),)), FACTS, 100),
        ((TASK, TASK), RECORDS, FACTS, 100),
        ((TASK,), RECORDS, (TaskFacts("missing"),), 100),
        ((TASK,), RECORDS, FACTS + FACTS, 100),
        ((TASK,), RECORDS, (TaskFacts("report", ("missing",)),), 100),
        ((TASK,), RECORDS, (TaskFacts("report", ("old",)),), 100),
    ],
)
def test_invalid_runtime_bindings_fail_closed(tasks, records, facts, now):
    with pytest.raises(ValueError):
        prepare_policy(tasks, records, facts, now=now)


def test_runtime_requires_matching_content_and_keeps_previous_policy_on_error():
    gate = RuntimeOntologyNavigator(
        lambda tasks, world: OntologyPolicy(KnowledgeGraph())
    )
    original = gate.policy
    with pytest.raises(ValueError, match="matching task content"):
        gate.prepare_tasks((TASK,), WorldState(0))
    assert gate.policy is original
    assert gate.gate(DeltaLog(), TASK).action == "DENY"


def test_factory_receives_copies_and_cannot_mutate_planned_tasks():
    def factory(tasks, world):
        tasks[0].payload["summary"] = "modified"
        world.observations["raw"] = "modified"
        return prepare_policy(tasks, RECORDS, FACTS, now=100)

    task = replace(TASK, payload={"summary": "A"})
    world = WorldState(0, {"raw": "original"})
    gate = RuntimeOntologyNavigator(factory)
    with pytest.raises(ValueError):
        gate.prepare_tasks((task,), world)
    assert task.payload == {"summary": "A"}
    assert world.observations == {"raw": "original"}


def test_per_tick_refresh_and_gate_record_payload_redaction():
    gate = RuntimeOntologyNavigator(
        lambda tasks, world: prepare_policy(
            tasks, RECORDS, (TaskFacts(t.task_id, ("obs",)) for t in tasks), now=100
        )
    )
    first = Task("first", "WRITE_REPORT", payload={"secret": "not-in-audit"})
    gate.prepare_tasks((first,), WorldState(0))
    decision = gate.gate(DeltaLog(), first)
    assert decision.action == "ALLOW"
    record = gate.decision_record(first, decision)
    assert record["findings"] == []
    assert "not-in-audit" not in json.dumps(record)
    gate.prepare_tasks((Task("second", "READ_ONLY_QUERY"),), WorldState(1))
    assert gate.gate(DeltaLog(), first).action == "DENY"


def test_real_loop_persists_denied_candidate_before_supported_execution(tmp_path):
    denied = Task("denied", "WRITE_REPORT")
    allowed = Task("allowed", "WRITE_REPORT")
    gate = RuntimeOntologyNavigator(
        lambda tasks, world: prepare_policy(
            tasks, RECORDS, (TaskFacts("allowed", ("obs",)),), now=100
        )
    )
    sensor = SimpleNamespace(read=lambda tick: WorldState(tick))
    calculator = SimpleNamespace(compute=lambda world: DeltaLog())
    planner = SimpleNamespace(propose=lambda *args: [denied, allowed])
    executor = Mock()
    executor.execute.return_value = ActResult(ok=True, state_change_bits=1)
    ledger = AuditLedger(str(tmp_path / "ledger.jsonl"))
    machine = SICLStateMachine(sensor, calculator, planner, gate, executor, ledger)
    machine.tick(audit_prob=0)
    executor.execute.assert_called_once_with(allowed)
    entries = [
        json.loads(line)
        for line in (tmp_path / "ledger.jsonl").read_text().splitlines()
    ]
    assert [entry["kind"] for entry in entries] == [
        "ontology_decision",
        "ontology_decision",
        "pre_commit",
        "post_receipt",
    ]
    denied_record, allowed_record = (entry["data"] for entry in entries[:2])
    assert denied_record["findings"][0]["rule"] == "O2_MISSING_EVIDENCE"
    assert denied_record["decision"]["action"] == "DENY"
    assert allowed_record["decision"]["action"] == "ALLOW"
    assert denied_record["trace_id"] == allowed_record["trace_id"]


def test_audit_failure_prevents_execution():
    gate = RuntimeOntologyNavigator(
        lambda tasks, world: prepare_policy(
            tasks, RECORDS, (TaskFacts("report", ("obs",)),), grants=(GRANT,), now=100
        )
    )
    ledger = Mock()
    ledger.append.side_effect = OSError("disk full")
    executor = Mock()
    machine = SICLStateMachine(
        SimpleNamespace(read=lambda tick: WorldState(tick)),
        SimpleNamespace(compute=lambda world: DeltaLog()),
        SimpleNamespace(propose=lambda *args: [TASK]),
        gate,
        executor,
        ledger,
    )
    with pytest.raises(OSError):
        machine.tick(audit_prob=0)
    executor.execute.assert_not_called()


def test_default_gate_still_executes_without_ontology_hooks():
    from sicl.gateway import GatewayNavigator

    task = Task("routine", "WRITE_REPORT")
    ledger = Mock()
    executor = Mock()
    executor.execute.return_value = ActResult(ok=True, state_change_bits=1)
    machine = SICLStateMachine(
        SimpleNamespace(read=lambda tick: WorldState(tick)),
        SimpleNamespace(compute=lambda world: DeltaLog()),
        SimpleNamespace(propose=lambda *args: [task]),
        GatewayNavigator(),
        executor,
        ledger,
    )
    machine.tick(audit_prob=0)
    executor.execute.assert_called_once_with(task)
    assert [call.args[0] for call in ledger.append.call_args_list] == [
        "pre_commit",
        "post_receipt",
    ]
