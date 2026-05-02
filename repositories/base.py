from azure.cosmos import CosmosClient, ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from pydantic import BaseModel
import os


class BaseRepository:
    def __init__(self, container_name: str):
        client = CosmosClient.from_connection_string(os.environ["COSMOS_CONNECTION_STRING"])
        database = client.get_database_client(os.environ["COSMOS_DATABASE"])
        self._container: ContainerProxy = database.get_container_client(container_name)

    def _upsert(self, model: BaseModel) -> dict:
        data = model.model_dump(mode="json")
        return self._container.upsert_item(data)

    def _get(self, item_id: str, partition_key: str) -> dict | None:
        try:
            return self._container.read_item(item_id, partition_key=partition_key)
        except CosmosResourceNotFoundError:
            return None

    def _delete(self, item_id: str, partition_key: str) -> None:
        try:
            self._container.delete_item(item_id, partition_key=partition_key)
        except CosmosResourceNotFoundError:
            pass

    def _query(self, query: str, parameters: list[dict] | None = None) -> list[dict]:
        return list(self._container.query_items(
            query=query,
            parameters=parameters or [],
            enable_cross_partition_query=True,
        ))
