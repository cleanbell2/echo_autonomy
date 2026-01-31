"""
Test session TTL + sweep — Phase 4
"""

import time

import pytest

from echo_gateway.session.store import SessionStore


def test_session_store_get_or_create():
    """get_or_create returns existing or creates new session."""
    store = SessionStore(ttl_seconds=60)
    s1 = store.get_or_create("session-1")
    assert s1.session_id == "session-1"

    s2 = store.get_or_create("session-1")
    assert s2.session_id == "session-1"
    assert s1 is s2  # same object


def test_session_store_updates_last_seen():
    """get_or_create updates last_seen."""
    store = SessionStore(ttl_seconds=60)
    s = store.get_or_create("session-1")
    first_seen = s.last_seen
    time.sleep(0.1)
    s2 = store.get_or_create("session-1")
    assert s2.last_seen > first_seen


def test_session_store_sweep_removes_idle():
    """sweep removes sessions idle beyond TTL."""
    store = SessionStore(ttl_seconds=1)
    store.get_or_create("session-1")
    store.get_or_create("session-2")
    time.sleep(1.5)
    removed = store.sweep()
    assert removed == 2


def test_session_store_sweep_keeps_active():
    """sweep keeps sessions within TTL."""
    store = SessionStore(ttl_seconds=10)
    store.get_or_create("session-1")
    time.sleep(0.5)
    removed = store.sweep()
    assert removed == 0
