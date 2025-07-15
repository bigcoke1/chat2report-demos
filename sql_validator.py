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

class Users(BaseModel):
    username : str
    password : str

class Executor:
    def __init__(self, authorization_level=3):
        self.authorization_level = authorization_level
    

curr_executor = Executor(authorization_level=4)
result = {}
for query in sql_queries:
    if any(banned_phrase in query.lower() for banned_phrase in BANNED_PHRASES):
        result[query] = False
        continue
    columns = parse_one(query).find_all(exp.Column)
    columns = [c.alias_or_name for c in columns]
    print(columns, "")
    for c in columns:
        if SENTSITIVITY_LEVELS[c] > curr_executor.authorization_level:
            result[query] = False
        else:
            result[query] = True

print(result)
