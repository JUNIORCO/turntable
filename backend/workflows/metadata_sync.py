import tempfile

from hatchet_sdk import Context

from app.core.e2e import DataHubDBParser
from app.models import Resource
from app.models.resources import ResourceSubtype
from workflows.hatchet import hatchet
from workflows.utils.log import inject_workflow_run_logging
from workflows.utils.debug import spawn_workflow
from workflows.generate_docs import GenerateDocsWorkflow

@hatchet.workflow(on_events=["metadata_sync"], timeout="15m")
@inject_workflow_run_logging(hatchet)
class MetadataSyncWorkflow:
    """
    input structure:
        {
            resource_id: str,
            workunits: Optional[int],
            ai_options: Optional[dict(
                llm_api_key: str,
                model_name: str,
                max_columns_per_batch: Optional[int],
                max_ai_workers: Optional[int],
            )]
        }
    """

    @hatchet.step(timeout="30m")
    def prepare_dbt_repos(self, context: Context):
        resource = Resource.objects.get(id=context.workflow_input()["resource_id"])
        for dbt_repo in resource.dbtresource_set.all():
            if dbt_repo.subtype == ResourceSubtype.DBT:
                dbt_repo.upload_artifacts()

    @hatchet.step(timeout="120m", parents=["prepare_dbt_repos"])
    def ingest_metadata(self, context: Context):
        resource = Resource.objects.get(id=context.workflow_input()["resource_id"])
        workunits = context.workflow_input().get("workunits")
        workflow_run_id = context.workflow_run_id()
        resource.details.run_datahub_ingest(
            workflow_run_id=workflow_run_id, workunits=workunits
        )

    @hatchet.step(timeout="120m", parents=["ingest_metadata"])
    def process_metadata(self, context: Context):
        resource_id = context.workflow_input()["resource_id"]
        resource = Resource.objects.get(id=resource_id)
        ai_options = context.workflow_input().get("ai_options")
        with resource.datahub_db.open("rb") as f:
            with tempfile.NamedTemporaryFile(
                "wb", delete=False, suffix=".duckdb"
            ) as f2:
                f2.write(f.read())
                parser = DataHubDBParser(resource, f2.name)
                parser.parse()

        DataHubDBParser.combine_and_upload([parser], resource)

        if ai_options:
            payload = {
                "resource_id": str(resource.id),
                "ai_options": ai_options,
            }
            print("CALLING GenerateDocsWorkflow")
            spawn_workflow(context, GenerateDocsWorkflow, payload)
