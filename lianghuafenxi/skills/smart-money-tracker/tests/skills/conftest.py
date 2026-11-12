import pytest
from pathlib import Path

from skills_testing.skill_loader import load_all_skills, load_skill

SKILLS_DIR = Path("/home/agent/.config/opencode/skills")


@pytest.fixture(scope="session")
def skills_dir():
    return SKILLS_DIR


@pytest.fixture(scope="session")
def all_skills():
    return load_all_skills(SKILLS_DIR)


@pytest.fixture
def skill_by_name(all_skills):
    def _get(name):
        return all_skills.get(name, (None, None))
    return _get


@pytest.fixture(scope="session")
def contracted_skills(all_skills):
    return {
        name: (meta, body)
        for name, (meta, body) in all_skills.items()
        if meta and meta.contracts and (
            meta.contracts.required_sections
            or meta.contracts.required_tools
            or meta.contracts.forbidden_patterns
            or meta.contracts.verification_required
        )
    }
