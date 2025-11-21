import os
import pyodbc
from dotenv import load_dotenv

load_dotenv(override=True)

def fabricsql_connection_agentic_db():
    """
    Create connection for database.
    Supports both:
    - Azure Managed Identity (ActiveDirectoryMSI) for production
    - Standard SQL authentication for local development
    """
    conn_str = os.getenv("FABRIC_SQL_CONNECTION_URL_AGENTIC")
    if not conn_str:
        raise RuntimeError("FABRIC_SQL_CONNECTION_URL_AGENTIC is not set")
    
    try:
        # Try to connect with the connection string as-is
        # This works for both Managed Identity (Azure) and SQL Auth (local)
        return pyodbc.connect(conn_str, timeout=30)
    except pyodbc.Error as e:
        # If it fails and contains MSI-related error, provide helpful message
        error_msg = str(e)
        if "ActiveDirectoryMSI" in conn_str and ("token" in error_msg.lower() or "msi" in error_msg.lower()):
            raise RuntimeError(
                "Failed to connect using Managed Identity. "
                "For local development, update your .env file to use SQL Authentication. "
                "Example: FABRIC_SQL_CONNECTION_URL_AGENTIC=Driver={ODBC Driver 18 for SQL Server};"
                "Server=localhost;Database=BankingDB;UID=sa;PWD=YourPassword;"
                "Encrypt=yes;TrustServerCertificate=yes;"
            ) from e
        else:
            raise

def fabricsql_connection_bank_db():
    """DEPRECATED: This function is now an alias for fabricsql_connection_agentic_db."""
    return fabricsql_connection_agentic_db()

def create_azuresql_connection():
    """Create connection for banking database (not used in this demo)."""
    raise NotImplementedError("create_azuresql_connection is not implemented.")

