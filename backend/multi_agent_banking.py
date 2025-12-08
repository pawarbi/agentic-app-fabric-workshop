from typing import Annotated, TypedDict, List
from langchain_core.messages import  BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
# from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool

# Import existing banking infrastructure
from banking_app import (
ai_client, get_user_accounts, create_new_account,
transfer_money, get_transactions_summary, search_support_documents)

from tools.database_query import query_database
# Multi-Agent State
class BankingAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The messages in the conversation"]
    current_agent: str
    task_type: str
    user_id: str
    session_id: str
    final_result: str

# Create LLM
def create_banking_llm():
    return ai_client
# Specialized Banking Agents
def create_support_agent():
    """Agent specialized in customer support operations."""
    llm = create_banking_llm()
    
    tools = [search_support_documents]
    
    system_prompt = """You are a customer support agent that provides immediate, complete answers.

                    ## CRITICAL RULES ##
                    1. **ANSWER IMMEDIATELY**: Use the knowledge base tool and provide the complete answer in ONE response.
                    2. **NO STATUS UPDATES**: Don't say "I'm searching..." or "Let me look that up..."
                    3. **DIRECT RESPONSES**: Call the tool, get results, and answer the question fully.

                    ## Your Capabilities ##
                    - Search knowledge base using `search_support_documents` tool
                    - Answer questions about policies, procedures, and general banking topics
                    - Provide troubleshooting guidance

                    ## Response Format ##
                    - Be helpful and professional
                    - Give complete, accurate information
                    - If multiple steps are needed, provide all steps at once
                    - Include relevant details from the knowledge base

                    REMEMBER: Answer the user's question COMPLETELY in your FIRST response."""

    return create_react_agent(
        llm, 
        tools, 
        prompt=system_prompt,
        checkpointer=MemorySaver()
    )
def create_account_management_agent(user_id: str):
    """Agent specialized in account management operations."""
    llm = create_banking_llm()
    
    @tool
    def get_user_accounts_tool() -> str:
        """Retrieves all accounts for the current user."""
        return get_user_accounts(user_id=user_id)
    
    @tool
    def create_new_account_tool(account_type: str = 'checking', name: str = None, balance: float = 0.0) -> str:
        """Creates a new bank account for the current user."""
        return create_new_account(user_id=user_id, account_type=account_type, name=name, balance=balance)
    
    @tool
    def transfer_money_tool(from_account_name: str = None, to_account_name: str = None, amount: float = 0.0, to_external_details: dict = None) -> str:
        """Transfers money between the current user's accounts or to an external account."""
        return transfer_money(user_id=user_id, from_account_name=from_account_name, to_account_name=to_account_name, amount=amount, to_external_details=to_external_details)
    
    @tool
    def get_transactions_summary_tool(time_period: str = 'this year', account_name: str = None) -> str:
        """Provides a categorical summary of the current user's spending for general periods."""
        return get_transactions_summary(user_id=user_id, time_period=time_period, account_name=account_name)
    
    tools = [get_user_accounts_tool, create_new_account_tool,
             transfer_money_tool, get_transactions_summary_tool,
             query_database]
    
    system_prompt=f"""
            You are a customer support agent for a banking application.
            
            **IMPORTANT: You are currently helping user_id: {user_id}**
            All operations must be performed for this user only.
            
            You have access to the following capabilities:
            1. Standard banking operations (get_user_accounts_tool, get_transactions_summary_tool, transfer_money_tool, create_new_account_tool)
            2. Direct database queries (query_database)
            
            ## How to Answer Questions ##
            - For simple requests like "what are my accounts?" or "what's my spending summary?", use the standard banking tools.
            - **'get_transactions_summary_tool' Tool**: Use this ONLY for general categorical summaries (e.g., "What's my spending summary this month?"). It CANNOT handle specific dates or lists.
            - **'query_database' Tool**: Use this for ALL other data questions. This is your default tool for anything specific.
                - "Show me my last 5 transactions" -> `query_database`
                - "How many savings accounts do I have?" -> `query_database`
                - "What has been my expense in 2025?" -> `query_database`
                - "How much did I spend at Starbucks?" -> `query_database`
            - When using 'query_database', you must first use the 'describe' action to see the table structure.
                - If no accounts specified, assume all accounts for the user.
                - if no categories specified, include all categories. If categories specified, filter by those categories.
                - if no time period specified, retrieve last 12 months of data for the user.
            
            ## Database Rules ##
            - You must only access data for the user_id '{user_id}'.
            - **CRITICAL SQL FIX:** The 'datetimeoffset' column type (like 'created_at') will fail. You **MUST** 'CAST' it to a string in all SELECT or ORDER BY clauses (e.g., 'CAST(created_at AS VARCHAR(30)) AS created_at_str').
            
            ## Response Formatting ##
            - **Be concise.** Do not explain your internal process (e.g., "I described the tables...").
            - **Present results directly.**
            - When a user asks for a list of transactions, format the final answer (after all tool calls are done) as a clean bulleted list.
            - **Example of a good response:**
            "Here are your last 5 transactions:
            - [Date] - $[Amount] - [Description] - [Category] - [Status]
            - [Date] - $[Amount] - [Description] - [Category] - [Status]"
            """
    return create_react_agent(
        llm, 
        tools, 
        prompt=system_prompt,
        checkpointer=MemorySaver()
    )

def create_coordinator_agent():
    """Agent that routes customer requests to appropriate specialists."""
    llm = create_banking_llm()
    
    routing_prompt = """You are a routing coordinator. Analyze the request and respond with ONLY the agent name.

    ## Routing Rules ##
    - Account/money/transaction/balance/spending/transfer queries → respond: "account_agent"
    - Help/policy/general questions/support → respond: "support_agent"

    ## Output Format ##
    Respond with ONLY: "account_agent" or "support_agent"
    Do NOT add any other text, explanation, or formatting."""
    
    return create_react_agent(
        llm, 
        [], 
        prompt=routing_prompt,
        checkpointer=MemorySaver()
    )

# Multi-Agent Node Functions

def coordinator_node(state: BankingAgentState):
    """Route customer requests to appropriate specialist agent."""
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    
    # Use keyword-based routing for speed and reliability
    message_lower = last_message.lower()
    
    # Account-related keywords
    account_keywords = [
        "account", "balance", "transaction", "transfer", "payment", 
        "spending", "summary", "history", "money", "deposit", "withdraw",
        "credit", "debit", "checking", "savings", "expense", "income", "breakdown",
        "income", "statement", "funds", "pay", "send", "receive"
    ]
    
    if any(keyword in message_lower for keyword in account_keywords):
        state["current_agent"] = "account_agent"
        state["task_type"] = "account_management"
        print(f"[COORDINATOR] Routing to: account_agent")
    else:
        state["current_agent"] = "support_agent"
        state["task_type"] = "customer_support"
        print(f"[COORDINATOR] Routing to: support_agent")
    
    return state

def account_agent_node(state: BankingAgentState):
    """Handle account management tasks."""
    user_id = state["user_id"]  # Get user_id from state
    account_agent = create_account_management_agent(user_id)  # Pass user_id
    
    thread_config = {"configurable": {"thread_id": f"account_{state['session_id']}"}}
    
    response = account_agent.invoke({"messages": state["messages"]}, config=thread_config)
    
    state["messages"] = response["messages"]
    state["final_result"] = response["messages"][-1].content
    
    return state

def support_agent_node(state: BankingAgentState):
    """Handle customer support tasks."""
    support_agent = create_support_agent()
    
    thread_config = {"configurable": {"thread_id": f"support_{state['session_id']}"}}
    
    response = support_agent.invoke({"messages": state["messages"]}, config=thread_config)
    
    state["messages"] = response["messages"]
    state["final_result"] = response["messages"][-1].content
    
    return state

# Create Multi-Agent Banking System

def create_multi_agent_banking_system():
    """Create the multi-agent banking workflow."""

    workflow = StateGraph(BankingAgentState)
    
    # Add nodes
    workflow.add_node("coordinator", coordinator_node)
    workflow.add_node("account_agent", account_agent_node)
    workflow.add_node("support_agent", support_agent_node)

    # Set entry point
    workflow.set_entry_point("coordinator")
    
    # Add conditional routing
    def route_to_specialist(state: BankingAgentState):
        return state["current_agent"]
    
    workflow.add_conditional_edges(
        "coordinator",
        route_to_specialist,
        {
            "account_agent": "account_agent",
            "support_agent": "support_agent"
        }
    )
    
    # All agents end the workflow
    workflow.add_edge("account_agent", END)
    workflow.add_edge("support_agent", END)
    
    return workflow.compile(checkpointer=MemorySaver())
