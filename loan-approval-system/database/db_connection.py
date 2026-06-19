"""
MySQL Database Connection Pool.
Used by MCP servers when DATA_SOURCE = "mysql".

Provides:
- Connection pooling (5 connections)
- execute_query() helper for simple queries
"""
import mysql.connector
from mysql.connector import pooling
from config import MYSQL_CONFIG

_pool = None


def get_pool():
    """Get or create the MySQL connection pool."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="loan_pool",
            pool_size=5,
            **MYSQL_CONFIG
        )
    return _pool


def get_connection():
    """Get a connection from the pool."""
    return get_pool().get_connection()


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """
    Helper to run a SQL query and return results.

    Args:
        query: SQL query string with %s placeholders
        params: Tuple of parameters for the query
        fetch_one: Return single row as dict
        fetch_all: Return all rows as list of dicts

    Returns:
        - dict (fetch_one=True)
        - list of dicts (fetch_all=True)
        - lastrowid (INSERT without fetch)
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch_one:
            return cursor.fetchone()
        if fetch_all:
            return cursor.fetchall()
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()