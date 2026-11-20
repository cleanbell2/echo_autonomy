# Echo ontology: parallel implementation v0.2

This opt-in SICL layer makes concepts and relationships executable. It runs
alongside E_break research; it does not change E_break, theta, DeltaLog formulas,
PR #12, or the production echo_gateway. SICL gains optional preparation and
audit hooks for the runtime adapter. It is a typed domain ontology with
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
| O5_TASK_CHANGED | Runtime task content differs from the prepared snapshot | DENY |

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
to apply these decisions before execution. SICL now calls `decide_mode` directly
instead of submitting a dummy task. Every actual planner task needs a
corresponding Task node. Use the runtime adapter below to refresh that snapshot
after planning on each tick.

Facts and the policy are trusted application inputs. Do not build approval or
evidence facts by accepting LLM output or untrusted task payloads as truth.
`trusted_approval_ids` must come from authenticated approval storage after
checking the exact task, expiry, revocation, and issuer. The ontology does not
perform authentication and `human_approved=True` cannot bypass its rules.
The basic policy still assumes IDs uniquely identify immutable tasks. The
runtime adapter additionally binds the complete task content to a SHA-256
digest. Authentication and persistent approval storage remain caller duties.

Conflicts remain blocking until a trusted reconciliation step replaces the
graph snapshot. Approval does not erase conflicts. GateDecision.reason contains
rule IDs and graph references; structured findings are available through
`policy.evaluate(task)`. RuntimeOntologyNavigator supplies structured records
that SICL writes before selecting/executing a task. Neither these modules nor
their tests send network messages,
execute trades, or call an LLM.

## Validation and next integration

Run `python -m pytest tests/test_sicl_ontology*.py --cov=sicl.ontology --cov=sicl.ontology_runtime --cov-report=term-missing`.
The tests cover domain/range validation, immutable snapshots, evidence rules,
bidirectional memory conflicts, forged/wrong-task approvals, rule precedence,
and enforcement through the real SICL gate.

Next: connect real authenticated evidence/memory/approval storage to the factory;
link measured E_break reports as evidence only after the calculator contract is
fixed. Add State/Decision/Rule nodes when the
state transition and audit representation are settled. Keep symbolic concept
names distinct from externally verified observations.

## Runtime adapter and audit integration

`prepare_policy(tasks, records, facts, grants=..., now=...)` registers each
planned task and its `proposes` relationship, then links explicitly supplied
TaskFacts to registered Evidence/Memory records. It rejects unknown record IDs,
wrong relationship types, duplicate task IDs, and duplicate bindings. A task's
payload claiming evidence or approval is never accepted as a trusted fact.
Only a trusted storage adapter can decide which record backs which task.

The input record graph contains Evidence/Memory nodes and unresolved memory
conflicts. ApprovalGrant records must already be authenticated. The adapter
filters out grants from other issuers, expired/non-finite expiry, revocation,
wrong task IDs, or changed task content. Grants are checked at snapshot
preparation time; long-running execution needs fresh checks immediately before
its external side effects. The digest is a content hash, not a signature, and
JSON-compatible tasks are required. ID-only legacy policy remains available;
the runtime navigator requires matching content bindings for every prepared task.

```python
import time
from sicl.ontology_runtime import RuntimeOntologyNavigator, TaskFacts, prepare_policy

def factory(tasks, world):
    # Implement with authenticated application storage, not raw LLM claims.
    records, task_facts, grants = trusted_store.resolve(tasks, world)
    return prepare_policy(tasks, records, task_facts, grants=grants, now=time.time())

gate = RuntimeOntologyNavigator(factory)
# Pass gate to SICLStateMachine. Its tick calls prepare_tasks after planning.
```

`trusted_store` is an integration interface in this example, not an implemented
service. Runtime policy preparation receives copies, preventing accidental
mutation of planned tasks. Every considered candidate, including denied ones,
produces `ontology_decision` data with tick, trace ID, task digest, final decision,
and structured rule findings. Raw task payloads and evidence contents are not
included in these new records. SICL's existing pre_commit event still contains
the chosen task payload. Audit write errors propagate before execution.

The existing AuditLedger persists these events, but its verify_chain method is
still a stub and restart chain recovery is not implemented. Persistence here
does not claim tamper-proof audit verification. Default GatewayNavigator remains
usable without a factory and emits no new ontology events.
