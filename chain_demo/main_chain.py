from langchain.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrockConverse
from sql_optimizer import explain_sql_query, execute_sql_query
from sql_validator import validate_sql_query
from check_pql import suggest_pql_optimizations
from check_jql import suggest_jql_optimizations
import os
import json

class GeneratorChain:
    def __init__(self, llm=None):
        self.classify_chain = (
            ChatPromptTemplate.from_template(
                "You are a query classifier. Given the following question and routing details, classify the data source of the query.\n\nQuestion: {question}\n\nRouting Details: {routing_details}\n\nRespond ONLY with 'SQL', 'PromQL', 'JiraQL', 'Text', or 'abort' if the question is unrelated."
            ) | llm
        )
        self.generate_chain = (
            ChatPromptTemplate.from_template(
                "You are a query generator. Given the following question, schema, and query_type, generate the query. \n\nQuestion: {question}\n\nSchema: {schema}\n\nQuery_Type: {query_type}\n\nRespond ONLY with the query."
            ) | llm
        )

    def run(self, question, schemas, routing_details):
        query_type = self.classify_chain.invoke({"question": question, "routing_details": routing_details}).content.strip().lower()
        print(f"Query type identified as: {query_type}")
        if query_type == "sql":
            query = self.generate_chain.invoke({"question": question, "schema": schemas["sql"], "query_type": query_type})
        elif query_type == "pql":
            query = self.generate_chain.invoke({"question": question, "schema": schemas["pql"], "query_type": query_type})
        elif query_type == "jql":
            query = self.generate_chain.invoke({"question": question, "schema": schemas["jql"], "query_type": query_type})
        else:
            raise Exception("Query type not identified")
        query = query.content.strip()
        print(f"Generated query: {query}")
        return query, query_type

class OptimizationChain:
    def __init__(self, llm=None):
        self.sql_optimize_chain = (
            ChatPromptTemplate.from_template(
                "Optimize the following SQL query: {query} given the execution plan: {execution_plan}. RESPOND ONLY with the optimized query or the original query if it's already optimized."
            ) | llm
        )
        self.sql_validate_chain = (
            ChatPromptTemplate.from_template(
                "Validate the following SQL query: {query}. ONLY respond with 'Yes' or 'No'. RESPOND ONLY with 'Yes' if the query is safe and valid, otherwise respond with 'No'."
            ) | llm
        )
        self.promql_chain = (
            ChatPromptTemplate.from_template(
                "Optimize the following PromQL query: {query} given the optimization suggestions: {optimization_suggestions}. RESPOND ONLY with the optimized query."
            ) | llm
        )
        self.jiraql_chain = (
            ChatPromptTemplate.from_template(
                "Optimize the following JiraQL query: {query} given the optimization suggestions: {optimization_suggestions}. RESPOND ONLY with the optimized query."
            ) | llm
        )

    def run(self, data):
        query = data.get("query")
        query_type = data.get("query_type", "sql").lower()

        if query_type == "sql":
            execution_plan = explain_sql_query(query)
            print(f"Execution plan for the query: {execution_plan}")
            data["optimized_query"] = self.sql_optimize_chain.invoke({"query": query, "execution_plan": execution_plan}).content.strip()
            # query_integrity = self.sql_validate_chain.invoke({"query": data["optimized_query"]})["text"].strip().lower() == "yes"
            # query_integrity = query_integrity and validate_sql_query(data["optimized_query"]["text"].strip())
            # if not query_integrity:
            #     raise Exception("This SQL query is not safe")

        elif query_type == "promql":
            optimization_suggestions = suggest_pql_optimizations(query)
            data["optimized_query"] = self.promql_chain.invoke({"query": query, "optimization_suggestions": optimization_suggestions}).content.strip()
        elif query_type == "jql":
            optimization_suggestions = suggest_jql_optimizations(query)
            data["optimized_query"] = self.jiraql_chain.invoke({"query": query, "optimization_suggestions": optimization_suggestions}).content.strip()
        else:
            raise ValueError(f"Unknown query_type: {query_type}")

        print(f"Final optimized query: {data['optimized_query']}")
        return data

def init_llm():
    model = ChatBedrockConverse(
        model_id=os.getenv("LLM_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"),
        region_name=os.getenv("AWS_REGION", "us-west-2"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )
    return model

if __name__ == "__main__":
    llm = init_llm()
    generator_chain = GeneratorChain(llm=llm)
    optimization_chain = OptimizationChain(llm=llm)
    question = "Which customers from the United States have spent more than $10 in total?"
    schemas = {}
    with open("./chain_demo/sql_schema.txt", "r") as f:
        schemas["sql"] = f.read()

    with open("./chain_demo/pql_schema.json", "r") as f:
        schemas["pql"] = json.dumps(f.read())

    with open("./chain_demo/jql_schema.json", "r") as f:
        schemas["jql"] = json.dumps(f.read())

    with open("./chain_demo/routing_details.txt", "r") as f:
        routing_details = f.read()

    query, query_type = generator_chain.run(question, schemas, routing_details)
    final_output = optimization_chain.run({"query": query, "query_type": query_type})

    print(final_output)

    optimized_query = final_output.get("optimized_query")
    if query_type == "sql":
        result = execute_sql_query(optimized_query)
        for row in result:
            print(row)