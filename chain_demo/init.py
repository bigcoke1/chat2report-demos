import os
import json
from langchain_aws import ChatBedrockConverse

def init_llm():
    model = ChatBedrockConverse(
        model_id=os.getenv("LLM_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"),
        region_name=os.getenv("AWS_REGION", "us-west-2"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    return model

def init_schemas():
    schemas = {}
    with open("./chain_demo/sql_schema.txt", "r") as f:
        schemas["sql"] = f.read()

    with open("./chain_demo/pql_schema.json", "r") as f:
        schemas["pql"] = json.dumps(f.read())

    with open("./chain_demo/jql_schema.json", "r") as f:
        schemas["jql"] = json.dumps(f.read())

    return schemas

def init_routing_details():
    with open("./chain_demo/routing_details.txt", "r") as f:
        routing_details = f.read()
    return routing_details

schemas = init_schemas()
llm = init_llm()
routing_details = init_routing_details()

