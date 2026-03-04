import pytest
from uuid import uuid4
from datetime import datetime
from domain.datasets.aggregate import Dataset
from domain.datasets.value_objects import DatasetQuality

def test_dataset_add_quality_calculates_syntax_score():
    # Setup dataset
    dataset_id = uuid4()
    platform_id = uuid4()
    old_raw = {"title": "Old Title", "description": "Old Desc"}
    new_raw = {"title": "New Title", "description": "Old Desc"} # Only title changed
    
    dataset = Dataset(
        id=dataset_id,
        platform_id=platform_id,
        buid="test-buid",
        slug="test-slug",
        title="New Title",
        page="http://example.com",
        created=datetime.now(),
        modified=datetime.now(),
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw=new_raw
    )
    
    # Add quality with previous_raw
    dataset.add_quality(
        downloads_count=10,
        api_calls_count=5,
        has_description=True,
        is_slug_valid=True,
        previous_raw=old_raw
    )
    
    assert dataset.quality.syntax_change_score is not None
    # Similarity should be between 0 and 100
    assert 0 <= dataset.quality.syntax_change_score <= 100
    # Title changed, desc stayed same. Score should be high but not 100.
    assert dataset.quality.syntax_change_score < 100.0
    assert dataset.quality.syntax_change_score > 50.0

def test_dataset_add_quality_without_previous_raw():
    # Setup dataset
    dataset = Dataset(
        id=uuid4(),
        platform_id=uuid4(),
        buid="test-buid",
        slug="test-slug",
        title="Title",
        page="http://example.com",
        created=datetime.now(),
        modified=datetime.now(),
        published=True,
        restricted=False,
        downloads_count=0,
        api_calls_count=0,
        raw={"title": "Title"}
    )
    
    dataset.add_quality(
        downloads_count=10,
        api_calls_count=5,
        has_description=True,
        is_slug_valid=True
    )
    
    assert dataset.quality.syntax_change_score is None
