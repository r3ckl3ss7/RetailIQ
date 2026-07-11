# RetailIQ

An AI-powered sales, billing, and analytics platform designed specifically for local shop owners, small vendors, and micro-retailers. RetailIQ replaces paper logs, unorganized billing, and complex enterprise software with a simple, digital, and conversational-first solution.

## Table of Contents
- [Problem Statement](#problem-statement)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Database Security & Row-Level Isolation](#database-security--row-level-isolation)
- [Environment Configuration](#environment-configuration)
  - [Backend Environment Variables](#backend-environment-variables)
  - [Frontend Environment Variables](#frontend-environment-variables)
- [Installation & Local Setup](#installation--local-setup)
  - [Prerequisites](#prerequisites)
  - [1. Backend Setup](#1-backend-setup)
  - [2. Frontend Setup](#2-frontend-setup)
- [Running the Application](#running-the-application)

---

## Problem Statement

Many small-scale retailers, family-owned stores, and street vendors rely on manual logbooks, spreadsheets, or physical diaries to record daily transactions. This approach makes it exceptionally difficult to track historic sales patterns, manage inventory, identify top-performing products, predict demand spikes, or make data-backed business decisions. Existing enterprise systems are often too complex, require steep learning curves, are expensive to license, or fail to address the specific workflows of small-scale retail operations.

**RetailIQ** bridges this gap by providing an intuitive, multi-tenant billing system, dynamic visual dashboards, and a conversational AI Business Assistant that answers operational questions in plain language (e.g., *"What were my sales yesterday?"* or *"Show me products that are running low on stock"*).

---

## Key Features

- **Multi-Tenant / Multi-Business Support**: Users can manage multiple independent businesses under a single account. Data between businesses is completely isolated at the database level.
- **Billing & Digital Invoices**: Instantly create, update, and manage invoices. Supports multiple payment methods (Cash, UPI, Card, Cheque, and other methods) and invoice status tracking (Paid, Pending, Refunded, Cancelled).
- **Product & Inventory Management**: Manage catalog items with SKU, barcode tracking, cost pricing, selling prices, categories, and real-time stock levels.
- **Dynamic Analytics Dashboard**: Visual indicators and graphs showing sales, profit margins, revenue patterns, top-selling products, and seasonal analytics.
- **Conversational AI Agent**: Powered by **LangChain** and modern LLMs (supporting Llama via Groq or Ollama). The assistant converts plain English queries into safe SQL queries, executes them against the business's database context, and summarizes the results conversationally.
- **Security Guardrails**:
  - Built-in static and dynamic query classifiers to intercept prompt injections, jailbreaks, or attempts to read sensitive tables (such as users or chat history).
  - Enforced read-only operations (strictly SELECT queries) for the database agent.
  - PostgreSQL Row-Level Security (RLS) ensuring that the AI agent can only access data belonging to the logged-in user's business.
- **Secure File Storage**: Easy logo upload and avatar support to personalize store configurations and printable invoices.

---

## System Architecture

The project is structured into three primary sub-systems:

1. **Frontend Client**:
   - Built with **React** (via **Vite**) for rapid development and optimization.
   - Global state management using **Redux Toolkit** and asynchronous thunks for API data sync.
   - Stylized using **Tailwind CSS** for a responsive, modern interface.
   
2. **Backend Service**:
   - Built with **FastAPI** (Python 3) for clean, high-performance, asynchronous endpoints.
   - Database operations managed via **SQLAlchemy ORM** (utilizing both async connections for general API endpoints and sync connections for the LLM SQL database utility).
   - Database migrations managed via **Alembic**.
   
3. **Database & Services Layer**:
   - **PostgreSQL**: Stores relational models for users, businesses, customers, products, payments, invoices, invoice items, and chat messages.
   - **Redis**: Used for session caching and background operation support.
   - **LangChain / Groq**: Orchestrates the SQL Agent and LLM-based query classification.

---

## Database Security & Row-Level Isolation

RetailIQ uses **PostgreSQL Row-Level Security (RLS)** to enforce multi-tenant isolation.
When the AI chatbot processes a user prompt:
1. The backend assigns a context variable (`ContextVar`) specifying the `business_id` belonging to the authenticated user.
2. In the connection checkout event, the application switches the active database connection role to `retailiq_chat_user` and initializes the session setting `app.current_business_id` with the active business ID.
3. PostgreSQL applies the corresponding RLS policy for tables like `products`, `customer`, and `invoice`, filtering database rows before returning any results to the query agent.
4. This ensures that even if an AI model generates an unconstrained query, it is mathematically impossible for it to retrieve data belonging to another tenant.

---

## Environment Configuration

### Backend Environment Variables
Create a `.env` file in the `backend/` directory using the following keys:

```ini
# Database Connection (AsyncPG dialect for async database transactions)
DATABASE_URL=postgresql+asyncpg://<username>:<password>@<host>:<port>/<db_name>

# Server Configuration
HOST=0.0.0.0
PORT=8000

# LLM APIs
GROQ_API_KEY=your_groq_api_key_here

# Mailer Settings (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your_smtp_email@gmail.com
SMTP_PASSWORD=your_app_specific_smtp_password

# Redis Configuration
REDIS_HOST=your_redis_host
REDIS_PORT=your_redis_port
REDIS_DECODE_RESPONSES=True
REDIS_USERNAME=default
REDIS_PASSWORD=your_redis_password
```

### Frontend Environment Variables
Create a `.env` file in the `frontend/retailIQ/` directory:

```ini
VITE_API_URL=http://localhost:8000
```

---

## Installation & Local Setup

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher (with npm)
- PostgreSQL 14 or higher (or a cloud provider like Supabase)
- Redis server
- Groq API Key or local Ollama installation

### 1. Backend Setup
1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment named `renv`:
   ```bash
   python -m venv renv
   ```
3. Activate the virtual environment:
   - **Windows (Command Prompt)**: `renv\Scripts\activate`
   - **Windows (PowerShell)**: `.\renv\Scripts\Activate.ps1`
   - **macOS/Linux**: `source renv/bin/activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Initialize and seed the database (creates tables, configures PostgreSQL RLS policies, and populates the schema with mock businesses, products, and invoices):
   ```bash
   python init_db.py
   ```

### 2. Frontend Setup
1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend/retailIQ
   ```
2. Install the package dependencies:
   ```bash
   npm install
   ```

---

## Running the Application

To start the application services:

- **Backend (FastAPI)**:
  ```bash
  cd backend
  # Ensure your virtual environment is active
  uvicorn app:app --reload --host 127.0.0.1 --port 8000
  ```
- **Frontend (React/Vite)**:
  ```bash
  cd frontend/retailIQ
  npm run dev
  ```

Once running, navigate to `http://localhost:5173` in your browser.