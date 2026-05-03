"""Generates docs/architecture.png — run with: uv run python docs/architecture.py"""
from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.azure.compute import FunctionApps
from diagrams.azure.database import CosmosDb
from diagrams.azure.general import Usericon
from diagrams.azure.integration import APIManagement
from diagrams.azure.security import KeyVaults
from diagrams.onprem.client import Users
from diagrams.onprem.network import Internet

OUTPUT = str(Path(__file__).parent / "architecture")

graph_attr = {
    "fontsize": "13",
    "bgcolor": "white",
    "pad": "0.5",
    "splines": "ortho",
}

node_attr = {
    "fontsize": "11",
}

with Diagram(
    "Julius — Architecture",
    filename=OUTPUT,
    show=False,
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
):
    user = Users("User\n(WhatsApp)")
    twilio = Internet("Twilio\nWhatsApp Gateway")
    openai = Internet("OpenAI\nGPT-4o")
    investec = Internet("Investec\nPrivate Banking API")
    acs = APIManagement("Azure Communication\nServices (Email)")

    with Cluster("Azure Functions"):
        webhook = FunctionApps("webhook\nHTTP POST /webhook")
        scheduler = FunctionApps("scheduler\nTimer (every 5 min)")

    with Cluster("Azure CosmosDB — julius"):
        sessions = CosmosDb("sessions")
        schedules = CosmosDb("schedules")
        memories = CosmosDb("memories")
        skills = CosmosDb("skills")
        reports = CosmosDb("reports")

    keyvault = KeyVaults("Azure Key Vault")

    # Inbound message flow
    user >> Edge(label="WhatsApp") >> twilio
    twilio >> Edge(label="POST /webhook") >> webhook
    webhook >> Edge(label="reply", style="dashed") >> twilio
    twilio >> Edge(label="WhatsApp", style="dashed") >> user

    # Webhook → agent loop
    webhook >> Edge(label="run()") >> openai
    scheduler >> Edge(label="run_scheduled()") >> openai

    # Tool calls
    openai >> Edge(label="banking tools") >> investec
    openai >> Edge(label="read/write") >> sessions
    openai >> Edge(label="read/write") >> memories
    openai >> Edge(label="read/write") >> skills
    openai >> Edge(label="read/write") >> schedules
    openai >> Edge(label="send_email") >> acs
    openai >> Edge(label="write") >> reports

    # Scheduler reads due schedules
    scheduler >> Edge(label="list_due / save") >> schedules

    # Key Vault
    webhook >> Edge(style="dotted", color="gray") >> keyvault
    scheduler >> Edge(style="dotted", color="gray") >> keyvault
