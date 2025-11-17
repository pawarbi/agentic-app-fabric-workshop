import os
import sqlalchemy
from sqlalchemy import text

# ... existing imports and code ...

def get_ingest_sql_path() -> str:
    """
    Resolve the path to Data_Ingest/ingest_data.sql in a way that works
    both locally and on Azure Web App.

    Assumes repository layout:
      <repo_root>/
        backend/init_data.py
        Data_Ingest/ingest_data.sql
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # repo root = parent of the directory that contains init_data.py
    repo_root = os.path.abspath(os.path.join(current_dir, ".."))
    candidate = os.path.join(repo_root, "Data_Ingest", "ingest_data.sql")

    print(f"[init_data] Looking for ingest SQL at: {candidate}")
    if not os.path.exists(candidate):
        raise FileNotFoundError(
            f"SQL ingest file not found at {candidate}. "
            "Ensure Data_Ingest/ingest_data.sql is deployed alongside backend/."
        )
    return candidate


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
        # Keep the error loud so you notice in logs, but don't crash the app
        print(f"[init_data] FATAL ERROR: {e}")
        # Decide whether to re-raise or not; if you want the app to still run:
        # return
        raise
    except Exception as e:
        print(f"[init_data] ERROR during data ingestion: {e}")
        raise

# existing check_and_ingest_data() should call ingest_initial_data(engine)