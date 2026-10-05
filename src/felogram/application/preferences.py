from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from felogram.security import WindowsDpapiSecretStore


@dataclass
class Preferences:
    collections: dict[str, list[int]] = field(default_factory=dict)
    searches: list[tuple[int, str]] = field(default_factory=list)


class PreferenceStore:
    """Optional DPAPI-protected, local-only workspace preferences."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path

    def load(self) -> Preferences:
        if self.path is None or not self.path.exists():
            return Preferences()
        payload = WindowsDpapiSecretStore._unprotect(self.path.read_bytes())
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("Invalid workspace preferences")
        collections = data.get("collections", {})
        searches = data.get("searches", [])
        if not isinstance(collections, dict) or not isinstance(searches, list):
            raise ValueError("Invalid workspace preferences")
        result = Preferences()
        for name, ids in collections.items():
            if isinstance(name, str) and isinstance(ids, list):
                result.collections[name[:64]] = [
                    identifier for identifier in ids if type(identifier) is int
                ]
        for item in searches[:50]:
            if (
                isinstance(item, list)
                and len(item) == 2
                and type(item[0]) is int
                and isinstance(item[1], str)
            ):
                result.searches.append((item[0], item[1][:256]))
        return result

    def save(self, preferences: Preferences) -> None:
        if self.path is None:
            return
        payload = json.dumps(
            {"collections": preferences.collections, "searches": preferences.searches},
            ensure_ascii=False,
        ).encode("utf-8")
        protected = WindowsDpapiSecretStore._protect(payload)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_bytes(protected)
        temporary.replace(self.path)
