from sqlglot import parse_one, optimizer
import json
import time
import mysql.connector
import os


def explain_sql_query(query):
    """
    Returns the execution plan for a SQL query.
    """
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute(f"EXPLAIN {query}")
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error explaining query: {e}")
        return None

def optimize_sql_query(query):
    """
    Optimizes a SQL query using sqlglot's optimizer.
    Returns the optimized query as a string.
    """
    try:
        parsed_query = parse_one(query, read="mysql")
        optimized_query = optimizer.optimize(parsed_query)
        optimized_query = optimized_query.sql(dialect="mysql")
        return str(optimized_query)
    except Exception as e:
        print(f"Error optimizing query: {e}")
        return query

def time_query(cursor, sql, repeats=5, discard_first=True):
    times = []
    for i in range(repeats):
        start = time.time()
        cursor.execute(sql)
        cursor.fetchall()
        times.append(time.time() - start)
    if discard_first and len(times) > 1:
        times = times[1:]            # drop first (cache‐warm) run
    return sum(times) / len(times)

def get_mysql_connection():
    """
    Returns a MySQL connection object.
    """
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.getenv("MYSQL_ROOT_PASSWORD"),
        database="Chinook"
    )

def load_sql_queries(file_path):
    """
    Loads SQL queries from a JSON file.
    Returns a list of queries.
    """
    with open(file_path, "r") as file:
        data = json.load(file)
    return data["queries"] if "queries" in data else []

def benchmark_queries(queries):
    """
    Benchmarks a list of SQL queries by optimizing them and printing the results.
    """
    conn = get_mysql_connection()
    cursor = conn.cursor()
    for query in queries:
        print(f"\n Query name: {query['name']}")
        print(f"\n🔍 Original Query:\n  {query['query']}")
        optimized_query = optimize_sql_query(query['query'])
        print(f"💡 Optimized Query:\n  {optimized_query}")

        original_execution_time = time_query(cursor, query['query'])
        print("Original query execution time: " + str(original_execution_time))
        cursor.fetchall() 

        optimized_execution_time = time_query(cursor, optimized_query)
        print("Optimized query execution time: " + str(optimized_execution_time))
        cursor.fetchall()

    cursor.close()
    conn.close()

if __name__ == "__main__":
    queries = load_sql_queries("sql_queries.json")
    benchmark_queries(queries)