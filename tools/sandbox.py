# tools/sandbox.py
"""
Sandbox for tool execution with path traversal prevention.

Key security principles:
- resolve() to normalize paths (collapse ../, follow symlinks)
- commonpath() to verify workspace containment
- Optional symlink blocking (strongest security)
- Fail-closed on any suspicious patterns

Defense against:
- Path traversal (../../../etc/passwd)
- Symlink escapes (workspace/symlink -> /etc)
- Absolute path injections (/tmp/evil)
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class SandboxViolation(RuntimeError):
    """Raised when sandbox security policy is violated."""

    pass


@dataclass(frozen=True)
class SandboxPolicy:
    """Sandbox security policy configuration."""

    allow_symlinks: bool = False
    # If False: forbid resolved paths that escape workspace even via symlink
    # If True: symlinks allowed but must remain within workspace when resolved
    # Recommendation: keep False for maximum security


def _commonpath(a: Path, b: Path) -> Path:
    """
    Return common ancestor path of two paths.

    Uses os.path.commonpath for robust handling of edge cases.

    Args:
        a: First path
        b: Second path

    Returns:
        Common ancestor path
    """
    return Path(os.path.commonpath([str(a), str(b)]))


def ensure_within_workspace(
    workspace: str,
    target_path: str,
    policy: SandboxPolicy = SandboxPolicy(),
) -> Path:
    """
    Validate and resolve path within workspace.

    Returns resolved Path if allowed; raises SandboxViolation otherwise.

    Args:
        workspace: Root directory for session (e.g., ./workspaces/<sid>)
        target_path: User/tool requested path (relative or absolute)
        policy: Sandbox security policy

    Returns:
        Resolved absolute path within workspace

    Raises:
        SandboxViolation: If path escapes workspace or violates policy

    Security checks:
    1. Resolve workspace to absolute canonical path
    2. Interpret relative paths as relative to workspace
    3. Resolve target path (collapse ../, follow symlinks)
    4. Verify resolved path is within workspace (commonpath check)
    5. Optionally block symlinks for stronger security

    Examples:
        >>> # Safe: relative path
        >>> ensure_within_workspace("/workspace", "file.txt")
        Path("/workspace/file.txt")

        >>> # BLOCKED: path traversal
        >>> ensure_within_workspace("/workspace", "../etc/passwd")
        SandboxViolation: path escapes workspace

        >>> # BLOCKED: absolute path outside workspace
        >>> ensure_within_workspace("/workspace", "/tmp/evil")
        SandboxViolation: path escapes workspace
    """
    # Resolve workspace to canonical form
    ws = Path(workspace).resolve()

    # Parse target path
    p = Path(target_path)

    # If relative, interpret relative to workspace
    if not p.is_absolute():
        p = ws / p

    # Resolve target path
    # For non-existent paths (create operations): resolve parent then append name
    try:
        resolved = p.resolve()
    except FileNotFoundError:
        # Path doesn't exist yet - resolve parent and append name
        parent = p.parent.resolve()
        resolved = parent / p.name

    # CRITICAL CHECK: Ensure resolved path is within workspace
    # If commonpath(ws, resolved) != ws, then resolved escapes workspace
    if _commonpath(ws, resolved) != ws:
        raise SandboxViolation(f"path escapes workspace: {resolved}")

    # Optional: Block symlinks for maximum security
    if not policy.allow_symlinks:
        # Check each component under workspace for symlinks
        # This prevents hidden escapes via symlink manipulation
        try:
            rel_parts = resolved.relative_to(ws).parts
        except ValueError:
            # resolved is not relative to ws (should be caught above, but fail-closed)
            raise SandboxViolation(f"path escapes workspace: {resolved}")

        cur = ws
        for part in rel_parts:
            cur = cur / part
            # Only check existing components
            if cur.exists() and cur.is_symlink():
                raise SandboxViolation(
                    f"symlink not allowed in workspace path: {cur}"
                )

    return resolved


def safe_cwd(workspace: str, requested_cwd: Optional[str]) -> str:
    """
    Resolve safe current working directory within workspace.

    Args:
        workspace: Workspace root path
        requested_cwd: User-requested cwd (or None for workspace root)

    Returns:
        Safe cwd path as string

    Raises:
        SandboxViolation: If requested_cwd escapes workspace

    Examples:
        >>> safe_cwd("/workspace", None)
        "/workspace"

        >>> safe_cwd("/workspace", "subdir")
        "/workspace/subdir"

        >>> safe_cwd("/workspace", "../etc")
        SandboxViolation: path escapes workspace
    """
    if not requested_cwd:
        return str(Path(workspace).resolve())
    p = ensure_within_workspace(workspace, requested_cwd)
    return str(p)


def validate_file_operation(
    workspace: str,
    operation: str,
    path: str,
    policy: SandboxPolicy = SandboxPolicy(),
) -> Path:
    """
    Validate file operation against sandbox policy.

    Convenience wrapper around ensure_within_workspace with operation context.

    Args:
        workspace: Workspace root path
        operation: Operation name (for error messages)
        path: Target path for operation
        policy: Sandbox security policy

    Returns:
        Resolved path

    Raises:
        SandboxViolation: If operation violates sandbox policy

    Examples:
        >>> validate_file_operation("/workspace", "read", "file.txt")
        Path("/workspace/file.txt")

        >>> validate_file_operation("/workspace", "write", "../passwd")
        SandboxViolation: [write] path escapes workspace
    """
    try:
        return ensure_within_workspace(workspace, path, policy)
    except SandboxViolation as e:
        # Add operation context to error message
        raise SandboxViolation(f"[{operation}] {e}") from e


# -------------------------
# Convenience utilities
# -------------------------


def is_safe_path(workspace: str, path: str) -> bool:
    """
    Check if path is safe without raising exception.

    Args:
        workspace: Workspace root path
        path: Path to check

    Returns:
        True if path is within workspace, False otherwise
    """
    try:
        ensure_within_workspace(workspace, path)
        return True
    except SandboxViolation:
        return False


def get_workspace_relative(workspace: str, path: str) -> str:
    """
    Get path relative to workspace.

    Args:
        workspace: Workspace root path
        path: Absolute path within workspace

    Returns:
        Path relative to workspace

    Raises:
        SandboxViolation: If path is not within workspace

    Examples:
        >>> get_workspace_relative("/workspace", "/workspace/subdir/file.txt")
        "subdir/file.txt"
    """
    resolved = ensure_within_workspace(workspace, path)
    ws = Path(workspace).resolve()
    try:
        return str(resolved.relative_to(ws))
    except ValueError as e:
        raise SandboxViolation(f"path not in workspace: {resolved}") from e
