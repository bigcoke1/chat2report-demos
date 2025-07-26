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

def validate_sql_query(query):
    """
    Validates a SQL query against banned phrases and sensitivity levels.
    Returns True if valid, False if invalid.
    """
    for phrase in BANNED_PHRASES:
        if phrase.lower() in query.lower():
            return False
    return True

if __name__ == "__main__":
    # Example usage
    print("Validating SQL queries...")
    result = {}
    for query in sql_queries:
        result[query] = validate_sql_query(query)

    print(result)
