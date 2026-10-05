from __future__ import annotations

from pathlib import Path

import pytest

from felogram.application.preferences import Preferences, PreferenceStore


@pytest.mark.native
def test_preferences_round_trip_is_protected(tmp_path: Path) -> None:
    path = tmp_path / "workspace.dpapi"
    store = PreferenceStore(path)
    preferences = Preferences(collections={"Projects": [1, 2]}, searches=[(1, "secret query")])
    store.save(preferences)
    assert b"secret query" not in path.read_bytes()
    assert store.load() == preferences


def test_memory_preferences_do_not_create_files() -> None:
    store = PreferenceStore()
    store.save(Preferences(searches=[(1, "query")]))
    assert store.path is None
