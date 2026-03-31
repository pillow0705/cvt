"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def tmp_out(tmp_path: Path) -> Path:
    """Temporary output directory."""
    return tmp_path


@pytest.fixture
def sample_json(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.json"


@pytest.fixture
def sample_yaml(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.yaml"


@pytest.fixture
def sample_toml(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.toml"


@pytest.fixture
def sample_csv(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.csv"


@pytest.fixture
def sample_md(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.md"


@pytest.fixture
def sample_html(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.html"


@pytest.fixture
def sample_txt(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.txt"
