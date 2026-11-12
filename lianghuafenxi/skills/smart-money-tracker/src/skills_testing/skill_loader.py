"""Skill loader - parse YAML frontmatter and extract contracts from SKILL.md files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from skills_testing.models import SkillContract, SkillMetadata, ValidationResult


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter and body from markdown content."""
    pattern = r"^---\s*\n(.*?)---\s*\n(.*)$"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        msg = "No YAML frontmatter found"
        raise ValueError(msg)
    frontmatter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)
    return frontmatter, body


def load_skill(skill_path: Path) -> tuple[SkillMetadata, str]:
    """Load a single skill file and return metadata + body."""
    content = skill_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)
    metadata = SkillMetadata(**frontmatter)
    return metadata, body


def load_all_skills(skills_dir: Path) -> dict[str, tuple[SkillMetadata, str]]:
    """Load all skills from the skills directory."""
    skills = {}
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        try:
            metadata, body = load_skill(skill_file)
            skills[metadata.name] = (metadata, body)
        except (ValueError, yaml.YAMLError) as e:
            skills[skill_dir.name] = (None, f"ERROR: {e}")
    return skills


def validate_skill_contract(skill_name: str, metadata: SkillMetadata, body: str) -> ValidationResult:
    """Validate a skill against its declared contract."""
    errors = []
    warnings = []
    missing_sections = []
    forbidden_found = []

    contract = metadata.contracts

    for section in contract.required_sections:
        pattern = rf"^##\s+{re.escape(section.replace('_', ' '))}\b"
        if not re.search(pattern, body, re.MULTILINE | re.IGNORECASE):
            missing_sections.append(section)

    for pattern in contract.forbidden_patterns:
        if pattern.lower() in body.lower():
            forbidden_found.append(pattern)

    missing_tools = []

    passed = not missing_sections and not forbidden_found and not errors

    return ValidationResult(
        skill_name=skill_name,
        passed=passed,
        errors=errors,
        warnings=warnings,
        missing_sections=missing_sections,
        missing_tools=missing_tools,
        forbidden_found=forbidden_found,
    )


def get_skill_file_path(skills_dir: Path, skill_name: str) -> Path | None:
    """Get the file path for a skill by name."""
    skill_dir = skills_dir / skill_name
    skill_file = skill_dir / "SKILL.md"
    return skill_file if skill_file.exists() else None
