from init import init_llm
from tools import tools
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from typing import List

class QueryItem(BaseModel):
    query: str = Field(..., description="The generated or optimized query.")
    query_type: str = Field(..., description="The type of the query (SQL, JiraQL, PromQL).")

class Queries(BaseModel):
    question: str = Field(..., description="The question to be answered by generating queries.")
    query_type_to_queries: List[QueryItem] = Field(None, description="The generated query items if applicable.")

prompt = """
    You are a helpful assistant that can answer questions by generating and optimizing queries. 
    First, formulate a plan of how many queries to generate (break down the question into sub-questions if needed) and what tools to use. 
    Then, use the tools provided to generate and optimize SQL, JiraQL, and PromQL queries based on user questions. 
    Lastly, ONLY respond with the generated or optimized query/queries.
"""

def init_agent():
    llm = init_llm()
    agent = create_react_agent(
        tools=tools,
        model=llm,
        prompt=prompt,
        response_format=Queries
    )
    return agent

if __name__ == "__main__":
    question = "Which customers from the United States have spent more than $10 in total? And also, what is the total http requests in the last 24 hours?"
    agent = init_agent()

    final_state = agent.invoke(
        {"messages": [{"role": "user", "content": question}]}
    )
    for message in final_state["messages"]:
        print(message.content)