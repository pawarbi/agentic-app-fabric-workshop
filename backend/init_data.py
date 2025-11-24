import os
import sqlalchemy
from sqlalchemy import text
import re

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

        # Split on GO (case-insensitive, line-based)
        # This regex ensures GO is on its own line
        batches = re.split(r'^\s*GO\s*$', sql_script, flags=re.MULTILINE | re.IGNORECASE)
        
        # Filter out empty batches and strip whitespace
        batches = [batch.strip() for batch in batches if batch.strip()]
        
        print(f"[init_data] Executing {len(batches)} SQL batches...")
        
        j=1
        with engine.begin() as conn:
            for i, batch in enumerate(batches, 1):
                try:
                    # Skip empty or comment-only batches
                    if not batch or batch.startswith('--'):
                        continue
                    
                    print(f"[init_data] Executing batch {j}...")
                    conn.exec_driver_sql(batch)
                    print(f"[init_data] Batch {j} executed successfully.")
                    j += 1
                    
                except Exception as e:
                    print(f"[init_data] ERROR in batch {i}: {str(e)}")
                    print(f"[init_data] Batch content preview: {batch[:200]}...")
                    # Continue with remaining batches
                    continue
        
        print("[init_data] ✅ Data ingestion completed successfully.")
        
    except FileNotFoundError as e:
        print(f"[init_data] FATAL ERROR: {e}")
        raise
    except Exception as e:
        print(f"[init_data] ERROR during data ingestion: {e}")
        import traceback
        traceback.print_exc()
        raise


def check_and_ingest_data(engine: sqlalchemy.engine.Engine):
    """
    Check if data exists, only ingest if database is empty.
    """
    print("[init_data] check_and_ingest_data called")
    
    try:
        # Check if data already exists
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM DocsChunks_Embeddings")).scalar()
            
            if result > 0:
                print(f"✅ Data already exists. Skipping ingestion.")
                return
            
            print("No data found. Running data ingestion...")
            
        # Only run if no data exists
        ingest_initial_data(engine)
        
    except Exception as e:
        print(f"[init_data] Warning: Could not check for existing data: {e}")
        print("[init_data] Attempting ingestion anyway...")
        try:
            ingest_initial_data(engine)
        except Exception as e2:
            print(f"[init_data] ❌ Failed to ingest data: {e2}")
            # Don't raise - allow app to start even if ingestion fails