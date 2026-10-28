"""Project configuration and output-directory utilities."""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

INPUTS_DIR = Path("inputs")
OUTPUTS_DIR = Path("outputs")
DEFAULT_CONFIG_PATH = INPUTS_DIR / "config.toml"


def get_default_retmax() -> int:
    """Read the default maximum number of PubMed records to fetch."""
    raw = os.getenv("RETMAX", "100")
    try:
        result = int(raw)
    except ValueError as exc:
        raise ValueError("RETMAX must be a positive integer") from exc
    if result <= 0:
        raise ValueError("RETMAX must be a positive integer")
    return result


@dataclass
class Config:
    email: str = field(default_factory=lambda: os.getenv("ENTREZ_EMAIL", ""))
    retmax: int = field(default_factory=get_default_retmax)
    date_start: str | None = None
    date_end: str | None = None
    queries: list[str] | None = None
    queries_dir: str | None = None


def load_config(path: Path | str | None = None) -> Config:
    """Read and validate the TOML configuration."""
    config = Config()
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return config
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise TypeError("Configuration must be a TOML table")
    if "email" in data:
        if not isinstance(data["email"], str):
            raise ValueError("email must be a string")
        config.email = data["email"]
    if "retmax" in data:
        if type(data["retmax"]) is not int or data["retmax"] <= 0:
            raise ValueError("retmax must be a positive integer")
        config.retmax = data["retmax"]
    for key in ("date_start", "date_end", "queries_dir"):
        if key in data:
            if not isinstance(data[key], str):
                raise ValueError(f"{key} must be a string")
            setattr(config, key, data[key])
    if "queries" in data:
        if not isinstance(data["queries"], list) or not all(
            isinstance(query, str) for query in data["queries"]
        ):
            raise ValueError("queries must be a list of strings")
        config.queries = data["queries"]
    return config


def ensure_output_dir(base: Path | str = OUTPUTS_DIR) -> Path:
    path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    return path
