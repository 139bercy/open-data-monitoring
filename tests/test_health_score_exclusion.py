from application.handlers import upsert_dataset


def test_health_score_exclusion_restricted(pg_app, pg_ods_platform, ods_dataset):
    # 1. Dataset normal (doit avoir un score)
    dataset_id = upsert_dataset(app=pg_app, platform=pg_ods_platform, dataset=ods_dataset)
    result = pg_app.dataset.repository.get_detail(dataset_id)
    assert result["health_score"] is not None

    # 2. Dataset restreint (ne doit PAS avoir de score)
    # Note: ODS adapter expects 'is_restricted' and 'is_published'
    restricted_dataset = {**ods_dataset, "uid": "restricted-ds", "dataset_id": "restricted-ds", "is_restricted": True}
    res_id = upsert_dataset(app=pg_app, platform=pg_ods_platform, dataset=restricted_dataset)

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
    unp_id = upsert_dataset(app=pg_app, platform=pg_ods_platform, dataset=unpublished_dataset)

    # Check via search
    items, total = pg_app.dataset.repository.search(q="unpublished-ds")
    assert total == 1
    assert items[0]["health_score"] is None

    # Check via get_detail
    detail = pg_app.dataset.repository.get_detail(unp_id)
    assert detail["health_score"] is None
