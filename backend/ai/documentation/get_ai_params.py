from typing import Literal

from pydantic import BaseModel, create_model
from app.models.metadata import Asset, Column
from ai.documentation.prompts import ASSET_SYSTEM_PROMPT, COLUMN_SYSTEM_PROMPT


class ModelDescription(BaseModel):
    description: str
    

class ColumnDescription(BaseModel):
    description: str


def get_asset_ai_params(
    asset: Asset,
    schema: str,
    model_name: Literal["gpt-4o-mini", "gpt-4o", "claude-3-haiku-20240307"],
):
    user_content = f"""Model name: {asset.name}
Schema:
{schema}
SQL: {asset.sql}
    """
    
    messages = [
        dict(
            role="system",
            content=ASSET_SYSTEM_PROMPT,
        ),
        dict(
            role="user",
            content=user_content,
        ),
    ]

    return dict(
        type="asset",
        id=asset.id,
        params=dict(
            model=model_name,
            messages=messages,
            response_model=ModelDescription,
            temperature=0,
            max_tokens=4000,
        )
    )


def get_column_ai_params(
    asset: Asset,
    columns: list[Column],
    schema: str,
    model_name: Literal["gpt-4o-mini", "gpt-4o", "claude-3-haiku-20240307"],
):  
    column_names = [column.name for column in columns]
    column_name_id_map = {column.name: column.id for column in columns}
    fields = {f"{k}": (ColumnDescription, ...) for k in column_names}
    ColumnDescriptionModel = create_model("ColumnDescriptionModel", **fields)
    
    user_content = f"""Model name: {asset.name}
Schema:
{schema}
SQL: {asset.sql}
Column names to describe: 
{column_names}
    """
    
    messages = [
        dict(
            role="system",
            content=COLUMN_SYSTEM_PROMPT,
        ),
        dict(
            role="user",
            content=user_content,
        ),
    ]

    return dict(
        type="column",
        id=asset.id,
        column_name_id_map=column_name_id_map,
        params=dict(
            model=model_name,
            messages=messages,
            response_model=ColumnDescriptionModel,
            strict=False,
            temperature=0,
            max_tokens=4000,
        )
    )
