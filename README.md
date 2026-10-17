# Nexa: A Secure Multi-Merchant WhatsApp AI Assistant

**Nexa — Multi-Merchant AI Assistant** is a production-oriented AI platform that enables customers to interact with multiple independent merchants through a unified WhatsApp interface:

1. **FreshMart Grocery** (Organic produce, dairy, bakery, and pantry staples)
2. **Royal Sweets & Delights** (Artisanal mithai, festive gift hampers, sugar-free sweets)
3. **Glow Salon** (Hair treatments, facial therapies, manicures, and spa bookings)
4. **SmileCare Dental Clinic** (Examinations, cleanings, cosmetic whitening, and clinical triage)

Nexa automatically identifies the intended merchant, loads isolated tenant data, executes authorized business operations via the official **Model Context Protocol (MCP)**, enforces multi-layered AI guardrails, prevents clinical malpractice, and escalates complex queries to human staff.

---

## Architecture Overview

```
                                      ┌──────────────────────────────────────────────────────────┐
                                      │              Customer on WhatsApp                        │
                                      └─────────────────────────────┬────────────────────────────┘
                                                                    │ Webhook HTTP POST
                                                                    ▼
                                      ┌──────────────────────────────────────────────────────────┐
                                      │             FastAPI Webhook Receiver                     │
                                      │  - HMAC SHA256 Signature Verification                    │
                                      │  - Message Deduplication Cache                           │
                                      │  - Phone Normalization & Rate Limiting                   │
                                      └─────────────────────────────┬────────────────────────────┘
                                                                    │
                                                                    ▼
                                      ┌──────────────────────────────────────────────────────────┐
                                      │            Multi-Layered AI Guardrails Engine            │
                                      │  - Prompt Injection & Jailbreak Detector                 │
                                      │  - Query Classification (Allowed / Harmful / OOS)        │
                                      │  - Dental Safety & Emergency Clinical Triage Guardrail   │
                                      │  - Multi-Tenant & IDOR Authorization Verification        │
                                      └─────────────────────────────┬────────────────────────────┘
                                                                    │
                                                                    ▼
                                      ┌──────────────────────────────────────────────────────────┐
                                      │           LangGraph Orchestration State Machine          │
                                      │  - Context Switching & Clarification Engine              │
                                      │  - Merchant Knowledge Retrieval (PDF/TXT/FAQ)            │
                                      │  - Authorized MCP Business Tools Dispatcher              │
                                      └─────────────────────────────┬────────────────────────────┘
                                                                    │
                                    ┌───────────────────────────────┴────────────────────────────┐
                                    ▼                                                            ▼
    ┌───────────────────────────────────────────────┐            ┌───────────────────────────────────────────────┐
    │          Authorized MCP Tools Engine          │            │            AI Provider Abstraction            │
    │  - Grocery: search, inventory, orders, cancel │            │  - Google Gemini (1.5 Flash/Pro)              │
    │  - Sweets: mithai, gift wrapping, orders      │            │  - OpenAI (GPT-4o / GPT-4o-mini)              │
    │  - Salon: service catalog, slots, bookings    │            │  - Groq (LLaMA 3.3 70B Fast)                  │
    │  - Dental: slots, bookings, human escalation  │            │  - Ollama (Local Self-Hosted)                 │
    │  - Customer: profile, tenant isolation        │            │  - Intelligent Offline Mock Provider          │
    └───────────────────────┬───────────────────────┘            └───────────────────────┬───────────────────────┘
                            │                                                            │
                            └───────────────────────────────┬────────────────────────────┘
                                                            │
                                                            ▼
                                      ┌──────────────────────────────────────────────────────────┐
                                      │              Output Validator & Safety Check             │
                                      │  - Secret / API Key / Connection String Redaction        │
                                      │  - Anti-Hallucination Tool Claim Verification            │
                                      │  - Cross-Tenant Data Leakage Prevention                  │
                                      └─────────────────────────────┬────────────────────────────┘
                                                                    │
                                                                    ▼
                                      ┌──────────────────────────────────────────────────────────┐
                                      │                 PostgreSQL Persistence                   │
                                      │  - Shared: merchants, users, customers, audit_logs       │
                                      │  - Business: grocery, sweets, salon, dental tables       │
                                      └──────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Intelligent Multi-Merchant Context Switching
- Seamlessly resolves merchant intent from referral metadata (`?ref=grocery`), explicit mentions, message content, or active conversation history.
- Changes topics cleanly without carrying private business records or sensitive cart data into a different tenant's space.
- Ambiguous queries trigger a structured clarification prompt asking the customer to select their intended merchant.

### 2. Mandatory AI Guardrails & Safety Controls
- **Prompt Injection Defense**: Detects instruction resets, DAN jailbreaks, control token escapes (`[INST]`, `<<SYS>>`), and system prompt exfiltration attempts.
- **Dental & Medical Safety Policy**: Strictly blocks clinical diagnosis, medication prescriptions, and DIY medical advice. Safely redirects emergencies to urgent care and clinical front desks.
- **Tenant Isolation & IDOR Protection**: Ensures customers can only view, modify, or cancel their own orders and appointments.
- **Output Sanitization**: Redacts sensitive API keys, database connection strings, and rejects unverified tool claims.

### 3. Model Context Protocol (MCP) Business Tools
Built with the official **MCP Python SDK** with strict merchant scoping:
- `search_products`, `check_inventory`, `get_product_price`, `get_active_offers`
- `create_order`, `get_order`, `cancel_order` (transactional inventory deduction & restocking)
- `list_services`, `check_available_slots`, `book_appointment`, `cancel_appointment` (double-booking prevention)
- `get_customer_profile`, `create_support_escalation`

### 4. Merchant Management Dashboard
A modern, responsive React + TypeScript web console featuring:
- **Overview**: KPI metrics, 7-day revenue charts, active conversation monitoring.
- **Knowledge Base**: Upload PDF, TXT, Markdown, CSV, JSON; FAQ manager; publishing toggles.
- **Products & Services**: Unified catalog, prices, and live stock adjustments.
- **Customers**: Search, filter, interaction count, authorized CSV export with audit logging.
- **Orders & Appointments**: Live status tracking, cancellations, and appointment rescheduling.
- **Human Assistant**: Escalation queue, human takeover mode, staff contact configuration.
- **Offers & Campaigns**: Promotional campaign creator, audience segmenting, WhatsApp preview.
- **AI & Integrations**: Multi-provider switcher (Gemini, OpenAI, Groq, Ollama, Mock), connectivity testing, WhatsApp webhook diagnostics.
- **General Settings**: Business hours, timezone, notification channels, staff RBAC, and security audit log viewer.
- **Interactive WhatsApp Simulator**: Real-time simulated WhatsApp device to test conversation flows, guardrail triggers, and bookings live.

---

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, LangGraph, Model Context Protocol (MCP) Python SDK, PostgreSQL / aiosqlite, Redis.
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts.
- **AI Providers**: Google Gemini, OpenAI, Groq, Ollama, and offline mock fallback.
- **Messaging**: Meta WhatsApp Business Platform Cloud API with simulator support.

---

## Quickstart & Local Setup

### 1. Clone & Configure
```bash
git clone https://github.com/Wasim7x/Nexa.git
cd Nexa
cp .env.example .env
```

### 2. Run Database Seed & Start Backend
```bash
# Seed initial demo data for all 4 merchants
python -m backend.scripts.seed_data

# Start backend server
python scripts/run_dev.py
```
- **Backend API**: `http://localhost:8000`
- **Swagger Documentation**: `http://localhost:8000/docs`

### 3. Start Frontend Dashboard (Development Mode)
```bash
cd frontend
npm install
npm run dev
```
- **Dashboard UI**: `http://localhost:5173`

*(Note: The FastAPI backend also automatically serves the compiled production dashboard at `http://localhost:8000`)*

---

## Automated Test Suite

Run the comprehensive Pytest suite covering all 20 business, security, and integration tests:

```bash
python -m pytest backend/tests/ -v
```

### Test Coverage Highlights
- `test_guardrails.py`: Phone normalization, prompt injection detection, sensitive PII protection, dental safety emergency handling, rate limiting.
- `test_mcp_tools.py`: Grocery order placement, transactional inventory deductions, IDOR access denial, salon slot double-booking prevention.
- `test_langgraph_workflow.py`: End-to-end conversation flows, context switching between merchants, human escalation triggers.
- `test_whatsapp.py`: Meta webhook verification (`hub.challenge`), message deduplication, and simulator execution.

---

## Meta WhatsApp Business Cloud API Configuration

1. In the **Meta for Developers Console**, navigate to your WhatsApp Business App.
2. In the **Configuration** tab, set:
   - **Callback URL**: `https://your-domain.com/api/whatsapp/webhook`
   - **Verify Token**: `nexa_whatsapp_verify_token_secure_2026`
3. Subscribe to the `messages` webhook field.
4. Copy your **Phone Number ID**, **WhatsApp Business Account ID**, and **Permanent Access Token** into `.env`.
5. Set `USE_MOCK_WHATSAPP="false"` in `.env` to enable live delivery.

---

## Production Deployment with Docker Compose

```bash
docker compose up -d --build
```
This launches:
- `postgres`: PostgreSQL 16 database.
- `redis`: Redis 7 cache and rate limiter.
- `backend`: FastAPI app running with gunicorn/uvicorn on port 8000.
- `frontend`: Nginx serving the production Vite React dashboard on port 3000.
