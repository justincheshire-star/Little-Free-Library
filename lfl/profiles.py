"""
lfl.profiles — Embedding profile management.

Load and validate embedding profiles for reproducible corpus ingestion.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class EmbeddingProfile:
    """Embedding profile configuration."""
    id: str
    display_name: str
    description: str
    status: Literal["official", "experimental", "custom"]
    model_name: str
    format: Literal["onnx", "pytorch", "safetensors"]
    runtime: str
    runner: str
    dimensions: int
    max_seq_len: int
    pooling: Literal["cls", "mean", "max"]
    normalize: bool
    hardware: list[str]
    platforms: list[str]
    install: dict[str, list[str]]
    reproducibility: str
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "EmbeddingProfile":
        """Load profile from dictionary."""
        return cls(
            id=data["id"],
            display_name=data["display_name"],
            description=data["description"],
            status=data["status"],
            model_name=data["model_name"],
            format=data["format"],
            runtime=data["runtime"],
            runner=data["runner"],
            dimensions=data["dimensions"],
            max_seq_len=data["max_seq_len"],
            pooling=data["pooling"],
            normalize=data["normalize"],
            hardware=data["hardware"],
            platforms=data["platforms"],
            install=data["install"],
            reproducibility=data["reproducibility"],
            notes=data.get("notes", ""),
        )


def get_profiles_dir() -> Path:
    """Get the directory containing embedding profile JSONs."""
    return Path(__file__).parent / "profiles"


def load_profile(profile_id: str) -> EmbeddingProfile:
    """
    Load an embedding profile by ID.
    
    Parameters
    ----------
    profile_id : str
        Profile identifier (e.g., "baseline_cpu_onnx_small")
    
    Returns
    -------
    EmbeddingProfile
    
    Raises
    ------
    FileNotFoundError
        If the profile does not exist
    ValueError
        If the profile JSON is invalid
    """
    profiles_dir = get_profiles_dir()
    profile_path = profiles_dir / f"{profile_id}.json"
    
    if not profile_path.exists():
        raise FileNotFoundError(
            f"Profile '{profile_id}' not found. "
            f"Expected at: {profile_path}"
        )
    
    try:
        data = json.loads(profile_path.read_text(encoding="utf-8"))
        return EmbeddingProfile.from_dict(data)
    except Exception as e:
        raise ValueError(f"Invalid profile JSON for '{profile_id}': {e}") from e


def list_profiles() -> list[str]:
    """
    List all available embedding profile IDs.
    
    Returns
    -------
    list[str]
        Sorted list of profile IDs
    """
    profiles_dir = get_profiles_dir()
    if not profiles_dir.exists():
        return []
    
    return sorted(
        p.stem for p in profiles_dir.glob("*.json")
    )


def get_default_profile() -> EmbeddingProfile:
    """
    Get the default embedding profile (baseline_cpu_onnx_small).
    
    Returns
    -------
    EmbeddingProfile
    """
    return load_profile("baseline_cpu_onnx_small")
