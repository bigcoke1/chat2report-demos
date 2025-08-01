from langchain.prompts import ChatPromptTemplate
from sql_optimizer import explain_sql_query
from sql_validator import validate_sql_query
from check_pql import suggest_pql_optimizations
from check_jql import suggest_jql_optimizations

class ClassifierChain:
    def __init__(self, llm, routing_details):
        self.classify_chain = (
            ChatPromptTemplate.from_template(
                "You are a query classifier. Given the following question and routing details, classify the data source of the query.\n\nQuestion: {question}\n\nRouting Details: {routing_details}\n\nRespond ONLY with 'SQL', 'PromQL', 'JiraQL', 'Text', or 'abort' if the question is unrelated."
            ) | llm
        )
        self.routing_details = routing_details

    def run(self, question):
        return self.classify_chain.invoke({"question": question, "routing_details": self.routing_details}).content.strip().lower()

class GeneratorChain:
    def __init__(self, llm, schemas, routing_details=None, query_type=None):

        self.generate_chain = (
            ChatPromptTemplate.from_template(
                "You are a query generator. Given the following question, schema, and query_type, generate the query. \n\nQuestion: {question}\n\nSchema: {schema}\n\nQuery_Type: {query_type}\n\nRespond ONLY with the query."
            ) | llm
        )
        
        self.query_type = query_type.lower() if query_type else None
        self.schemas = schemas
        self.routing_details = routing_details

    def run(self, question):
        schemas = self.schemas
        routing_details = self.routing_details
        query_type = self.query_type or ClassifierChain().run(question, routing_details)
        if not schemas or not routing_details:
            raise ValueError("Schemas and routing details must be provided.")
        if not question:
            raise ValueError("Question must be provided.")
        if query_type not in ["sql", "pql", "jql"]:
            raise ValueError(f"Unknown query_type: {query_type}")
        
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
    def __init__(self, llm=None, query_type=None):
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
        self.query_type = query_type.lower() if query_type else None

    def run(self, query):
        query_type = self.query_type

        if query_type == "sql":
            execution_plan = explain_sql_query(query)
            print(f"Execution plan for the query: {execution_plan}")
            optimized_query = self.sql_optimize_chain.invoke({"query": query, "execution_plan": execution_plan}).content.strip()
            query_integrity = self.sql_validate_chain.invoke({"query": optimized_query}).content.strip().lower() == "yes"
            query_integrity = query_integrity and validate_sql_query(optimized_query)
            if not query_integrity:
                raise Exception("This SQL query is not safe")

        elif query_type == "promql":
            optimization_suggestions = suggest_pql_optimizations(query)
            optimized_query = self.promql_chain.invoke({"query": query, "optimization_suggestions": optimization_suggestions}).content.strip()
        elif query_type == "jql":
            optimization_suggestions = suggest_jql_optimizations(query)
            optimized_query = self.jiraql_chain.invoke({"query": query, "optimization_suggestions": optimization_suggestions}).content.strip()
        else:
            raise ValueError(f"Unknown query_type: {query_type}")

        print(f"Final optimized query: {optimized_query}")
        return query_type, optimized_query
