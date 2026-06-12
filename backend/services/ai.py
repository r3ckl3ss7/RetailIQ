import os
import uuid
import asyncio
import contextvars
from sqlalchemy import create_engine, text, event, select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from dotenv import load_dotenv

from models.user import Business
from models.ai import ChatMessage

# LangChain imports
from langchain_community.utilities import SQLDatabase
from langchain_ollama import ChatOllama
from langchain_community.agent_toolkits import create_sql_agent

# Load environment configuration
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

# Convert async dialect (postgresql+asyncpg) to sync dialect (postgresql) for SQLAlchemy/LangChain
sync_db_url = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")

# Context variable to hold the current business ID during the request lifecycle
current_business_id_var = contextvars.ContextVar("current_business_id", default=None)

# Initialize dedicated engine for chatbot with RLS event listeners
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
        # Commit to clear transaction block state in psycopg2
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

# Initialize LLM (using qwen2.5:3b via Ollama)
llm = ChatOllama(model="qwen2.5:3b", temperature=0)

# Build system prefix with strict read-only rules and table descriptions
PREFIX_PROMPT = """You are a PostgreSQL query agent for the RetailIQ database.
Your task is to answer user questions by writing and executing syntactically correct SELECT queries.

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
- 'invoice' table: Invoices (id, business_id, customer_id, payment_id, status [PENDING, DRAFT, PAID, REFUNDED, CANCELLED], source [ONLINE, OCR], subtotal, tax, discount, total, notes, created_at, updated_at).
- 'invoice_items' table: Items mapping invoices to products (id, invoice_id, product_id, quantity).
- 'products' table: Product inventory of a business (id, name, business_id, original_price, selling_price, stock, sku, barcode, category, description, created_at, updated_at).

Always explain your query and the results clearly.
"""

# Lazy loaded components
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
        )
    return _agent_executor

def setup_database_rls(conn):
    """
    Sets up the non-superuser role and enables Row Level Security (RLS) policies
    for all tenant-specific tables. This function is designed to run synchronously
    during table creation (via connection.run_sync).
    """
    # Create the role dynamically if it does not exist
    conn.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'retailiq_chat_user') THEN
                CREATE ROLE retailiq_chat_user WITH LOGIN PASSWORD 'temp_chat_pass';
            END IF;
        END
        $$;
    """))

    # Grant connections and schema usage
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

    # customer_address
    conn.execute(text("DROP POLICY IF EXISTS customer_address_isolation_policy ON customer_address;"))
    conn.execute(text("ALTER TABLE customer_address ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("ALTER TABLE customer_address FORCE ROW LEVEL SECURITY;"))
    conn.execute(text("""
        CREATE POLICY customer_address_isolation_policy ON customer_address
        USING (customer_id IN (SELECT id FROM customer));
    """))

    # invoice_items
    conn.execute(text("DROP POLICY IF EXISTS invoice_items_isolation_policy ON invoice_items;"))
    conn.execute(text("ALTER TABLE invoice_items ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("ALTER TABLE invoice_items FORCE ROW LEVEL SECURITY;"))
    conn.execute(text("""
        CREATE POLICY invoice_items_isolation_policy ON invoice_items
        USING (invoice_id IN (SELECT id FROM invoice));
    """))

    # payment
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
    # 1. Enforce business ownership check
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

    # 2. Persist User query
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

    # 3. Execute database agent in thread-pool to keep event loop unblocked
    token = current_business_id_var.set(business_id)
    try:
        executor = get_agent_executor()
        # Run synchronous invocation inside a thread, contextvars will propagate
        response_dict = await asyncio.to_thread(executor.invoke, {"input": message})
        ai_response = response_dict.get("output", "No response received.")
    except Exception as e:
        ai_response = f"Error executing query: {str(e)}"
    finally:
        current_business_id_var.reset(token)

    # 4. Persist Assistant response
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
