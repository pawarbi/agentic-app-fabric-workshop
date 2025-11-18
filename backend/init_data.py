import os
import sqlalchemy
from sqlalchemy import text

def get_ingest_sql_path() -> str:
    """
    Resolve the path to Data_Ingest/ingest_data.sql in a way that works
    both locally and on Azure Web App.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(current_dir, ".."))
    
    # Try multiple possible locations
    candidates = [
        os.path.join(repo_root, "Data_Ingest", "ingest_data.sql"),
        os.path.join(repo_root, "data_ingest", "ingest_data.sql"),
        os.path.join(repo_root, "backend", "Data_Ingest", "ingest_data.sql"),
    ]
    
    for candidate in candidates:
        if os.path.exists(candidate):
            print(f"[init_data] Found ingest SQL at: {candidate}")
            return candidate
    
    raise FileNotFoundError(
        f"SQL ingest file not found. Tried: {candidates}"
    )


def ingest_initial_data(engine: sqlalchemy.engine.Engine):
    """
    Run the ingest_data.sql script against the target database if needed.
    """
    try:
        ingest_sql_path = get_ingest_sql_path()
        print(f"[init_data] Using ingest script: {ingest_sql_path}")

        with open(ingest_sql_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        with engine.begin() as conn:
            # If the script contains multiple statements, use .exec_driver_sql
            conn.exec_driver_sql(sql_script)
        print("[init_data] Data ingestion completed successfully.")
    except FileNotFoundError as e:
        # Keep the error loud so you notice in logs
        print(f"[init_data] FATAL ERROR: {e}")
        raise
    except Exception as e:
        print(f"[init_data] ERROR during data ingestion: {e}")
        raise


def check_and_ingest_data(engine: sqlalchemy.engine.Engine):
    """
    Backwards-compatible entry point used by banking_app.py.

    You can extend this to:
      - Check if data already exists
      - Only run ingest_initial_data(engine) when needed
    For now, always run ingest_initial_data to ensure the demo data is present.
    """
    print("[init_data] check_and_ingest_data called")
    ingest_initial_data(engine)