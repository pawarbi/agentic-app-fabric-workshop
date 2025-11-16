import os
import pyodbc
from dotenv import load_dotenv

load_dotenv(override=True)

def fabricsql_connection_agentic_db():
    """Create connection for Fabric database using Managed Identity (ActiveDirectoryMSI)."""
    conn_str = os.getenv("FABRIC_SQL_CONNECTION_URL_AGENTIC")
    if not conn_str:
        raise RuntimeError("FABRIC_SQL_CONNECTION_URL_AGENTIC is not set")
    # The ODBC driver will use the Web App's managed identity because
    # the connection string includes Authentication=ActiveDirectoryMSI.
    return pyodbc.connect(conn_str, timeout=30)

def fabricsql_connection_bank_db():
    """DEPRECATED: This function is now an alias for fabricsql_connection_agentic_db."""
    return fabricsql_connection_agentic_db()

def create_azuresql_connection():
    """Create connection for banking database (not used in this demo)."""
    raise NotImplementedError("create_azuresql_connection is not implemented.")

