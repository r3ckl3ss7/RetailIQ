import os
import re
import uuid
import asyncio
import contextvars
from sqlalchemy import create_engine, text, event, select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from dotenv import load_dotenv

from models.user import Business
from models.ai import ChatMessage

from langchain_community.utilities import SQLDatabase
from langchain_ollama import ChatOllama
from langchain_community.agent_toolkits import create_sql_agent

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

sync_db_url = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")

current_business_id_var = contextvars.ContextVar("current_business_id", default=None)

chatbot_engine = create_engine(sync_db_url, pool_pre_ping=True)

@event.listens_for(chatbot_engine, "checkout")
def set_connection_rls_variables(dbapi_connection, connection_record, connection_proxy):
    business_id = current_business_id_var.get()
    if dbapi_connection is None or not hasattr(dbapi_connection, "cursor"):
        return
    cursor = dbapi_connection.cursor()
    try:
        if business_id is not None:
            cursor.execute("SET ROLE retailiq_chat_user;")
            cursor.execute(f"SET app.current_business_id = '{business_id}';")
        else:
            cursor.execute("RESET ROLE;")
            cursor.execute("SET app.current_business_id = '';")
        dbapi_connection.commit()
    except Exception as e:
        try:
            cursor.execute("RESET ROLE;")
            cursor.execute("SET app.current_business_id = '';")
            dbapi_connection.commit()
        except Exception:
            pass
        raise e
    finally:
        cursor.close()

@event.listens_for(chatbot_engine, "checkin")
def reset_connection_rls_variables(dbapi_connection, connection_record):
    if dbapi_connection is None or not hasattr(dbapi_connection, "cursor"):
        return
    try:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("RESET ROLE;")
            cursor.execute("SET app.current_business_id = '';")
            dbapi_connection.commit()
        finally:
            cursor.close()
    except Exception:
        pass

llm = ChatOllama(model="qwen2.5:3b", temperature=0)

PREFIX_PROMPT = """You are a helpful PostgreSQL query agent for the RetailIQ database.
Your task is to answer user questions by writing and executing syntactically correct SELECT queries, then presenting the RESULTS in a clear, human-readable format.

CRITICAL SAFETY RULES:
1. You must ONLY write and execute read-only queries (SELECT statements).
2. You are STRICTLY FORBIDDEN from writing or running any query that modifies, creates, deletes, or drops database records, tables, or schemas (including INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, TRUNCATE, etc.).
3. If the user requests to insert, update, or delete data, or change the schema, you must immediately refuse and state that you are a read-only assistant.
4. Unless specified by the user, always limit your queries to a maximum of 10 rows.
5. Only query the columns necessary to answer the question. Do not run SELECT * queries.
6. Double-check table and column names using the schema tools before running queries.

DATABASE MODEL INFORMATION:
- 'businesses' table: Business profiles (id, user_id, name, gst_number, phone, email, address, city, state, country, postal_code, logo_url, invoice_prefix, currency, timezone, created_at).
- 'customer' table: Customers of a business (id, business_id, name, phone_number_country_code, phone_number, email, created_at).
- 'customer_address' table: Customer addresses (id, customer_id, line1, line2, city, state, country, postal_code, created_at).
- 'payment' table: Payments for invoices (id, method [CASH, UPI, CARD, CHEQUE, OTHER], status, amount, paid_at, created_at).
- 'invoice' table: Invoices (id, business_id, customer_id, payment_id, status [PENDING, DRAFT, PAID, REFUNDED, CANCELLED], source [ONLINE], subtotal, tax, discount, total, notes, created_at, updated_at).
- 'invoice_items' table: Items mapping invoices to products (id, invoice_id, product_id, quantity).
- 'products' table: Product inventory of a business (id, name, business_id, original_price, selling_price, stock, sku, barcode, category, description, created_at, updated_at).

CRITICAL OUTPUT RULES:
- Your FINAL ANSWER must ALWAYS be the actual data/results in plain language, NOT the SQL query itself.
- NEVER include SQL code in your final answer. The user does not want to see SQL.
- Summarize the query results in a natural, conversational manner.
- If the query returns rows, present them clearly (e.g., as a numbered list or short summary).
- If the query returns no rows, say so clearly (e.g., "No results found for your query.").
"""

SUFFIX_PROMPT = """IMPORTANT REMINDER: When providing your Final Answer, you MUST:
1. Present ONLY the actual data results from the query in plain, human-readable language.
2. NEVER include SQL queries, code blocks, or technical syntax in the Final Answer.
3. Summarize the findings conversationally. For example, instead of showing a SQL query, say "You have 5 products in stock. The top ones are: 1. Widget ($10), 2. Gadget ($25)..."
4. If no data was found, clearly state that.

Begin!

Question: {input}
Thought: I should look at the relevant tables to answer this question.
{agent_scratchpad}"""

_db_utility = None
_agent_executor = None

def get_agent_executor():
    """
    Lazy loads and returns the LangChain SQL agent executor.
    This prevents database lookup/reflection at module import time when tables do not exist yet.
    """
    global _db_utility, _agent_executor
    if _agent_executor is None:
        _db_utility = SQLDatabase(
            chatbot_engine,
            ignore_tables=["users", "chat_messages"]
        )
        _agent_executor = create_sql_agent(
            llm=llm,
            db=_db_utility,
            agent_type="zero-shot-react-description",
            verbose=True,
            prefix=PREFIX_PROMPT,
            suffix=SUFFIX_PROMPT,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )
    return _agent_executor

def setup_database_rls(conn):
    """
    Sets up the non-superuser role and enables Row Level Security (RLS) policies
    for all tenant-specific tables. This function is designed to run synchronously
    during table creation (via connection.run_sync).
    """
    conn.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'retailiq_chat_user') THEN
                CREATE ROLE retailiq_chat_user WITH LOGIN PASSWORD 'temp_chat_pass';
            END IF;
        END
        $$;
    """))

    db_name = conn.execute(text("SELECT current_database()")).scalar()
    conn.execute(text(f"GRANT CONNECT ON DATABASE {db_name} TO retailiq_chat_user;"))
    conn.execute(text("GRANT USAGE ON SCHEMA public TO retailiq_chat_user;"))
    conn.execute(text("GRANT SELECT ON ALL TABLES IN SCHEMA public TO retailiq_chat_user;"))
    conn.execute(text("REVOKE SELECT ON users FROM retailiq_chat_user;"))
    conn.execute(text("REVOKE SELECT ON chat_messages FROM retailiq_chat_user;"))

    tables_with_business_id = ["businesses", "products", "customer", "invoice"]
    for table in tables_with_business_id:
        conn.execute(text(f"DROP POLICY IF EXISTS {table}_isolation_policy ON {table};"))
        conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
        conn.execute(text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;"))
        col = "id" if table == "businesses" else "business_id"
        conn.execute(text(f"""
            CREATE POLICY {table}_isolation_policy ON {table}
            USING ({col} = NULLIF(current_setting('app.current_business_id', true), '')::integer);
        """))

    conn.execute(text("DROP POLICY IF EXISTS customer_address_isolation_policy ON customer_address;"))
    conn.execute(text("ALTER TABLE customer_address ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("ALTER TABLE customer_address FORCE ROW LEVEL SECURITY;"))
    conn.execute(text("""
        CREATE POLICY customer_address_isolation_policy ON customer_address
        USING (customer_id IN (SELECT id FROM customer));
    """))

    conn.execute(text("DROP POLICY IF EXISTS invoice_items_isolation_policy ON invoice_items;"))
    conn.execute(text("ALTER TABLE invoice_items ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("ALTER TABLE invoice_items FORCE ROW LEVEL SECURITY;"))
    conn.execute(text("""
        CREATE POLICY invoice_items_isolation_policy ON invoice_items
        USING (invoice_id IN (SELECT id FROM invoice));
    """))

    conn.execute(text("DROP POLICY IF EXISTS payment_isolation_policy ON payment;"))
    conn.execute(text("ALTER TABLE payment ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("ALTER TABLE payment FORCE ROW LEVEL SECURITY;"))
    conn.execute(text("""
        CREATE POLICY payment_isolation_policy ON payment
        USING (id IN (SELECT payment_id FROM invoice WHERE payment_id IS NOT NULL));
    """))

async def get_chat_history(db: AsyncSession, business_id: int, session_id: str) -> list[ChatMessage]:
    """
    Retrieves chronological chat messages for a specific session and business.
    """
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.business_id == business_id, ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return list(result.scalars().all())

async def list_chat_sessions(db: AsyncSession, business_id: int) -> list[dict]:
    """
    Lists distinct chat sessions for a business along with the latest message.
    """
    subq = (
        select(
            ChatMessage.session_id,
            func.max(ChatMessage.id).label("max_id")
        )
        .where(ChatMessage.business_id == business_id)
        .group_by(ChatMessage.session_id)
        .subquery()
    )

    result = await db.execute(
        select(
            ChatMessage.session_id,
            ChatMessage.message.label("last_message"),
            ChatMessage.created_at.label("updated_at")
        )
        .join(subq, ChatMessage.id == subq.c.max_id)
        .order_by(ChatMessage.created_at.desc())
    )

    sessions = []
    for row in result.all():
        sessions.append({
            "session_id": row.session_id,
            "last_message": row.last_message,
            "updated_at": row.updated_at
        })
    return sessions

async def delete_chat_session(db: AsyncSession, business_id: int, session_id: str) -> None:
    """
    Deletes the chat history for a session of a specific business.
    """
    await db.execute(
        delete(ChatMessage)
        .where(ChatMessage.business_id == business_id, ChatMessage.session_id == session_id)
    )
    await db.commit()



async def classify_query(message: str) -> str:
    """
    Classifies the user's query into one of three categories:
    - 'GREETING': simple greetings, intros, capability inquiries.
    - 'SQL': questions about business operations, products, stock, invoices, customers, sales.
    - 'IRRELEVANT': off-topic queries (code generation, essays, general Q&A, math, etc.).
    """
    system_prompt = (
        "You are a routing and validation system for a retail business database chatbot called RetailIQ.\n"
        "Your task is to classify the user's input into one of three categories:\n"
        "1. 'GREETING': If the query is a simple greeting, introduction, or capability inquiry (e.g. 'hi', 'hello', 'who are you', 'what can you do', 'help').\n"
        "2. 'SQL': If the query asks for business data, retail operations, products, stock, inventory, sales, customers, invoices, or payments.\n"
        "3. 'IRRELEVANT': If the query is unrelated, such as code generation, software engineering, translations, writing essays/stories/emails, general knowledge, math, or other off-topic tasks.\n"
        "Respond with exactly one word: 'GREETING', 'SQL', or 'IRRELEVANT'.\n"
        "Do not include any explanation, punctuation, or extra characters."
    )
    prompt = f"System: {system_prompt}\nUser Query: {message}\nResponse:"
    try:
        response = await asyncio.to_thread(llm.invoke, prompt)
        classification = response.content.strip().upper()
        if "GREETING" in classification:
            return "GREETING"
        elif "SQL" in classification:
            return "SQL"
        else:
            return "IRRELEVANT"
    except Exception:
        # Fallback to SQL if LLM fails, so we don't break the chatbot
        return "SQL"

_SQL_PATTERN = re.compile(
    r'\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN|GROUP BY|ORDER BY|LIMIT|CREATE|ALTER|DROP)\b',
    re.IGNORECASE
)

def _looks_like_sql(text: str) -> bool:
    """Check if text appears to contain SQL statements rather than results."""
    if not text:
        return False
    sql_keywords_found = len(_SQL_PATTERN.findall(text))
    # If 3+ SQL keywords are present, it's likely SQL rather than natural language
    return sql_keywords_found >= 3

def _extract_last_observation(intermediate_steps: list) -> str | None:
    """
    Extract the last tool observation (query result) from agent intermediate steps.
    Each step is a tuple of (AgentAction, observation_string).
    """
    if not intermediate_steps:
        return None
    for action, observation in reversed(intermediate_steps):
        if observation and isinstance(observation, str) and observation.strip():
            return observation.strip()
    return None

def _sanitize_agent_output(response_dict: dict) -> str:
    """
    Post-processes the SQL agent's response to ensure the user gets actual
    query results in natural language, not raw SQL.
    
    If the agent's 'output' looks like SQL, extracts the real data from
    intermediate steps and formats a readable response using the LLM.
    """
    output = response_dict.get("output", "").strip()
    intermediate_steps = response_dict.get("intermediate_steps", [])

    if not output:
        output = "No response received."

    # If output doesn't look like SQL, return it as-is (agent did its job)
    if not _looks_like_sql(output):
        return output

    # Output looks like SQL — try to extract actual results from intermediate steps
    observation = _extract_last_observation(intermediate_steps)

    if not observation:
        # No observation found, strip SQL from output and return what we can
        return "I found the relevant data but encountered a formatting issue. Please try rephrasing your question."

    # Use the LLM to convert raw query results into a human-readable response
    try:
        summary_prompt = (
            "You are a helpful assistant. The user asked a question about their business data. "
            "A database query was executed and returned the following raw results:\n\n"
            f"{observation}\n\n"
            "Please summarize these results in a clear, conversational, human-readable format. "
            "Do NOT include any SQL queries or code. Just present the data naturally. "
            "If the results are empty, say 'No results found.'"
        )
        summary_response = llm.invoke(summary_prompt)
        summarized = summary_response.content.strip()
        if summarized and not _looks_like_sql(summarized):
            return summarized
    except Exception:
        pass

    # Final fallback: return the raw observation data directly (still better than SQL)
    if observation and not _looks_like_sql(observation):
        return f"Here are the results from your query:\n\n{observation}"

    return "I found some data for your question, but had trouble formatting the response. Please try rephrasing your question."

async def chat_with_agent(
    db: AsyncSession,
    business_id: int,
    user_id: int,
    message: str,
    session_id: str | None = None
) -> ChatMessage:
    """
    Saves user prompt, executes the LLM database agent using the RLS-isolated engine,
    saves the AI's reply, and returns the assistant's response.
    """
    business_result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = business_result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if business.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Forbidden | Business does not belong to logged in user!",
        )

    if not session_id:
        session_id = str(uuid.uuid4())

    user_msg = ChatMessage(
        business_id=business_id,
        user_id=user_id,
        session_id=session_id,
        sender="user",
        message=message
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # Classify the message for relevance and routing to avoid misuse/abuse (e.g. code generation)
    category = await classify_query(message)
    if category == "GREETING":
        ai_response = (
            "Hello! I am RetailIQ's AI Chatbot. I can help you analyze your business data, "
            "search products, look up customer info, and review invoices. How can I help you today?"
        )
    elif category == "IRRELEVANT":
        ai_response = (
            "I can only help you with questions related to your RetailIQ business data, "
            "products, customers, invoices, and sales. For safety and security, general queries, "
            "code generation, and off-topic requests are not allowed."
        )
    else:
        token = current_business_id_var.set(business_id)
        try:
            executor = get_agent_executor()
            response_dict = await asyncio.to_thread(executor.invoke, {"input": message})
            ai_response = _sanitize_agent_output(response_dict)
        except Exception as e:
            ai_response = f"Error executing query: {str(e)}"
        finally:
            current_business_id_var.reset(token)

    assistant_msg = ChatMessage(
        business_id=business_id,
        user_id=user_id,
        session_id=session_id,
        sender="assistant",
        message=ai_response
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return assistant_msg


