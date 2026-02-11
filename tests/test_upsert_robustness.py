from unittest.mock import MagicMock

from application.handlers import upsert_dataset


def test_upsert_dataset_sync_failed_new_dataset(app, ods_platform):
    """
    Test that upsert_dataset handles a 'failed' sync status correctly
    when the dataset does not yet exist in the database (regression test for 500 error).
    """
    # 1. Arrange: Dataset with sync_status="failed" that is NOT in DB
    dataset_payload = {"slug": "non-existent-yet", "sync_status": "failed"}

    # Ensure repository returns None for this slug
    app.dataset.repository.get_id_by_slug = MagicMock(return_value=None)
    # Mock update_dataset_sync_status to verify it's NOT called
    app.dataset.repository.update_dataset_sync_status = MagicMock()

    # 2. Act
    # This should NOT raise TypeError: 'NoneType' object is not subscriptable
    result = upsert_dataset(app=app, platform=ods_platform, dataset=dataset_payload)

    # 3. Assert
    assert result is None
    app.dataset.repository.update_dataset_sync_status.assert_not_called()


def test_upsert_dataset_sync_failed_existing_dataset(app, ods_platform):
    """
    Test that upsert_dataset handles a 'failed' sync status correctly
    when the dataset already exists in the database.
    """
    # 1. Arrange: Dataset with sync_status="failed" that IS in DB
    existing_id = "2036df3d-e306-448f-b414-d1b1a145cfe9"
    dataset_payload = {"slug": "existing-dataset", "sync_status": "failed"}

    app.dataset.repository.get_id_by_slug = MagicMock(return_value=existing_id)
    app.dataset.repository.update_dataset_sync_status = MagicMock()

    # 2. Act
    upsert_dataset(app=app, platform=ods_platform, dataset=dataset_payload)

    # 3. Assert
    app.dataset.repository.update_dataset_sync_status.assert_called_once_with(
        platform_id=ods_platform.id, dataset_id=existing_id, status="failed"
    )
