from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
import os
import getpass

SENSITIVITY_TEMPLATE = """
- Log and audit each query with explicit authentication metadata
  - Public / Low Sensitivity
    - e.g., simple server uptime, pod status, ticket count
  - Internal / Medium Sensitivity
    - e.g., service error logs, internal performance metrics
  - Restricted / High Sensitivity
    - e.g., user data, credentials, security incidents, secrets
  - Critical
    - e.g., root-level server access, direct data modification queries
"""

class AbortableChain:
    def __init__(self, chains):
        self.chains = chains

    def run(self, input_data):
        data = input_data
        for chain in self.chains:
            output = chain.run(data)
            if isinstance(output, str) and output.lower() == "abort":
                print("Chain execution aborted.")
                return {"aborted": True, "final_output": None}
            data = output
        return {"aborted": False, "final_output": data}
    
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter your OpenAI API key: ")

llm = OpenAI()

prompt1 = PromptTemplate(
    input_variables=["question", "sensitivity_template"],
    template="You are a SQL query validator. Given the following question, determine the sensitivity of the data being accessed:\n\n{question}\n\nThe sensitivity template of the data is: {sensitivity_template}. Respond ONLY with the sensitivity level or 'abort'."
)

prompt2 = PromptTemplate(
    input_variables=["question", "sensitivity_level", "current_user_department"],
    template="You are a SQL query validator. Given the following question and sensitivity level, determine if the current user has permission to access the data:\n\n{question}\n\nSensitivity Level: {sensitivity_level}\n\nCurrent User Department: {current_user_department}\n\nRespond ONLY with 'yes' or 'abort'."
)

prompt3 = PromptTemplate(
    input_variables=["question"],
    template="You are a SQL query generator. Given the following question, generate the SQL query or 'abort'."
)

prompt4 = PromptTemplate(
    input_variables=["sql_query"],
    template="You are a SQL query validator. Given the following SQL query, determine if it is safe or 'abort'.\n\n{sql_query}\n\nRespond ONLY with 'valid' or 'abort'."
)

chain1 = LLMChain(llm=llm, prompt=prompt1)
chain2 = LLMChain(llm=llm, prompt=prompt2)
chain3 = LLMChain(llm=llm, prompt=prompt3)
chain4 = LLMChain(llm=llm, prompt=prompt4)

abortable_chain = AbortableChain(
    chains=[chain1, chain2, chain3, chain4]
)

result = abortable_chain.run({
    "question": "Who are the top 2 TiKV customers by storage?",
    "sensitivity_template": SENSITIVITY_TEMPLATE,
    "current_user_department": "Engineering"
})

print("Final Output:", result["final_output"])
if result["aborted"]:
    print("Chain execution was aborted.")