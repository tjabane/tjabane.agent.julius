from __future__ import annotations

import os

from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

CONTAINERS = (
    "sessions",
    "schedules",
    "reports",
    "memory",
    "skills",
)


def main() -> None:
    load_dotenv()

    connection_string = os.environ["COSMOS_CONNECTION_STRING"]
    database_name = os.environ.get("COSMOS_DATABASE", "krabs")

    client = CosmosClient.from_connection_string(connection_string)
    database = client.create_database_if_not_exists(id=database_name)

    for container_name in CONTAINERS:
        database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path="/id"),
        )
        print(f"ready: {database_name}/{container_name}")


if __name__ == "__main__":
    main()
