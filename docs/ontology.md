# Echo ontology: parallel implementation v0.1

This opt-in SICL layer makes concepts and relationships executable. It runs
alongside E_break research; it does not change E_break, theta, DeltaLog formulas,
PR #12, or the production echo_gateway. It is a typed domain ontology with
explicit Python rules, not RDF/OWL reasoning or a claim of validated AI safety.

## Concepts and relationships

| Subject concept | Relationship | Object concept | Meaning |
| --- | --- | --- | --- |
| Agent | proposes | Task | An agent proposes an action, without approval authority |
| Task | supported_by | Evidence | Action has a referenced basis |
| Task | uses_memory | Memory | Action depends on a memory record |
| Memory | conflicts_with | Memory | Unresolved contradiction, checked in either direction |
| Task | approved_by | Approval | Approval is explicitly linked to this task |
| Approval | issued_by | Principal | Identifies the approval issuer |

Existing SICL `DeltaLog` and `GateDecision` remain the state and decision
contracts. Graph nodes identify records; they do not validate evidence content,
detect semantic contradictions, or measure consciousness or selfhood.

## Executable rules

| Rule | Trigger | Decision |
| --- | --- | --- |
| O1_UNKNOWN_TASK | Task ID absent from the graph | DENY |
| O2_MISSING_EVIDENCE | Any task other than evidence-gathering READ_ONLY_QUERY lacks supported_by | DENY |
| O3_MEMORY_CONFLICT | A used memory participates in an unresolved conflict | DENY |
| O4_BEL_APPROVAL_REQUIRED | High-risk or requires_human task lacks trusted, task-linked approval from cleanbell2 | REQUIRE_APPROVAL |

All matching rules are returned, with node references. Denial takes precedence
over approval requests. Existing DENY/FREEZE decisions remain in force.
The ontology cannot upgrade a baseline gate decision. In particular, the
current SICL gate still returns REQUIRE_APPROVAL for high-risk tasks even when
ontology approval is present. Resolving that baseline behavior is separate work.

## Minimal real gate example

```python
from sicl.ontology import KnowledgeGraph, Node, Relation, OntologyPolicy, OntologyNavigator
from sicl.types import DeltaLog, Task

graph = KnowledgeGraph(
    nodes=(Node("echo", "Agent"), Node("report.1", "Task"), Node("obs.1", "Evidence")),
    relations=(Relation("echo", "proposes", "report.1"),
               Relation("report.1", "supported_by", "obs.1")),
)
gate = OntologyNavigator(OntologyPolicy(graph))
decision = gate.gate(DeltaLog(), Task("report.1", "WRITE_REPORT"))
assert decision.action == "ALLOW"
```

Pass `gate` to the existing `SICLStateMachine(..., gate=gate, ...)` constructor
to apply these decisions before execution. Its internal dummy task used to
inspect mode will be denied by O1; mode calculation is retained and that dummy
task is never executed. Every actual planner task needs a corresponding Task
node. Refresh the policy snapshot when the trusted observation/planning layer
creates tasks or updates memories. There is no automatic graph builder yet.

Facts and the policy are trusted application inputs. Do not build approval or
evidence facts by accepting LLM output or untrusted task payloads as truth.
`trusted_approval_ids` must come from authenticated approval storage after
checking the exact task, expiry, revocation, and issuer. The ontology does not
perform authentication and `human_approved=True` cannot bypass its rules.
This version assumes task IDs uniquely identify immutable task content; callers
must not reuse an approved ID for a changed payload. Cryptographic binding and
persistent approval storage are future integration work.

Conflicts remain blocking until a trusted reconciliation step replaces the
graph snapshot. Approval does not erase conflicts. GateDecision.reason contains
rule IDs and graph references; structured findings are available through
`policy.evaluate(task)`. SICL's existing state machine does not yet persist these
findings in its ledger. Neither this module nor its tests send network messages,
execute trades, or call an LLM.

## Validation and next integration

Run `python -m pytest tests/test_sicl_ontology.py --cov=sicl.ontology --cov-report=term-missing`.
The tests cover domain/range validation, immutable snapshots, evidence rules,
bidirectional memory conflicts, forged/wrong-task approvals, rule precedence,
and enforcement through the real SICL gate.

Next: add trusted observation-to-graph adapters and persistent rule traces;
bind approvals to task content; link measured E_break reports as evidence only
after the calculator contract is fixed. Add State/Decision/Rule nodes when the
state transition and audit representation are settled. Keep symbolic concept
names distinct from externally verified observations.
