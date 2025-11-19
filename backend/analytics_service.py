import time
from typing import List, Dict, Any

import chat_data_model  # module import
from shared.utils import _serialize_messages
from langchain_core.messages import BaseMessage

# Import the banking_app to get its Flask app object
import banking_app


def get_chat_history_for_session(session_id: str, user_id: str) -> List[Dict[str, Any]]:
    """
    In-process equivalent of GET /analytics/api/chat/history/<session_id>.
    Returns a list of serialized messages for the given session.
    """
    # Ensure we're inside the banking_app's Flask application context
    with banking_app.app.app_context():
        ChatHistoryManager = chat_data_model.ChatHistoryManager
        if ChatHistoryManager is None:
            raise RuntimeError(
                "ChatHistoryManager is not initialized. Did you call init_chat_db(db)?"
            )

        manager = ChatHistoryManager(session_id=session_id, user_id=user_id)
        history = manager.get_conversation_history(limit=50)
        return history or []


def log_chat_trace(
    session_id: str,
    user_id: str,
    messages: List[BaseMessage],
    trace_duration_ms: int,
) -> None:
    """
    In-process equivalent of POST /analytics/api/chat/log-trace.
    """
    start = time.time()

    with banking_app.app.app_context():
        ChatHistoryManager = chat_data_model.ChatHistoryManager
        if ChatHistoryManager is None:
            raise RuntimeError(
                "ChatHistoryManager is not initialized. Did you call init_chat_db(db)?"
            )

        manager = ChatHistoryManager(session_id=session_id, user_id=user_id)

        serialized_messages = _serialize_messages(messages)

        manager.add_trace_messages(
            serialized_messages=serialized_messages,
            trace_duration=trace_duration_ms,
        )

    elapsed = time.time() - start
    print(
        f"[analytics_service] Logged chat trace for session={session_id}, "
        f"user_id={user_id} in {elapsed:.2f}s "
        f"(trace_duration_ms={trace_duration_ms})"
    )