"""Agent OS layered configuration loading.

Precedence (lowest → highest):
1. Packaged defaults (installed with library)
2. User global overrides (e.g. macOS: ~/Library/Application Support/EvoSuite/agent-os)
3. Workspace overrides (project root: .agent-os/)
4. Environment variable overrides (EVOSUITE_AGENT_OS_*)

Merging strategy:
- Dicts: deep merge (later layers override scalar values, extend lists uniquely)
- Lists: later layer items appended if not duplicate
- Scalars: last layer wins

Provides single entry point: load_agent_os_config(root_path: Path) -> dict
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json
import os
import sys

try:  # Optional dependency guard
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # type: ignore

CONFIG_FILENAMES = ["config.yaml", "config.yml", "config.json"]


def _platform_user_config_root() -> Path:
    """Return the user-level base directory for global Agent OS config.

    macOS: ~/Library/Application Support/EvoSuite/agent-os
    Linux: ~/.config/evosuite/agent-os
    Windows: %APPDATA%/EvoSuite/agent-os
    """
    home = Path.home()
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "EvoSuite" / "agent-os"
    elif sys.platform == "darwin":  # macOS
        base = home / "Library" / "Application Support" / "EvoSuite" / "agent-os"
    else:  # Linux / Unix
        base = home / ".config" / "evosuite" / "agent-os"
    return base


def _load_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        if path.suffix in (".yaml", ".yml") and yaml is not None:
            return yaml.safe_load(path.read_text()) or {}
        if path.suffix == ".json":
            return json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - logged upstream later
        return {"_error": f"Failed loading {path.name}: {exc}"}
    return {}


def _deep_merge(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in incoming.items():
        if k not in base:
            base[k] = v
            continue
        if isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        elif isinstance(base[k], list) and isinstance(v, list):
            existing = set(json.dumps(item, sort_keys=True) for item in base[k])
            for item in v:
                encoded = json.dumps(item, sort_keys=True)
                if encoded not in existing:
                    base[k].append(item)
                    existing.add(encoded)
        else:
            base[k] = v
    return base


def _collect_layer_config(dir_path: Path) -> dict:
    for name in CONFIG_FILENAMES:
        candidate = dir_path / name
        if candidate.exists():
            return _load_file(candidate)
    return {}


def _env_overrides() -> dict:
    prefix = "EVOSUITE_AGENT_OS_"
    overrides: Dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        path_str = key[len(prefix) :].lower()  # e.g. LOG_LEVEL or SAMPLING__MAX_PARALLEL
        parts = path_str.split("__")
        target = overrides
        for p in parts[:-1]:
            target = target.setdefault(p, {})  # type: ignore
        leaf = parts[-1]
        # Basic type coercion
        if value.isdigit():
            coerced: Any = int(value)
        elif value.lower() in {"true", "false"}:
            coerced = value.lower() == "true"
        else:
            try:
                coerced = json.loads(value)
            except Exception:
                coerced = value
        target[leaf] = coerced  # type: ignore
    return overrides


def load_agent_os_config(workspace_root: Path) -> dict:
    """Load layered Agent OS configuration.

    Args:
        workspace_root: Path to project root containing optional .agent-os/
    Returns:
        Merged configuration dictionary with provenance markers.
    """
    merged: Dict[str, Any] = {"_provenance": []}

    # 1. Packaged defaults (relative to this file: defaults/config.*)
    pkg_defaults_dir = Path(__file__).parent / "defaults"
    defaults_cfg = _collect_layer_config(pkg_defaults_dir)
    if defaults_cfg:
        _deep_merge(merged, defaults_cfg)
        merged["_provenance"].append("package")

    # 2. User global overrides
    user_dir = _platform_user_config_root()
    user_cfg = _collect_layer_config(user_dir)
    if user_cfg:
        _deep_merge(merged, user_cfg)
        merged["_provenance"].append(str(user_dir))

    # 3. Workspace overrides
    ws_dir = workspace_root / ".agent-os"
    ws_cfg = _collect_layer_config(ws_dir)
    if ws_cfg:
        _deep_merge(merged, ws_cfg)
        merged["_provenance"].append(str(ws_dir))

    # 4. Environment overrides
    env_cfg = _env_overrides()
    if env_cfg:
        _deep_merge(merged, env_cfg)
        merged["_provenance"].append("env")

    return merged


__all__ = ["load_agent_os_config"]