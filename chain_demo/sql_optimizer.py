from sqlglot import parse_one, optimizer
import json
import time
import mysql.connector
import os
import re

def strip_code_fencing(query):
    return re.sub(r"```(?:sql)?\s*", "", query).strip("` \n")

def execute_sql_query(query):
    """
    Executes a SQL query and returns the result.
    """
    query = strip_code_fencing(query)
    print(f"Executing query: {query}")
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error executing query: {e}")
        return None
    
def explain_sql_query(query):
    return execute_sql_query(f"EXPLAIN {query}")

def optimize_sql_query(query):
    """
    Optimizes a SQL query using sqlglot's optimizer.
    Returns the optimized query as a string.
    """
    query = strip_code_fencing(query)
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
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("""EXPLAIN SELECT
                        T1.FirstName,
                        T1.LastName
                        FROM Customer AS T1
                        INNER JOIN Invoice AS T2
                        ON T1.CustomerId = T2.CustomerId
                        WHERE
                        T1.Country = 'USA'
                        GROUP BY
                        T1.CustomerId,
                        T1.FirstName,
                        T1.LastName
                        HAVING
                        SUM(T2.Total) > 10;""")
        print("Executing query:")
        result = cursor.fetchall()
        for row in result:
            print(row)
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error executing query: {e}")