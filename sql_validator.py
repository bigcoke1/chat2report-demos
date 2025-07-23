from sqlglot import parse_one, exp
from pydantic import BaseModel

BANNED_PHRASES = [
    # DML / Schema-altering
    "drop",
    "alter",
    "update",
    "delete",
    "insert",
    "create",
    "truncate",
    "replace",
    "rename",

    # Permissions and execution
    "grant",
    "revoke",
    "execute",
    "exec",
    "call",

    # SQL injection patterns
    "union select",
    "sleep",
    "benchmark",
    "--",
    "#",
    "/*",
    "*/",

    # File/server access
    "into outfile",
    "into dumpfile",
    "load_file",

    # Transaction control
    "begin",
    "commit",
    "rollback",
]

SENTSITIVITY_LEVELS = {"username": 5, "password": 5, "ticket": 3}

sql_queries = ["SELECT username, password FROM Users WHERE 1 = 1", "SELECT ticket FROM Errors", "DROP Users"]

class Executor:
    def __init__(self, authorization_level=3):
        self.authorization_level = authorization_level
    
def validate_sql_query(query, executor):
    """
    Validates a SQL query against banned phrases and sensitivity levels.
    Returns True if valid, False if invalid.
    """
    for phrase in BANNED_PHRASES:
        if phrase.lower() in query.lower():
            return False
    columns = parse_one(query).find_all(exp.Column)
    columns = [c.alias_or_name for c in columns]
    for c in columns:
        if SENTSITIVITY_LEVELS.get(c, 0) > executor.authorization_level:
            return False
    return True

if __name__ == "__main__":
    # Example usage
    print("Validating SQL queries...")
    result = {}
    curr_executor = Executor(authorization_level=4)
    for query in sql_queries:
        result[query] = validate_sql_query(query, curr_executor)

    print(result)
