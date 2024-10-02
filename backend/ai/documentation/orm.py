from concurrent.futures import ThreadPoolExecutor

from ai.documentation.get_ai_params import get_asset_ai_params, get_column_ai_params
from ai.documentation.models import INSTRUCTOR_CLIENT_MAP
from app.models import Asset, Column


# TODO writing this out for the new implementation
def write_docs(resource_id: str, llm_api_key: str, model_name: str, max_columns_per_batch: int = 20, max_ai_workers: int = 20):
    instructor_client = INSTRUCTOR_CLIENT_MAP[model_name]
    instructor_client = instructor_client(llm_api_key)
    asset_requests = []
    column_requests = []
    
    asset_obs = Asset.objects.filter(resource_id=resource_id, type=Asset.AssetType.MODEL).prefetch_related("columns").all()
    column_objs = []
    column_map_id_to_idx = {}  # map column id to index in columns list, used for bulk update
    
    for asset in asset_obs:
        asset_cols = asset.columns.all()
        for idx, column in enumerate(asset_cols):
            column_map_id_to_idx[column.id] = idx

        column_objs.extend(asset_cols)
        schema = "\n".join([f"- {column.name}: {column.type}" for column in asset_cols])
        
        asset_ai_params = get_asset_ai_params(asset, schema, model_name)
        asset_requests.append(asset_ai_params)
        
        if len(asset_cols) > max_columns_per_batch:
            column_batches = [asset_cols[i:i + max_columns_per_batch] for i in range(0, len(asset_cols), max_columns_per_batch)]
            for batch in column_batches:
                column_ai_params = get_column_ai_params(asset, batch, schema, model_name)
                column_requests.append(column_ai_params)
        else:
            column_ai_params = get_column_ai_params(asset, asset_cols, schema, model_name)
            column_requests.append(column_ai_params)

    with ThreadPoolExecutor(max_workers=max_ai_workers) as executor:
        asset_results = list(executor.map(lambda r: process_ai_request(**r, instructor_client=instructor_client), asset_requests))
        column_results = list(executor.map(lambda r: process_ai_request(**r, instructor_client=instructor_client), column_requests))
    
        for idx, result in enumerate(asset_results):
            asset_obs[idx].ai_description = result["description"]
        
        for idx, result in enumerate(column_results):
            column_name_id_map = result["column_name_id_map"]
            for k, v in result["description"].items():
                column_objs[column_map_id_to_idx[column_name_id_map[k]]].ai_description = v
    
    batch_size = 5000
    Asset.objects.bulk_update(asset_obs, ["ai_description"], batch_size)
    Column.objects.bulk_update(column_objs, ["ai_description"], batch_size)


# TODO add query level caching here w/ redis
def process_ai_request(type: str, id: str, params: dict, column_name_id_map: dict[str, str], instructor_client) -> dict:
    response = instructor_client.chat.completions.create(**params)
    if type == "column":
        return dict(
            type=type,
            id=id,
            description={k: v["description"] for k, v in response.model_dump().items()},
            column_name_id_map=column_name_id_map
        )
    elif type == "asset":
        return dict(
            type=type,
            id=id,
            description=response.description
        )
    else:
        raise ValueError(f"Invalid type: {type}")
