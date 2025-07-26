from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from sql_optimizer import explain_sql_query, benchmark_queries, get_mysql_connection
from sql_validator import validate_sql_query
from check_pql import suggest_pql_optimizations
from check_jql import suggest_jql_optimizations
import os
import getpass
import json

class GeneratorChain:
    def __init__(self, llm=None):
        self.classify_chain = LLMChain(
            llm=llm or OpenAI(),
            prompt=PromptTemplate.from_dict({
                "input_variables": ["question", "routing_details"],
                "template": "You are a query classifier. Given the following question and routing details, classify the data source of the query.\n\nQuestion: {question}\n\nRouting Details: {routing_details}\n\nRespond ONLY with 'SQL', 'PromQL', 'JiraQL', 'Text', or 'abort' if the question is unrelated."
            })
        )
        self.generate_chain = LLMChain(
            llm=llm or OpenAI(),
            prompt=PromptTemplate.from_dict({
                "input_variables": ["question", "schema", "query_type"],
                "template": "You are a query generator. Given the following question, schema, and query_type, generate the query. \n\nQuestion: {question}\n\nSchema: {schema}\n\nQuery_Type: {query_type}\n\nRespond ONLY with the query."
            })
        )

    def run(self, question, schemas, routing_details):
        query_type = self.classify_chain({"question": question, "routing_details": routing_details})
        if query_type.lower() == "sql":
            query = self.generate_chain({"question": question, "schema": schemas["sql"], "query_type": query_type})
        elif query_type.lower() == "pql":
            query = self.generate_chain({"question": question, "schema": schemas["pql"], "query_type": query_type})
        elif query_type.lower() == "jql":
            query = self.generate_chain({"question": question, "schema": schemas["jql"], "query_type": query_type})
        else:
            raise Exception("Query type not identified")

        return query, query_type

class OptimizationChain:
    def __init__(self, llm=None):
        self.sql_optimize_chain = LLMChain(
            llm=llm or OpenAI(),
            prompt=PromptTemplate.from_dict({
                "input_variables": ["query", "execution_plan"],
                "template": "Optimize the following SQL query: {query} given the execution plan: {execution_plan}"
            })
        )
        self.sql_validate_chain = LLMChain(
            llm=llm or OpenAI(),
            prompt=PromptTemplate.from_dict({
                "input_variables": ["query"],
                "template": "Validate the following SQL query: {query}. ONLY respond with 'Yes' or 'No'"
            })
        )
        self.promql_chain = LLMChain(
            llm=llm or OpenAI(),
            prompt=PromptTemplate.from_dict({
                "input_variables": ["query", "optimization_suggestions"],
                "template": "Optimize the following PromQL query: {query}"
            })
        )
        self.jiraql_chain = LLMChain(
            llm=llm or OpenAI(),
            prompt=PromptTemplate.from_dict({
                "input_variables": ["query", "optimization_suggestions"],
                "template": "Optimize the following JiraQL query: {query}"
            })
        )

    def run(self, data):
        query = data.get("query")
        query_type = data.get("query_type", "sql").lower()

        if query_type.lower() == "sql":
            execution_plan = explain_sql_query(query)
            data["optimized_query"] = self.sql_optimize_chain.run({"query": query, "execution_plan": execution_plan})
            query_integrity = self.sql_validate_chain.run({"query": data["optimized_query"]})
            query_integrity = query_integrity and validate_sql_query(data["optimized_query"])
            if not query_integrity:
                raise Exception("This SQL query is not safe")

        elif query_type.lower() == "promql":
            optimization_suggestions = suggest_pql_optimizations(query)
            data["optimized_query"] = self.promql_chain.run({"query": query, "optimization_suggestions": optimization_suggestions})
        elif query_type.lower() == "jiraql":
            optimization_suggestions = suggest_jql_optimizations(query)
            data["optimized_query"] = self.jiraql_chain.run({"query": query, "optimization_suggestions": optimization_suggestions})
        else:
            raise ValueError(f"Unknown query_type: {query_type}")

        return data

if __name__ == "__main__":
    llm = OpenAI()
    generator_chain = GeneratorChain()
    optimization_chain = OptimizationChain()
    question = ""
    schemas = {}
    with open("sql_schema.txt", "r") as f:
        schemas["sql"] = f.read()
    
    with open("pql_schema.txt", "r") as f:
        schemas["pql"] = json.dumps(f.read())
    
    with open("jql_schema.txt", "r") as f:
        schemas["jql"] = json.dumps(f.read())

    with open("routing_details.txt", "r") as f:
        routing_details = f.read()

    query, query_type = generator_chain.run(question, schemas, routing_details)
    final_output = optimization_chain.run({"query": query, "query_type": query_type})

    print(final_output)


    