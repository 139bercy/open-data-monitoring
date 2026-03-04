import pytest
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from domain.datasets.aggregate import Dataset
from domain.datasets.kpis import DiscoverabilityKPI, ImpactKPI


def test_discoverability_kpi_seo_score():
    # Title with 7 words (perfect score)
    dataset = Dataset(
        id=uuid4(),
        platform_id=uuid4(),
        buid="test",
        slug="test-slug",
        title="Ceci est un titre de sept mots exactement",
        page="https://example.com",
        created=datetime.now(timezone.utc),
        modified=datetime.now(timezone.utc),
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw={}
    )
    
    kpi = dataset.calculate_discoverability_kpi()
    assert kpi.seo_score == 100.0


def test_discoverability_kpi_seo_score_short():
    # Title with 2 words (short score)
    dataset = Dataset(
        id=uuid4(),
        platform_id=uuid4(),
        buid="test",
        slug="test-slug",
        title="Titre court",
        page="https://example.com",
        created=datetime.now(timezone.utc),
        modified=datetime.now(timezone.utc),
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw={}
    )
    
    kpi = dataset.calculate_discoverability_kpi()
    # distance = abs(2-5) = 3. Score = 100 - (3 * 20) = 40.
    assert kpi.seo_score == 40.0


def test_impact_kpi_engagement_rate():
    dataset = Dataset(
        id=uuid4(),
        platform_id=uuid4(),
        buid="test",
        slug="test-slug",
        title="Test",
        page="https://example.com",
        created=datetime.now(timezone.utc),
        modified=datetime.now(timezone.utc),
        published=True,
        restricted=False,
        downloads_count=100,
        api_calls_count=500,
        views_count=1000,
        reuses_count=50,
        raw={}
    )
    
    kpi = dataset.calculate_impact_kpi()
    assert kpi.engagement_rate == 0.05  # 50 / 1000
    assert kpi.usage_intensity == 0.8333333333333334  # 500 / 600
