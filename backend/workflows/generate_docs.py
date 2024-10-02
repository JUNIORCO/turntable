from hatchet_sdk import Context

from app.models import Resource
from ai.documentation.orm import write_docs
from workflows.hatchet import hatchet
from workflows.utils.log import inject_workflow_run_logging


@hatchet.workflow(on_events=["generate_docs"], timeout="15m")
@inject_workflow_run_logging(hatchet)
class GenerateDocsWorkflow:
    """
    input structure:
        {
            resource_id: str,
            ai_options: dict(
                llm_api_key: str,
                model_name: str,
                max_columns_per_batch: Optional[int],
                max_ai_workers: Optional[int],
            )
        }
    """

    @hatchet.step(timeout="180m")
    def generate_docs(self, context: Context):
        print("running GenerateDocsWorkflow workflow")
        input_data = context.workflow_input()
        resource_id = input_data["resource_id"]
        ai_options = input_data["ai_options"]
        write_docs(resource_id=resource_id, **ai_options)
