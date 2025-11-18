# import urllib.parse
import uuid
from datetime import datetime
import json
import time
import traceback
from dateutil.relativedelta import relativedelta
# from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_sqlserver import SQLServer_VectorStore
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.store.memory import InMemoryStore
from shared.connection_manager import sqlalchemy_connection_creator, connection_manager
from shared.utils import get_user_id, _serialize_messages
import requests  # For calling analytics service
from langgraph.prebuilt import create_react_agent
from init_data import check_and_ingest_data
from tools.database_query import query_database

# Load Environment variables and initialize app
import os
load_dotenv(override=True)

app = Flask(__name__)
CORS(app)

AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

if not AZURE_OPENAI_KEY or not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_DEPLOYMENT or not AZURE_OPENAI_EMBEDDING_DEPLOYMENT:
    raise ValueError("Missing one or more required Azure OpenAI environment variables")

ai_client = AzureChatOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version="2024-10-21",
    api_key=AZURE_OPENAI_KEY,
    azure_deployment=AZURE_OPENAI_DEPLOYMENT
)
embeddings_client = AzureOpenAIEmbeddings(
    azure_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    openai_api_version="2024-10-21",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY,
)

# Database configuration for Azure SQL (banking data)
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://"
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'creator': sqlalchemy_connection_creator,
    'poolclass': QueuePool,
    'pool_size': 5,
    'max_overflow': 10,
    'pool_pre_ping': True,
    'pool_recycle': 3600,
    'pool_reset_on_return': 'rollback'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Import chat / analytics models after DB is initialized
from chat_data_model import init_chat_db
init_chat_db(db)
from chat_data_model import ChatHistoryManager

# -----------------------
# Helper functions
# -----------------------
def get_db_connection():
    """Get a raw DB connection from the connection manager."""
    return connection_manager.create_connection()

# Initialize vector store for knowledge base (support docs)
# Reconstruct the connection string using the connection manager’s config
def _build_connection_string_from_env() -> str:
    """
    Build a SQLAlchemy-style connection string from the same environment
    variables that connection_manager uses.
    """
    driver = os.getenv("FABRIC_ODBC_DRIVER") or os.getenv("ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
    server = os.getenv("FABRIC_SQL_SERVER") or os.getenv("SQL_SERVER")
    database = os.getenv("FABRIC_SQL_DATABASE") or os.getenv("SQL_DATABASE")
    user = os.getenv("FABRIC_SQL_USER") or os.getenv("SQL_USER")
    password = os.getenv("FABRIC_SQL_PASSWORD") or os.getenv("SQL_PASSWORD")

    if not all([server, database, user, password]):
        raise ValueError("Missing one or more SQL connection environment variables")

    # Typical pyodbc connection string – adjust if your connection_manager expects different details
    return (
        f"mssql+pyodbc:///?odbc_connect="
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )

connection_url = _build_connection_string_from_env()

vector_store = SQLServer_VectorStore(
    connection_string=connection_url,
    distance_strategy=DistanceStrategy.COSINE,
    embedding_function=embeddings_client,
    embedding_length=1536,
    table_name="DocsChunks_Embeddings",
)

# Run data ingestion check (ensures DB has demo data)
check_and_ingest_data(connection_url, embeddings_client)

def get_user_accounts(user_id: str) -> dict:
    """Get all accounts for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            account_id,
            user_id,
            account_name,
            account_type,
            balance,
            created_at
        FROM dbo.accounts
        WHERE user_id = ?
        ORDER BY account_name
    """, (user_id,))

    accounts = []
    for row in cursor.fetchall():
        accounts.append({
            "account_id": row.account_id,
            "user_id": row.user_id,
            "account_name": row.account_name,
            "account_type": row.account_type,
            "balance": float(row.balance),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })

    cursor.close()
    conn.close()

    return {
        "status": "success",
        "accounts": accounts,
        "message": f"Retrieved {len(accounts)} accounts for user {user_id}"
    }

def get_transactions_summary(user_id: str, time_period: str = None, account_name: str = None) -> dict:
    """Get spending summary for a user with optional filters."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Default: last 30 days
    end_date = datetime.utcnow()
    if time_period and time_period.lower() == "last_month":
        start_date = end_date - relativedelta(months=1)
    else:
        start_date = end_date - relativedelta(days=30)

    # Build query with optional account_name filter
    query = """
        SELECT 
            t.transaction_type,
            COUNT(*) AS transaction_count,
            SUM(t.amount) AS total_amount
        FROM dbo.transactions t
        JOIN dbo.accounts a ON t.from_account_id = a.account_id
        WHERE a.user_id = ?
          AND t.created_at BETWEEN ? AND ?
    """
    params = [user_id, start_date, end_date]

    if account_name:
        query += " AND a.account_name = ?"
        params.append(account_name)

    query += " GROUP BY t.transaction_type"

    cursor.execute(query, params)

    summary = []
    for row in cursor.fetchall():
        summary.append({
            "transaction_type": row.transaction_type,
            "transaction_count": int(row.transaction_count),
            "total_amount": float(row.total_amount),
        })

    cursor.close()
    conn.close()

    return {
        "status": "success",
        "time_period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "account_name": account_name,
        "summary": summary,
        "message": f"Retrieved summary for user {user_id}"
    }

def search_support_documents(user_question: str) -> dict:
    """Search the knowledge base for support answers using vector search."""
    try:
        docs = vector_store.similarity_search_with_score(user_question, k=3)
        
        results = []
        for doc, score in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            })
        
        return {
            "status": "success",
            "results": results,
            "message": f"Found {len(results)} relevant documents"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Support document search failed: {str(e)}"
        }

def create_new_account(user_id: str, account_type: str, name: str, balance: float = 0.0) -> dict:
    """Create a new account for the user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    account_id = str(uuid.uuid4())
    created_at = datetime.utcnow()

    cursor.execute("""
        INSERT INTO dbo.accounts (account_id, user_id, account_name, account_type, balance, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (account_id, user_id, name, account_type, balance, created_at))

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "status": "success",
        "account": {
            "account_id": account_id,
            "user_id": user_id,
            "account_name": name,
            "account_type": account_type,
            "balance": balance,
            "created_at": created_at.isoformat(),
        },
        "message": f"Account '{name}' created successfully for user {user_id}"
    }

def transfer_money(user_id: str, from_account_name: str = None, to_account_name: str = None,
                   amount: float = 0.0, to_external_details: dict = None) -> dict:
    """Transfer money between user's accounts or to an external account."""
    if amount <= 0:
        return {
            "status": "error",
            "message": "Transfer amount must be positive"
        }
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get from account
        cursor.execute("""
            SELECT account_id, balance
            FROM dbo.accounts
            WHERE user_id = ? AND account_name = ?
        """, (user_id, from_account_name))
        from_row = cursor.fetchone()

        if not from_row:
            return {
                "status": "error",
                "message": f"Source account '{from_account_name}' not found for user {user_id}"
            }

        from_account_id = from_row.account_id
        from_balance = float(from_row.balance)

        if from_balance < amount:
            return {
                "status": "error",
                "message": f"Insufficient funds in account '{from_account_name}'"
            }

        # Internal transfer to another account of same user
        to_account_id = None
        if to_account_name:
            cursor.execute("""
                SELECT account_id
                FROM dbo.accounts
                WHERE user_id = ? AND account_name = ?
            """, (user_id, to_account_name))
            to_row = cursor.fetchone()
            if not to_row:
                return {
                    "status": "error",
                    "message": f"Destination account '{to_account_name}' not found for user {user_id}"
                }
            to_account_id = to_row.account_id

        # Perform transfer within a transaction
        cursor.execute("BEGIN TRANSACTION")

        # Debit from account
        cursor.execute("""
            UPDATE dbo.accounts
            SET balance = balance - ?
            WHERE account_id = ?
        """, (amount, from_account_id))

        # Credit to account if internal transfer
        if to_account_id:
            cursor.execute("""
                UPDATE dbo.accounts
                SET balance = balance + ?
                WHERE account_id = ?
            """, (amount, to_account_id))

        # Insert transaction record
        transaction_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        transaction_type = "internal_transfer" if to_account_id else "external_transfer"

        cursor.execute("""
            INSERT INTO dbo.transactions (
                transaction_id,
                user_id,
                from_account_id,
                to_account_id,
                amount,
                transaction_type,
                description,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction_id,
            user_id,
            from_account_id,
            to_account_id,
            amount,
            transaction_type,
            json.dumps(to_external_details) if to_external_details else None,
            created_at
        ))

        conn.commit()

        return {
            "status": "success",
            "transaction": {
                "transaction_id": transaction_id,
                "user_id": user_id,
                "from_account_name": from_account_name,
                "to_account_name": to_account_name,
                "amount": amount,
                "transaction_type": transaction_type,
                "created_at": created_at.isoformat(),
            },
            "message": "Transfer completed successfully"
        }
    except Exception as e:
        conn.rollback()
        return {
            "status": "error",
            "message": f"Transfer failed: {str(e)}"
        }
    finally:
        cursor.close()
        conn.close()

# -----------------------
# Multi-tenant wrappers
# -----------------------
def get_user_accounts_for_current_user() -> dict:
    """Wrapper to get accounts for the current authenticated user."""
    user_id = get_user_id()
    return get_user_accounts(user_id=user_id)

def get_transactions_summary_for_current_user(time_period: str = None, account_name: str = None) -> dict:
    """Wrapper to get transaction summary for the current authenticated user."""
    user_id = get_user_id()
    return get_transactions_summary(
        user_id=user_id,
        time_period=time_period,
        account_name=account_name,
    )

def create_new_account_for_current_user(account_type: str, name: str, balance: float = 0.0) -> dict:
    """Wrapper to create account for the current authenticated user."""
    user_id = get_user_id()
    return create_new_account(
        user_id=user_id,
        account_type=account_type,
        name=name,
        balance=balance,
    )

def transfer_money_for_current_user(from_account_name: str = None, to_account_name: str = None, 
                                    amount: float = 0.0, to_external_details: dict = None) -> dict:
    """Wrapper to transfer money for the current authenticated user."""
    user_id = get_user_id()
    return transfer_money(
        user_id=user_id,
        from_account_name=from_account_name,
        to_account_name=to_account_name,
        amount=amount,
        to_external_details=to_external_details,
    )

# -----------------------
# Canonical tool wrappers (Option A)
# -----------------------
# These are the functions that are exposed as tools to the agent.
# Their names MUST match initialize_tool_definitions() entries.

def get_user_accounts_tool() -> dict:
    """Canonical tool: retrieves all accounts for the current user."""
    return get_user_accounts_for_current_user()

def get_transactions_summary_tool(time_period: str = None, account_name: str = None) -> dict:
    """Canonical tool: provides spending summary with time period and account filters for the current user."""
    return get_transactions_summary_for_current_user(
        time_period=time_period,
        account_name=account_name,
    )

def create_new_account_tool(account_type: str, name: str, balance: float = 0.0) -> dict:
    """Canonical tool: creates a new bank account for the current user."""
    return create_new_account_for_current_user(
        account_type=account_type,
        name=name,
        balance=balance,
    )

def transfer_money_tool(from_account_name: str = None, to_account_name: str = None,
                        amount: float = 0.0, to_external_details: dict = None) -> dict:
    """Canonical tool: transfers money between accounts or to external accounts for the current user."""
    return transfer_money_for_current_user(
        from_account_name=from_account_name,
        to_account_name=to_account_name,
        amount=amount,
        to_external_details=to_external_details,
    )

# Force canonical tool names to match ToolDefinition names
get_user_accounts_tool.__name__ = "get_user_accounts"
get_transactions_summary_tool.__name__ = "get_transactions_summary"
create_new_account_tool.__name__ = "create_new_account"
transfer_money_tool.__name__ = "transfer_money"

# -----------------------
# Banking Agent Endpoint
# -----------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    """Main chat endpoint for the banking agent."""
    try:
        data = request.json
        messages = data.get("messages", [])
        session_id = data.get("session_id")
        if not session_id:
            return jsonify({"error": "session_id is required"}), 400

        # Determine current user (multi-tenant)
        user_id = get_user_id()

        # Initialize session memory / store
        store = InMemoryStore()
        session_memory = {"configurable": {"thread_id": session_id}}

        # Build LangGraph messages from frontend messages
        lg_messages = []
        for msg in messages:
            if msg["role"] == "user":
                lg_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lg_messages.append(AIMessage(content=msg["content"]))

        # Tools list with canonical names (Option A)
        tools = [
            get_user_accounts_tool,           # name: "get_user_accounts"
            get_transactions_summary_tool,    # name: "get_transactions_summary"
            search_support_documents,         # name: "search_support_documents"
            create_new_account_tool,          # name: "create_new_account"
            transfer_money_tool,              # name: "transfer_money"
            query_database,                   # name: "query_database"
        ]

        # Initialize banking agent with enhanced prompt
        banking_agent = create_react_agent(
            model=ai_client,
            tools=tools,
            checkpointer=store,
            prompt=f"""
            You are a customer support agent for a banking application.
            
            **IMPORTANT: You are currently helping user_id: {user_id}**
            All operations must be performed for this user only.
            
            You have access to the following capabilities:
            1. Standard banking operations (get_user_accounts, get_transactions_summary, transfer_money, create_new_account)
            2. Knowledge base search (search_support_documents)
            3. Direct database queries (query_database)
            
            ## How to Answer Questions ##
            - For simple requests like "what are my accounts?" or "what's my spending summary?", use the standard banking tools.
            - For policy or FAQ-type questions, use search_support_documents.
            - For complex analytics or troubleshooting that requires database structure or data inspection, use query_database.
            
            ## Tool Usage Guidelines ##
            - Always explain to the user which tools you are using and why, in natural language.
            - When using query_database:
              - Prefer 'describe' for understanding table schemas before writing queries.
              - Use 'read' only for SELECT queries and avoid heavy queries (limit rows).
              - Explain the query logic in simple terms to the user.
            """
        )

        # Run the agent
        trace_start = time.time()
        result = banking_agent.invoke(
            {"messages": lg_messages},
            config=session_memory,
        )
        trace_duration = int((time.time() - trace_start) * 1000)

        # Serialize messages for analytics
        serialized_messages = _serialize_messages(result["messages"])

        # Persist chat history & tool usage
        history_manager = ChatHistoryManager(session_id=session_id, user_id=user_id)
        history_manager.add_trace_messages(serialized_messages, trace_duration)

        # Extract the final assistant message
        final_ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
        if not final_ai_messages:
            return jsonify({"error": "No AI response generated"}), 500

        final_message = final_ai_messages[-1].content

        return jsonify({
            "reply": final_message,
            "session_id": session_id
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Serve frontend
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path and os.path.exists(os.path.join("../build", path)):
        return send_from_directory("../build", path)
    else:
        return send_from_directory("../build", "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)