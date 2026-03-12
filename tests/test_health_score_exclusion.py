from application.use_cases.sync_dataset import SyncDatasetCommand, SyncDatasetUseCase


def test_health_score_exclusion_restricted(pg_app, pg_ods_platform, ods_dataset):
    # 1. Dataset normal (doit avoir un score)
    result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id=ods_dataset["uid"], raw_data=ods_dataset)
    )
    dataset_id = result.dataset_id
    result = pg_app.dataset.repository.get_detail(dataset_id)
    assert result["health_score"] is not None

    # 2. Dataset restreint (ne doit PAS avoir de score)
    # Note: ODS adapter expects 'is_restricted' and 'is_published'
    restricted_dataset = {**ods_dataset, "uid": "restricted-ds", "dataset_id": "restricted-ds", "is_restricted": True}
    res_result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id="restricted-ds", raw_data=restricted_dataset)
    )
    res_id = res_result.dataset_id

    # Check via search
    items, total = pg_app.dataset.repository.search(q="restricted-ds")
    assert total == 1
    assert items[0]["health_score"] is None

    # Check via get_detail
    detail = pg_app.dataset.repository.get_detail(res_id)
    assert detail["health_score"] is None


def test_health_score_exclusion_unpublished(pg_app, pg_ods_platform, ods_dataset):
    # Dataset non publié (ne doit PAS avoir de score)
    unpublished_dataset = {
        **ods_dataset,
        "uid": "unpublished-ds",
        "dataset_id": "unpublished-ds",
        "is_published": False,
    }
    unp_result = SyncDatasetUseCase(uow=pg_app.uow).handle(
        SyncDatasetCommand(platform=pg_ods_platform, platform_dataset_id="unpublished-ds", raw_data=unpublished_dataset)
    )
    unp_id = unp_result.dataset_id

    # Check via search
    items, total = pg_app.dataset.repository.search(q="unpublished-ds")
    assert total == 1
    assert items[0]["health_score"] is None

    # Check via get_detail
    detail = pg_app.dataset.repository.get_detail(unp_id)
    assert detail["health_score"] is None
