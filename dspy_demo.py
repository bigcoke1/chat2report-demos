import os
import json
import dspy
from dspy.teleprompt import BootstrapFewShotWithRandomSearch

# Set up LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

lm = dspy.LM('gemini/gemini-2.5-flash', api_key=GEMINI_API_KEY)
dspy.configure(lm=lm)

# Example schema (replace with real one)
SCHEMA = """
CREATE TABLE usage (
    company VARCHAR,
    storage_gb INT,
    engine VARCHAR
);
"""

# DSPy signature
class GenerateSQL(dspy.Signature):
    question = dspy.InputField()
    table_schema = dspy.InputField()
    sql_query = dspy.OutputField()

class SQLGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generator = dspy.Predict(GenerateSQL)  # this wraps the LM with your signature

    def forward(self, question, table_schema):
        return self.generator(question=question, table_schema=table_schema)

# Simple training set
training_set = [
    dspy.Example(
        question="Which company uses the most storage?",
        table_schema=SCHEMA,
        sql_query="SELECT company FROM usage ORDER BY storage_gb DESC LIMIT 1;"
    ),
    dspy.Example(
        question="List top 3 TiKV users by storage.",
        table_schema=SCHEMA,
        sql_query="SELECT company FROM usage WHERE engine='TiKV' ORDER BY storage_gb DESC LIMIT 3;"
    )
]
training_set = [ex.with_inputs("question", "table_schema") for ex in training_set]

# Metric function
def exact_match(pred, ex, trace=None):
    return pred.sql_query.strip() == ex.sql_query.strip()

# Bootstrap and test
def main():
    teleprompter = BootstrapFewShotWithRandomSearch(
        metric=exact_match
    )
    module = teleprompter.compile(student=SQLGenerator(), trainset=training_set)

    result = module(
        question="Who are the top 2 TiKV customers by storage?",
        table_schema=SCHEMA
    )

    print("Generated SQL:\n", result.sql_query)

    dspy.inspect_history(n=10)

if __name__ == "__main__":
    main()
