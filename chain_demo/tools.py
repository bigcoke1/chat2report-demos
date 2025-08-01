from langchain.tools import Tool
from chains import ClassifierChain, GeneratorChain, OptimizationChain
from init import llm, schemas, routing_details

classify_chain = ClassifierChain(llm=llm, routing_details=routing_details)
# Initialize the generator and optimization chains for each query type
sql_chain = GeneratorChain(llm=llm, query_type="sql", schemas=schemas, routing_details=routing_details)
jira_chain = GeneratorChain(llm=llm, query_type="jiraql", schemas=schemas, routing_details=routing_details)
prom_chain = GeneratorChain(llm=llm, query_type="pql", schemas=schemas, routing_details=routing_details)
sql_opt_chain = OptimizationChain(llm=llm, query_type="sql")
jira_opt_chain = OptimizationChain(llm=llm, query_type="jiraql")
prom_opt_chain = OptimizationChain(llm=llm, query_type="pql")

tools = [
    Tool(
        name="Datasource_Classifier",
        func=lambda q: classify_chain.run(q),
        description="Use this to map questions to their data source (SQL, JiraQL, PromQL)."
    ),
    Tool(
        name="SQL_Generator",
        func=lambda q: sql_chain.run(q),
        description="Use this to answer questions that need SQL queries."
    ),
    Tool(
        name="Jira_Generator",
        func=lambda q: jira_chain.run(q),
        description="Use this to answer Jira ticket related questions."
    ),
    Tool(
        name="Prometheus_Generator",
        func=lambda q: prom_chain.run(q),
        description="Use this to answer Prometheus query related questions."
    ),
    Tool(
        name="SQL_Optimizer",
        func=lambda q: sql_opt_chain.run(q),
        description="Use this to optimize SQL queries."
    ),
    Tool(
        name="Jira_Optimizer",
        func=lambda q: jira_opt_chain.run(q),
        description="Use this to optimize JiraQL queries."
    ),
    Tool(
        name="Prometheus_Optimizer",
        func=lambda q: prom_opt_chain.run(q),
        description="Use this to optimize PromQL queries."
    )
]