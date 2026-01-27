# CLAUDE.md - Echo Autonomy

> AI assistant guide for the Echo Autonomy codebase

## Project Overview

**Echo Autonomy** is a Self-Improved Control Logic (SICL) system implementing autonomous agent behavior control with safety constraints. Version 0.9 is codenamed "The Heartbeat" (심장이 뛰기 시작함).

The system provides:
- Autonomous decision-making within defined safety constraints
- Real-time risk assessment and mode control
- Dynamic control parameter optimization (Tau Controller)
- Cryptographic audit logging for tamper detection
- Stasis break mechanisms to prevent indefinite freeze states

## Codebase Structure

```
echo_autonomy/
├── .env                          # Environment config (API keys, model selection)
├── audit_ledger.jsonl            # Append-only audit log with hash chain
├── sicl/                         # Core SICL system
│   ├── __init__.py
│   ├── types.py                  # Type definitions, enums, dataclasses
│   ├── state_machine.py          # Main SICL state machine orchestrator
│   ├── world_sensor.py           # Environmental state observation
│   ├── planner.py                # Task planning and proposal generation
│   ├── gateway.py                # Decision gating with security rules
│   ├── executor.py               # Task execution
│   ├── ledger.py                 # Audit log management with hash chain
│   ├── metrics.py                # Performance and behavior metrics
│   └── control/
│       └── tau_controller.py     # Dynamic control parameter optimization
└── benches/                      # Benchmarking
    ├── __init__.py
    ├── run_bench.py              # Benchmark runner
    └── autonomybench20.jsonl     # Test case definitions
```

## Key Concepts

### State Machine (8-State SICL Cycle)

Each tick progresses through:
```
IDLE → OBSERVE → ASSESS → PLAN → GATE → ACT → REVIEW → UPDATE → (repeat)
```

- **OBSERVE**: Read world state via WorldSensor
- **ASSESS**: Calculate DeltaLog (risk/complexity metrics)
- **PLAN**: Generate candidate tasks with priority queue
- **GATE**: Apply security rules and risk gating
- **ACT**: Execute chosen task
- **REVIEW**: Optional random audit injection
- **UPDATE**: Record metrics and advance time

### Operating Modes

| Mode | Trigger Condition | Allowed Tasks |
|------|-------------------|---------------|
| `NORMAL` | `e_est < 0.5` and `comp < 0.75` | READ_ONLY_QUERY, WRITE_LOG, WRITE_REPORT, SIMULATE |
| `RESTRICTED` | `e_est >= 0.5` or `comp >= 0.75` | READ_ONLY_QUERY, WRITE_LOG, WRITE_REPORT, SIMULATE |
| `FREEZE` | `e_est >= 0.8` | READ_ONLY_QUERY, WRITE_LOG |

### Task Types

- **Safe**: `READ_ONLY_QUERY`, `WRITE_LOG`, `WRITE_REPORT`, `SIMULATE`
- **High Risk**: `SYSTEM_CHANGE`, `NETWORK_POST`, `TRADE` (blocked in FREEZE, require approval in RESTRICTED)

### Tau Controller

Dynamically adjusts:
- `tau`: Response time constant (0.4 - 3.0)
- `tick_interval_sec`: Control loop frequency
- `audit_prob`: Audit trigger probability (floor: 0.05, ceiling: 0.60)
- `stasis_cooldown_sec`: Cooldown between stasis breaks (60-900 sec)

### Audit Ledger

- Append-only JSONL format with cryptographic hash chain
- Each record contains `prev` (previous hash) and `hash` (current hash)
- First record uses "GENESIS" as the initial hash
- Record kinds: `pre_commit`, `post_receipt`, `sys_audit`

## Development Commands

### Run Benchmarks
```bash
python benches/run_bench.py
```

Output format:
```
[01] tick_without_prompt          | A_gain: 0.XX | Tau_End: 1.XX
[21] latency_stress_response      | A_gain: 0.XX | Tau_End: 0.XX
```

### Environment Setup
```bash
# Install dependencies
pip install python-dotenv

# Configure .env file
GEMINI_API_KEY=<your-key>
GEMINI_MODEL=gemini-2.0-flash-exp
```

## Key Metrics

- **A_gain**: Weighted action impact (novel actions: 1.0, repeated: 0.3)
- **CL_rate**: Closed-loop completion percentage
- **S_stasis**: Proportion of FREEZE/RESTRICTED modes

## Code Conventions

### Naming

- **Functions**: lowercase with underscores (`compute()`, `record_action_weighted()`)
- **Internal methods**: underscore prefix (`_family_id()`, `_family_key()`)
- **Classes**: PascalCase with role suffix (`GatewayNavigator`, `TauController`)
- **Metrics variables**: Greek letters (`tau`, `phi`, `psi`, `chi`, `omega`, `theta`)

### Style

- Compact semicolon style for related statements
- Heavy use of dataclasses and type hints
- Bilingual comments (Korean and English)
- Short, concise inline documentation

### Key Files for Common Tasks

| Task | Files |
|------|-------|
| Modify gating logic | `sicl/gateway.py` |
| Add new task types | `sicl/types.py`, `sicl/gateway.py` |
| Adjust control parameters | `sicl/control/tau_controller.py` |
| Add metrics | `sicl/metrics.py` |
| Modify planning | `sicl/planner.py` |
| Add benchmark tests | `benches/autonomybench20.jsonl` |

## Important Patterns

### Split-Execution Detection

The gateway tracks cumulative risk (`e_est`) per task family in a 120-second sliding window to prevent circumventing restrictions through task fragmentation.

### Stasis Break Mechanism

After 8+ ticks with high stasis (S_stasis >= 0.7), the planner proposes a safe action to break out of freeze state. Cooldown prevents rapid successive breakouts.

### Priority Queue with Fallback

Tasks are proposed in priority order. If a high-priority task is denied, the system falls back to lower-priority allowed tasks.

## Type Definitions Reference

```python
# Modes
Mode = Literal["NORMAL", "RESTRICTED", "FREEZE"]

# Task types
TaskType = Literal[
    "READ_ONLY_QUERY", "WRITE_LOG", "WRITE_REPORT",
    "SIMULATE", "SYSTEM_CHANGE", "NETWORK_POST", "TRADE"
]

# Gate decisions
GateDecision.action: Literal["ALLOW", "RESTRICT_ALLOW", "REQUIRE_APPROVAL", "DENY", "FREEZE"]

# Key dataclasses
DeltaLog    # Risk metrics: psi, phi, chi, omega, comp, e_est, theta_drift_deg
Task        # Action proposal: task_id, type, requires_human, e_est, payload
ActResult   # Execution result: ok, artifact, state_change_bits, error
```

## Architecture Notes

- This is a prototype (v0.9) with stub implementations in `executor.py` and `world_sensor.py`
- External API integration (Gemini) is configured but not yet active
- The audit ledger verification (`verify_chain()`) is simplified for now
