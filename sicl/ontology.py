"""Small typed ontology and conservative, explainable SICL policy layer.

Facts are supplied by trusted application code, never inferred from task text.
This is a domain ontology with explicit rules, not an OWL reasoner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .gateway import HIGH_RISK, GatewayNavigator
from .types import DeltaLog, GateDecision, Task

Kind = Literal["Agent", "Task", "Evidence", "Memory", "Approval", "Principal"]

# Domain/range declarations are used to validate every asserted relationship.
RELATIONS = {
    "proposes": ("Agent", "Task"),
    "supported_by": ("Task", "Evidence"),
    "uses_memory": ("Task", "Memory"),
    "conflicts_with": ("Memory", "Memory"),
    "approved_by": ("Task", "Approval"),
    "issued_by": ("Approval", "Principal"),
}
KINDS = frozenset({"Agent", "Task", "Evidence", "Memory", "Approval", "Principal"})


@dataclass(frozen=True)
class Node:
    """An immutable concept instance; IDs are global within one graph."""

    id: str
    kind: Kind


@dataclass(frozen=True)
class Relation:
    """A directed, typed fact."""

    subject: str
    predicate: str
    object: str


@dataclass(frozen=True)
class KnowledgeGraph:
    """Validated snapshot; memory conflicts are treated symmetrically."""

    nodes: tuple[Node, ...] = ()
    relations: tuple[Relation, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "relations", tuple(self.relations))
        kinds = {node.id: node.kind for node in self.nodes}
        if len(kinds) != len(self.nodes):
            raise ValueError("duplicate node ID")
        if any(not node.id or node.kind not in KINDS for node in self.nodes):
            raise ValueError("invalid concept instance")
        for fact in self.relations:
            signature = RELATIONS.get(fact.predicate)
            if (
                signature is None
                or (kinds.get(fact.subject), kinds.get(fact.object)) != signature
            ):
                raise ValueError(
                    "unknown relation, missing endpoint, or wrong domain/range"
                )

    def contains(self, node_id: str, kind: Kind) -> bool:
        """Check the type of a referenced node."""
        return any(node.id == node_id and node.kind == kind for node in self.nodes)

    def targets(self, node_id: str, predicate: str) -> tuple[str, ...]:
        """Return sorted unique outgoing relationship targets."""
        return tuple(
            sorted(
                {
                    fact.object
                    for fact in self.relations
                    if fact.subject == node_id and fact.predicate == predicate
                }
            )
        )

    def conflicts(self, task_id: str) -> tuple[Relation, ...]:
        """Find unresolved conflicts incident to memories used by this task."""
        memories = set(self.targets(task_id, "uses_memory"))
        return tuple(
            fact
            for fact in self.relations
            if fact.predicate == "conflicts_with"
            and (fact.subject in memories or fact.object in memories)
        )


@dataclass(frozen=True)
class RuleFinding:
    """An explanation with graph references rather than an opaque score."""

    rule: str
    action: Literal["DENY", "REQUIRE_APPROVAL"]
    references: tuple[str, ...]


class OntologyPolicy:
    """Evaluate task relationships without granting execution authority.

    ``trusted_approval_ids`` must come from authenticated application storage.
    A graph claim or ``human_approved=True`` alone is never proof of approval.
    Approval validity, expiry, and revocation must be checked by that caller.
    """

    def __init__(
        self,
        graph: KnowledgeGraph,
        *,
        trusted_approval_ids: frozenset[str] = frozenset(),
        approval_principal: str = "cleanbell2",
    ) -> None:
        self.graph = graph
        self.trusted_approval_ids = frozenset(trusted_approval_ids)
        self.approval_principal = approval_principal

    def evaluate(self, task: Task) -> tuple[RuleFinding, ...]:
        """Return all applicable restrictions in deterministic rule order."""
        graph = self.graph
        if not graph.contains(task.task_id, "Task"):
            return (RuleFinding("O1_UNKNOWN_TASK", "DENY", (task.task_id,)),)
        findings = []
        evidence = graph.targets(task.task_id, "supported_by")
        if task.type != "READ_ONLY_QUERY" and not evidence:
            findings.append(RuleFinding("O2_MISSING_EVIDENCE", "DENY", (task.task_id,)))
        conflicts = graph.conflicts(task.task_id)
        if conflicts:
            refs = tuple(
                sorted(
                    {node for fact in conflicts for node in (fact.subject, fact.object)}
                )
            )
            findings.append(RuleFinding("O3_MEMORY_CONFLICT", "DENY", refs))
        if task.requires_human or task.type in HIGH_RISK:
            approvals = graph.targets(task.task_id, "approved_by")
            authorized = any(
                approval in self.trusted_approval_ids
                and self.approval_principal in graph.targets(approval, "issued_by")
                for approval in approvals
            )
            if not authorized:
                findings.append(
                    RuleFinding(
                        "O4_BEL_APPROVAL_REQUIRED",
                        "REQUIRE_APPROVAL",
                        (task.task_id, *approvals),
                    )
                )
        return tuple(findings)


class OntologyNavigator(GatewayNavigator):
    """Opt-in SICL gate applying ontology restrictions to existing decisions.

    Pass an instance as ``gate`` to SICLStateMachine. The existing gate always
    runs first; ontology rules can restrict but cannot upgrade its decision.
    GateDecision.reason includes rule IDs and graph references for the caller.
    """

    def __init__(self, policy: OntologyPolicy, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.policy = policy

    def gate(
        self, dlog: DeltaLog, task: Task, human_approved: bool = False
    ) -> GateDecision:
        """Apply the strongest restriction, keeping the existing mode."""
        original = super().gate(dlog, task, human_approved)
        findings = self.policy.evaluate(task)
        if not findings:
            return original
        reason = (
            original.reason
            + ";"
            + ";".join(
                finding.rule + ":" + ",".join(finding.references)
                for finding in findings
            )
        )
        if original.action in {"DENY", "FREEZE"}:
            return GateDecision(original.action, original.mode, reason)
        action = (
            "DENY" if any(f.action == "DENY" for f in findings) else "REQUIRE_APPROVAL"
        )
        return GateDecision(action, original.mode, reason)
