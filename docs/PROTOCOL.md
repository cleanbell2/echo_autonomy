# Echo Gateway Protocol Specification (Phase 3)

## 1. Overview
This document defines the **wire-format** and **validation rules** for the Echo Gateway Protocol.
Goals:
- Type-safe request/response schemas (Pydantic v2)
- Fail-closed validation (unknown/invalid inputs are rejected)
- Security-first handling (size limits, nesting depth, JSON safety)
- Deterministic envelope structure for transport and logging

## 2. Envelope
All payloads are wrapped by an Envelope.

### 2.1 Fields
- `session_id` (string, required)
  - Identifies the client session.
  - Must be sanitized before use (dangerous characters removed).
- `timestamp` (float, required)
  - Unix epoch seconds.
  - Used for recency checks (default policy: 5-minute window).
- `payload` (object/dict, required)
  - Must be JSON-serializable.
  - Must satisfy nesting depth limits (default: 32).
- `signature` (string, optional)
  - Optional integrity field. Format is implementation-defined (e.g. `sha256:...`).

### 2.2 Envelope Validation Rules
- Timestamp recency: reject if older than the allowed window.
- `payload` must be a dict-like JSON object.
- Fail-closed: if envelope validation fails, the message is rejected.

## 3. Request Schemas
Requests are discriminated by `type`.

### 3.1 MessageRequest
- `type`: `"message"`
- `content`: string (min 1 char)
- `metadata`: object (optional)

### 3.2 ToolCallRequest
- `type`: `"tool_call"`
- `tool_name`: string (min 1 char)
- `arguments`: object (optional)
- `metadata`: object (optional)

### 3.3 StatusRequest
- `type`: `"status"`
- `status`: one of:
  - `ping`, `ready`, `busy`, `shutdown`
- `metadata`: object (optional)

### 3.4 Unknown Fields Policy
All request schemas use **extra=forbid**:
- Any unknown field triggers schema validation error.
- This prevents silent acceptance of unexpected inputs.

### 3.5 Unknown Type Policy
- Unknown `type` is rejected (ValueError).
- Fail-closed behavior: "unknown" is never treated as a valid request.

## 4. Response Schema
### 4.1 MessageResponse
- `status`: `"success" | "error" | "pending"`
- `data`: object (optional; default `{}`)
- `error`: string (optional; see rules below)

#### Error Rules (Fail-Closed)
- If `status == "error"`: `error` must be a non-empty string.
- If `status in ("success", "pending")`: `error` must be omitted or `null`.
  - Rationale: avoids ambiguous "success with error" states.

## 5. Validator Rules (Transport Safety)
These are applied before schema parsing where appropriate.

### 5.1 Size Limit
- Default: 10MB max.
- Messages exceeding limit are rejected.

### 5.2 Session ID Sanitization
- Remove dangerous characters and normalize.
- Enforce max length (default: 128).

### 5.3 JSON Serializability
- Payload must be JSON-serializable.
- Non-serializable objects are rejected.

### 5.4 Nesting Depth Limit
- Default max depth: 32.
- Prevents "nesting bombs" / recursion attacks.

## 6. Security Guarantees
- Fail-closed by default: invalid inputs are rejected.
- No shell-based suppression of failures in CI (no `|| true`).
- E2E "server missing" cases should be represented as **internal test skips**, not forced passes.
- Unknown request types and unexpected fields are blocked.

## 7. Versioning & Compatibility
- Protocol changes should be additive when possible.
- If breaking changes are introduced, bump a protocol version marker (future work).

## 8. Test Coverage Expectations
Minimum recommended tests:
- Envelope creation/validation/roundtrip
- Schema parsing and forbid-extra behavior
- Validator: size/session_id/json/depth
- Integration pipeline: envelope ↔ validator ↔ schema
