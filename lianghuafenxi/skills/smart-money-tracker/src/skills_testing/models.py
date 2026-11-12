"""Pydantic models for skill contract validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SkillContract(BaseModel):
    """Machine-verifiable contract declared in skill frontmatter."""

    required_sections: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    forbidden_patterns: list[str] = Field(default_factory=list)
    verification_required: bool = False
    decision_tree: dict[str, Any] | None = None


class SkillMetadata(BaseModel):
    """YAML frontmatter from a SKILL.md file."""

    name: str
    description: str
    contracts: SkillContract = Field(default_factory=SkillContract)


class ValidationResult(BaseModel):
    """Result of validating a skill against its contract."""

    skill_name: str
    passed: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    missing_sections: list[str] = Field(default_factory=list)
    missing_tools: list[str] = Field(default_factory=list)
    forbidden_found: list[str] = Field(default_factory=list)

    @field_validator("errors", "warnings", "missing_sections", "missing_tools", "forbidden_found")
    @classmethod
    def _ensure_list(cls, v: list[str]) -> list[str]:
        return v if v is not None else []
