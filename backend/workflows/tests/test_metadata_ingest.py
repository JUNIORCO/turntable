import os
import pytest

from app.models import (
    Asset,
    Column,
    Resource,
)
from app.utils.test_utils import assert_ingest_output, require_env_vars
from workflows.metadata_sync import MetadataSyncWorkflow
from workflows.utils.debug import ContextDebugger, WorkflowDebugger


def run_test_sync(resources, recache: bool, use_cache: bool = False, ai_options: dict = None):
    for resource in resources:
        input = {
            "resource_id": resource.id,
        }
        
        if ai_options:
            input["ai_options"] = ai_options
        
        if use_cache:
            db_read_path = f"fixtures/datahub_dbs/{resource.details.subtype}.duckdb"
            with open(db_read_path, "rb") as f:
                resource.datahub_db.save(db_read_path, f, save=True)
            MetadataSyncWorkflow().process_metadata(ContextDebugger({"input": input}))
        else:
            WorkflowDebugger(MetadataSyncWorkflow, input).run()

    assert_ingest_output(resources)

    # recache datahub_dbs if successful and arg is passed
    if recache:
        for resource in Resource.objects.all():
            if resource.id in [r.id for r in resources]:
                with resource.datahub_db.open("rb") as f:
                    db_save_path = (
                        f"fixtures/datahub_dbs/{resource.details.subtype}.duckdb"
                    )
                    with open(db_save_path, "wb") as f2:
                        f2.write(f.read())
                        
    # if ai_options:
    #     # at least one asset has an ai_description
    #     assert Asset.objects.filter(ai_description__isnull=False).exists()
    #     # at least one column has an ai_description
    #     assert Column.objects.filter(ai_description__isnull=False).exists()


@pytest.mark.django_db
def test_metadata_sync(local_metabase, local_postgres, recache: bool, use_cache: bool):
    resources = [local_metabase, local_postgres]
    run_test_sync(resources, recache, use_cache)
    assert_ingest_output(resources)


@pytest.mark.django_db
@require_env_vars("OPENAI_API_KEY")
def test_metadata_sync_with_ai(local_metabase, local_postgres, recache: bool, use_cache: bool):
    resources = [local_metabase, local_postgres]
    ai_options = {
        "llm_api_key": os.environ["OPENAI_API_KEY"],
        "model_name": "gpt-4o-mini",
    }
    run_test_sync(resources, recache, use_cache, ai_options)
    assert_ingest_output(resources)
    

@pytest.mark.django_db
@require_env_vars("OPENAI_API_KEY")
def test_metadata_sync_with_batches(local_metabase, local_postgres, recache: bool, use_cache: bool):
    resources = [local_metabase, local_postgres]
    ai_options = {
        "llm_api_key": os.environ["OPENAI_API_KEY"],
        "model_name": "gpt-4o-mini",
        "max_columns_per_batch": 4,
        "max_ai_workers": 10,
    }
    run_test_sync(resources, recache, use_cache, ai_options)
    assert_ingest_output(resources)


@pytest.mark.django_db
@require_env_vars("BIGQUERY_0_WORKSPACE_ID")
def test_bigquery_sync(remote_bigquery, recache: bool, use_cache: bool):
    run_test_sync([remote_bigquery], recache, use_cache)


@pytest.mark.django_db
@require_env_vars("DATABRICKS_0_WORKSPACE_ID")
def test_databricks_sync(remote_databricks, recache: bool, use_cache: bool):
    run_test_sync([remote_databricks], recache, use_cache)


@pytest.mark.django_db
@require_env_vars("REDSHIFT_0_WORKSPACE_ID")
def test_redshift_sync(remote_redshift, recache: bool, use_cache: bool):
    run_test_sync([remote_redshift], recache, use_cache)


@pytest.mark.django_db
@require_env_vars("TABLEAU_0_USERNAME")
def test_tableau_sync(remote_tableau, recache: bool, use_cache: bool):
    run_test_sync([remote_tableau], recache, use_cache)
    

    
