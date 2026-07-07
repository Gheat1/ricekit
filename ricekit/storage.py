"""XDG-flavoured state, cache, and config for an app — the cache-first doctrine.

Render from cache instantly, refresh in the background, and make every
mutation update the cache immediately so what the user sees is always what
they did.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path


class AppDirs:
    """Per-app file locations plus tiny JSON state/cache helpers.

    `save_state` MERGES a patch over what's on disk — callers never clobber
    keys owned by other features (a lesson learned the hard way).
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.state_file = Path.home() / ".local/state" / name / "state.json"
        self.cache_dir = Path.home() / ".cache" / name
        self.config_file = Path.home() / ".config" / name / "config.toml"

    # ── state ─────────────────────────────────────────────────────────
    def load_state(self) -> dict:
        try:
            return json.loads(self.state_file.read_text())
        except Exception:
            return {}

    def save_state(self, patch: dict) -> None:
        try:
            data = self.load_state()
            data.update(patch)
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(json.dumps(data))
        except Exception:
            pass

    # ── cache ─────────────────────────────────────────────────────────
    def read_cache(self, name: str) -> dict | None:
        try:
            return json.loads((self.cache_dir / f"{name}.json").read_text())
        except Exception:
            return None

    def write_cache(self, name: str, data: dict) -> None:
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            (self.cache_dir / f"{name}.json").write_text(json.dumps(data))
        except Exception:
            pass

    def clear_cache(self) -> int:
        count = 0
        try:
            for f in self.cache_dir.glob("*.json"):
                f.unlink()
                count += 1
        except Exception:
            pass
        return count

    # ── config ────────────────────────────────────────────────────────
    def load_config(self) -> dict:
        try:
            return tomllib.loads(self.config_file.read_text())
        except Exception:
            return {}

    def save_secret(self, key: str, value: str) -> None:
        """Write a single-value secret config (chmod 600)."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(f'{key} = "{value}"\n')
        self.config_file.chmod(0o600)
