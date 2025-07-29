import re

# Known expensive fields and functions
SLOW_FIELDS = ["labels", "description", "comment", "text"]
SLOW_FUNCTIONS = ["portfolioChildIssuesOf", "issueFunction"]

def suggest_jql_optimizations(jql_query: str):
    suggestions = []
    normalized = jql_query.lower()

    # 1. Check for missing project scope
    if "project" not in normalized:
        suggestions.append("⚠️ Add `project = X` or `project in (...)` to reduce search scope.")

    # 2. Detect slow fields
    for field in SLOW_FIELDS:
        if field in normalized:
            suggestions.append(f"⚠️ Field `{field}` may slow down queries. Try to avoid or replace if possible.")

    # 3. Detect slow functions
    for func in SLOW_FUNCTIONS:
        if func in normalized:
            suggestions.append(f"⚠️ Function `{func}` is expensive. Consider alternatives or avoid recursive structures.")

    # 4. Detect top-level AND combinations
    if " and " in normalized and " or " in normalized:
        suggestions.append("💡 Consider rewriting the query to use `OR` at the top level and group `AND` clauses in subgroups.")

    # 5. Detect overly generic queries
    if "assignee" in normalized and "project" not in normalized:
        suggestions.append("⚠️ Filtering by assignee without project scope may result in a slow query.")

    # 6. Clause-by-clause build suggestion
    if len(jql_query.split("AND")) + len(jql_query.split("OR")) > 4:
        suggestions.append("💡 Build the query clause-by-clause to detect which parts are slow.")

    return str(suggestions)

if __name__ == "__main__":
    # Example JQLs to test
    test_queries = [
        "assignee = currentUser()",
        "project in (TIS, PMO) OR assignee in (A, B)",
        "(project = TIS OR assignee = A) AND (project = PMO OR assignee = B)",
        "labels in (urgent, critical) AND portfolioChildIssuesOf(PROJ-123)",
        "text ~ 'failure' AND assignee = jdoe"
    ]

    for q in test_queries:
        print(f"\n🔍 Analyzing JQL:\n  {q}")
        for s in suggest_jql_optimizations(q):
            print(s)
