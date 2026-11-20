"""Typed fact validation and real gate decisions for the ontology layer."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from sicl.ontology import (
    KnowledgeGraph,
    Node,
    OntologyNavigator,
    OntologyPolicy,
    Relation,
)
from sicl.types import DeltaLog, Task


def graph(*relations):
    return KnowledgeGraph(
        (
            Node("echo", "Agent"),
            Node("task", "Task"),
            Node("other", "Task"),
            Node("source", "Evidence"),
            Node("old", "Memory"),
            Node("new", "Memory"),
            Node("approval", "Approval"),
            Node("cleanbell2", "Principal"),
            Node("ai", "Principal"),
        ),
        (Relation("echo", "proposes", "task"), *relations),
    )


SUPPORT = Relation("task", "supported_by", "source")
USES = Relation("task", "uses_memory", "old")
APPROVAL = Relation("task", "approved_by", "approval")
BEL = Relation("approval", "issued_by", "cleanbell2")


@pytest.mark.parametrize(
    "nodes,relations",
    [
        ((Node("x", "Task"), Node("x", "Task")), ()),
        ((Node("", "Task"),), ()),
        ((Node("x", "Invented"),), ()),
        ((Node("x", "Task"),), (Relation("x", "unknown", "x"),)),
        ((Node("x", "Task"),), (Relation("x", "supported_by", "missing"),)),
        ((Node("x", "Task"),), (Relation("x", "supported_by", "x"),)),
    ],
)
def test_invalid_graphs_rejected(nodes, relations):
    with pytest.raises(ValueError):
        KnowledgeGraph(nodes, relations)


def test_snapshot_copies_mutable_inputs_and_deduplicates_queries():
    nodes = [Node("task", "Task"), Node("source", "Evidence")]
    relations = [SUPPORT, SUPPORT]
    snapshot = KnowledgeGraph(nodes, relations)
    nodes.clear()
    relations.clear()
    assert snapshot.contains("task", "Task")
    assert not snapshot.contains("task", "Memory")
    assert snapshot.targets("task", "supported_by") == ("source",)
    assert snapshot.targets("task", "uses_memory") == ()


def test_unknown_task_fails_closed():
    findings = OntologyPolicy(graph()).evaluate(Task("missing", "READ_ONLY_QUERY"))
    assert findings[0].rule == "O1_UNKNOWN_TASK"
    assert findings[0].action == "DENY"


def test_read_can_collect_evidence_but_writes_need_it():
    policy = OntologyPolicy(graph())
    assert policy.evaluate(Task("task", "READ_ONLY_QUERY")) == ()
    assert (
        policy.evaluate(Task("task", "WRITE_REPORT"))[0].rule == "O2_MISSING_EVIDENCE"
    )
    assert OntologyPolicy(graph(SUPPORT)).evaluate(Task("task", "WRITE_REPORT")) == ()


@pytest.mark.parametrize(
    "conflict",
    [
        Relation("old", "conflicts_with", "new"),
        Relation("new", "conflicts_with", "old"),
    ],
)
def test_conflicting_memory_blocks_even_with_approval(conflict):
    policy = OntologyPolicy(
        graph(SUPPORT, USES, conflict, APPROVAL, BEL),
        trusted_approval_ids=frozenset({"approval"}),
    )
    findings = policy.evaluate(Task("task", "WRITE_REPORT", requires_human=True))
    assert len(findings) == 1
    assert findings[0].rule == "O3_MEMORY_CONFLICT"
    assert findings[0].references == ("new", "old")


def test_unrelated_conflict_does_not_block():
    policy = OntologyPolicy(graph(SUPPORT, Relation("old", "conflicts_with", "new")))
    assert policy.evaluate(Task("task", "WRITE_REPORT")) == ()


@pytest.mark.parametrize(
    "facts,trusted",
    [
        ((), frozenset()),
        ((APPROVAL, BEL), frozenset()),
        ((APPROVAL, Relation("approval", "issued_by", "ai")), frozenset({"approval"})),
        ((Relation("other", "approved_by", "approval"), BEL), frozenset({"approval"})),
    ],
)
def test_approval_must_be_trusted_from_bel_and_bound_to_task(facts, trusted):
    policy = OntologyPolicy(graph(SUPPORT, *facts), trusted_approval_ids=trusted)
    assert (
        policy.evaluate(Task("task", "WRITE_REPORT", requires_human=True))[0].rule
        == "O4_BEL_APPROVAL_REQUIRED"
    )


def test_findings_are_all_reported_in_rule_order():
    policy = OntologyPolicy(graph(USES, Relation("old", "conflicts_with", "new")))
    findings = policy.evaluate(Task("task", "NETWORK_POST"))
    assert [f.rule for f in findings] == [
        "O2_MISSING_EVIDENCE",
        "O3_MEMORY_CONFLICT",
        "O4_BEL_APPROVAL_REQUIRED",
    ]


def test_gate_allows_supported_report_and_retains_existing_restrictions():
    policy = OntologyPolicy(
        graph(SUPPORT, APPROVAL, BEL), trusted_approval_ids=frozenset({"approval"})
    )
    gate = OntologyNavigator(policy)
    assert gate.gate(DeltaLog(), Task("task", "WRITE_REPORT")).action == "ALLOW"
    assert (
        gate.gate(DeltaLog(e_est=0.5), Task("task", "WRITE_REPORT")).action
        == "RESTRICT_ALLOW"
    )
    assert (
        gate.gate(DeltaLog(e_est=0.8), Task("task", "WRITE_REPORT")).action == "FREEZE"
    )
    assert (
        gate.gate(DeltaLog(), Task("task", "NETWORK_POST")).action == "REQUIRE_APPROVAL"
    )


def test_boolean_approval_cannot_bypass_ontology_rule():
    gate = OntologyNavigator(OntologyPolicy(graph(SUPPORT)))
    task = Task("task", "WRITE_REPORT", requires_human=True)
    decision = gate.gate(DeltaLog(), task, human_approved=True)
    assert decision.action == "REQUIRE_APPROVAL"
    assert "O4_BEL_APPROVAL_REQUIRED:task" in decision.reason


@pytest.mark.parametrize(
    "task_type,expected",
    [
        ("WRITE_REPORT", "FREEZE"),
        ("UNKNOWN", "DENY"),
    ],
)
def test_existing_denials_preserved_with_rule_explanations(task_type, expected):
    gate = OntologyNavigator(OntologyPolicy(graph()))
    decision = gate.gate(
        DeltaLog(e_est=0.8 if expected == "FREEZE" else 0), Task("task", task_type)
    )
    assert decision.action == expected
    assert "O2_MISSING_EVIDENCE" in decision.reason


def test_ontology_denial_overrides_split_attack_restrict_allow(monkeypatch):
    gate = OntologyNavigator(OntologyPolicy(graph()), split_cum_threshold=0)
    clock = iter((100.0, 101.0))
    monkeypatch.setattr("sicl.gateway.time.time", lambda: next(clock))
    gate.gate(DeltaLog(), Task("task", "READ_ONLY_QUERY", e_est=0))
    decision = gate.gate(DeltaLog(), Task("task", "NETWORK_POST", e_est=0.5))
    assert decision.action == "DENY"


def test_gate_denies_unknown_task():
    gate = OntologyNavigator(OntologyPolicy(graph()))
    assert gate.gate(DeltaLog(), Task("missing", "READ_ONLY_QUERY")).action == "DENY"


def test_trusted_approval_snapshot_is_copied():
    trusted = {"approval"}
    policy = OntologyPolicy(graph(SUPPORT, APPROVAL, BEL), trusted_approval_ids=trusted)
    trusted.clear()
    assert policy.evaluate(Task("task", "WRITE_REPORT", requires_human=True)) == ()


@pytest.mark.parametrize("supported,executed", [(False, False), (True, True)])
def test_state_machine_enforces_ontology_before_execution(supported, executed):
    from sicl.state_machine import SICLStateMachine
    from sicl.types import ActResult, WorldState

    policy = OntologyPolicy(graph(*((SUPPORT,) if supported else ())))
    sensor = SimpleNamespace(read=lambda tick: WorldState(tick))
    calculator = SimpleNamespace(compute=lambda world: DeltaLog())
    task = Task("task", "WRITE_REPORT")
    planner = SimpleNamespace(propose=lambda *args: [task])
    executor = Mock()
    executor.execute.return_value = ActResult(ok=True, state_change_bits=1)
    machine = SICLStateMachine(
        sensor, calculator, planner, OntologyNavigator(policy), executor, Mock()
    )
    machine.tick(audit_prob=0)
    assert executor.execute.called is executed
    assert machine.t == 1
