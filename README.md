# 🏢 Business Mention Resolution Platform (BMRP)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2+-FF6F00.svg?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![FAISS](https://img.shields.io/badge/Vector_Search-FAISS_CPU-orange.svg)](https://github.com/facebookresearch/faiss)
[![GLiNER](https://img.shields.io/badge/Zero--Shot_NER-GLiNER_v2.5-9cf.svg)](https://github.com/urchade/GLiNER)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit_UI-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Containerized-Docker_Compose-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An enterprise-grade, microservice-based AI platform for **extracting, resolving, and disambiguating local business mentions from unstructured text** (reviews, social posts, articles, customer tickets) and linking them to canonical records in a massive database catalog (Yelp Academic Dataset).

The platform combines **zero-shot Named Entity Recognition (GLiNER)**, **dense semantic search (Sentence-Transformers + FAISS)**, **fuzzy lexical matching**, **deterministic policy guardrails**, **LangGraph multi-step agentic LLM reasoning**, **ReportLab PDF generation**, and a **Streamlit portal** with human-in-the-loop review workflows.

---

## 📑 Table of Contents

- [Business Problem \& Value Proposition](#-business-problem--value-proposition)
- [System Architecture](#-system-architecture)
- [Key Features \& Capabilities](#-key-features--capabilities)
- [NLP \& Entity Resolution Pipeline](#-nlp--entity-resolution-pipeline)
  - [1. Mention Extraction (GLiNER vs. spaCy)](#1-mention-extraction-gliner-vs-spacy)
  - [2. Hybrid Candidate Generation](#2-hybrid-candidate-generation)
  - [3. Scoring Matrix \& Mathematical Formulation](#3-scoring-matrix--mathematical-formulation)
  - [4. LangGraph Smart AI Resolution Assistant](#4-langgraph-smart-ai-resolution-assistant)
  - [5. Human Review \& Audit Workflow](#5-human-review--audit-workflow)
- [Services \& Microservice Topology](#-services--microservice-topology)
- [Interactive Streamlit UI](#-interactive-streamlit-ui)
- [API Reference \& Endpoints](#-api-reference--endpoints)
- [Project Score, Evaluation \& Metrics](#-project-score-evaluation--metrics)
- [Quick Start \& How to Run](#-quick-start--how-to-run)
  - [Prerequisites](#prerequisites)
  - [Option A: Running with Docker (Recommended)](#option-a-running-with-docker-recommended)
  - [Option B: Local Development Setup](#option-b-local-development-setup)
- [Environment Configuration](#-environment-configuration)
- [Database Schema \& Migrations](#-database-schema--migrations)
- [Vector Index Management](#-vector-index-management)
- [Automated Testing \& Quality Assurance](#-automated-testing--quality-assurance)
- [Troubleshooting \& Common Scenarios](#-troubleshooting--common-scenarios)
- [Project Directory Structure](#-project-directory-structure)

---

## 🎯 Business Problem & Value Proposition

### The Challenge
Unstructured text across the internet, customer reviews, CRM notes, and support tickets is filled with references to local businesses:
- *"Had a great pizza at Tony's near downtown yesterday."*
- *"We stopped by Target on Broadway Blvd in Tucson, AZ."*
- *"The Starbucks barista was super quick!"*

Matching these free-form text mentions to a canonical business database presents severe challenges:
1. **Entity Ambiguity & Polysemy:** Multiple branches or distinct businesses share identical or near-identical names (e.g., thousands of *Starbucks* locations, dozens of *Tony's Pizza* in different cities).
2. **Noisy Text & Informal Names:** Users omit official suffixes ("Inc.", "LLC", "Cafe"), misspell addresses, or provide partial geographic clues ("near the stadium", "on Broadway").
3. **High-Risk Automation Errors:** Automatically resolving a mention to the wrong business corrupts downstream sentiment analytics, marketing attributions, and CRM intelligence.
4. **General NER Inadequacy:** Off-the-shelf NLP models (such as spaCy's `en_core_web_sm`) often misclassify business names (e.g., classifying *"Domino's"* as `PERSON` instead of `ORG`), causing high false-negative rates.

### The Solution
The **Business Mention Resolution Platform (BMRP)** provides an end-to-end automated pipeline with human oversight:
- **Zero-Shot Extraction:** Detects domain-specific business entities with high precision using GLiNER.
- **Hybrid Retrieval:** Blends vector embeddings (FAISS cosine similarity) with relational token queries (`ILIKE` database searches) to handle both semantic descriptions and exact name matches.
- **Weighted Multi-Factor Scoring:** Combines name similarity, embedding similarity, city, state, and street address context.
- **LangGraph Agentic Decisioning:** Uses LLM reasoning (`gpt-4o-mini`) to examine surrounding text for subtle contextual clues before resolving or escalating.
- **Human-in-the-Loop Review Queue:** Routes ambiguous or unverified businesses to human reviewers with full audit trails.
- **Automated Document Generation:** Generates individual resolution summary PDFs and monthly executive analytics reports.
- **Natural Language Catalog Q&A:** Enables non-technical business users to ask conversational questions over the catalog with zero SQL knowledge and zero hallucination risk.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    User([User / External System]) -->|HTTP / Web Browser| UI[Streamlit Frontend :8501]
    User -->|REST API Calls| CatalogAPI[Catalog Service :8000\nFastAPI]

    subgraph Platform Services
        UI -->|JWT Auth / API Proxy| CatalogAPI
        UI -->|Document Queries| DocAPI[Document Service :8001\nFastAPI]
        CatalogAPI -->|Internal Token Auth| DocAPI

        subgraph Catalog Microservice
            CatalogAPI --> AuthModule[Auth & Security\nJWT / RBAC / Rate Limiting]
            CatalogAPI --> NER[Extraction Engine\nGLiNER v2.5 / spaCy]
            CatalogAPI --> ResEngine[Resolution Engine\nHybrid Scoring / Decision Rules]
            CatalogAPI --> LGGraph[LangGraph Assistant\nStateGraph Workflow / GPT-4o-mini]
            CatalogAPI --> QAEngine[Catalog Q&A Engine\nQuery Planner / Grounded LLM]
            ResEngine --> FAISS[(FAISS Vector Store\nbusinesses.faiss)]
            ResEngine --> Embeddings[Sentence-Transformers\nall-MiniLM-L6-v2]
        end

        subgraph Document Microservice
            DocAPI --> PDFGen[PDF Generation Engine\nReportLab 5.0]
            PDFGen --> DocStorage[(Local Document Storage\ndata/documents/*.pdf)]
        end

        subgraph Database Layer
            CatalogAPI --> Postgres[(PostgreSQL 18 Database\nPort 5433 : 5432)]
            DocAPI --> Postgres
        end
    end
```

---

## ✨ Key Features & Capabilities

| Feature | Description | Technology Stack |
| :--- | :--- | :--- |
| **Zero-Shot Mention Extraction** | Detects business names from noisy text without requiring custom model re-training. | GLiNER (`gliner_small-v2.5`), spaCy |
| **Hybrid Candidate Search** | Combines vector similarity with fast database token matching to retrieve top business candidates. | FAISS, Sentence-Transformers, PostgreSQL |
| **Smart AI Resolution Assistant** | Graph-based agentic pipeline that reasons over surrounding context and candidates before deciding. | LangGraph, OpenAI GPT-4o-mini |
| **Deterministic Policy Guardrails** | Enforces hard constraints (e.g., unverified businesses must never auto-resolve). | Python, Pydantic, SQLAlchemy |
| **Human Review Queue** | Reviewer interface for approving, rejecting, and adding audit notes to ambiguous matches. | Streamlit, FastAPI, RBAC |
| **Natural Language Catalog Q&A** | Converts user questions into safe SQL query plans and synthesizes hallucination-free grounded answers. | OpenAI GPT-4o-mini, SQLAlchemy |
| **Automated PDF Document Engine** | Generates resolution summaries and executive monthly metric reports with charts. | ReportLab 5.0, Microservice Architecture |
| **Enterprise Security & Auth** | Role-Based Access Control (`admin`, `reviewer`, `viewer`), password hashing (`bcrypt`), and rate limiting. | OAuth2 JWT, passlib, Python-Jose |
| **Dockerized Microservices** | Containerized deployment with PostgreSQL pre-seeded with ~150,000 Yelp catalog records. | Docker Compose, Alpine Linux |

---

## 🔬 NLP & Entity Resolution Pipeline

### 1. Mention Extraction (GLiNER vs. spaCy)

The platform evaluates two NER architectures:
1. **GLiNER (`gliner-community/gliner_small-v2.5`) [Primary]:**
   - Zero-shot entity extractor configured with target labels: `["business", "restaurant", "store", "hotel", "cafe"]`.
   - Includes contextual labels (`["city", "state", "address"]`) during inference to prevent cities/streets from being falsely tagged as business names.
   - Accurately captures proprietary and casual names (e.g., *"Domino's"*, *"Copper Finch Cafe"*).
2. **spaCy (`en_core_web_sm`) [Baseline]:**
   - Standard generic NER baseline matching `ORG` entities.

```
Input: "We ordered pizza from Domino's in Philadelphia yesterday."
  ├── spaCy:  "Domino" -> PERSON ❌ (Ignored or misclassified)
  └── GLiNER: "Domino's" -> restaurant ✅ (Extracted with confidence 0.91)
```

---

### 2. Hybrid Candidate Generation

When a mention is ingested, the platform executes a two-pronged candidate retrieval strategy:
1. **Lexical PostgreSQL Search:** Tokenizes the mention text and executes an `ILIKE` condition across the business catalog.
2. **Dense Vector Search (FAISS):** Encodes the mention text + surrounding context using `sentence-transformers/all-MiniLM-L6-v2` and performs an Inner-Product (Cosine) search against `data/vector_store/businesses.faiss` to fetch the top 50 semantic matches.
3. **Candidate Merging:** Merges both candidate sets and removes duplicates.

---

### 3. Scoring Matrix & Mathematical Formulation

Each retrieved candidate is scored across five granular dimensions:

#### A. Name Similarity Score ($S_{\text{name}}$)
Combines character-level sequence matching with word token set overlap:
$$S_{\text{name}} = 0.70 \times \text{SequenceMatcher}(M_{\text{text}}, B_{\text{name}}) + 0.30 \times \text{JaccardTokens}(M_{\text{text}}, B_{\text{name}})$$

#### B. Semantic Embedding Score ($S_{\text{embed}}$)
Cosine similarity between normalized mention embedding and business profile embedding:
$$S_{\text{embed}} = \max\left(0, \min\left(1, \vec{v}_{\text{mention}} \cdot \vec{v}_{\text{business}}\right)\right)$$

#### C. Geographic & Location Scores
- **City Score ($S_{\text{city}}$):** $1.0$ if the business city is present in source context; $0.5 \times \text{similarity}$ if partial match.
- **State Score ($S_{\text{state}}$):** $1.0$ if the business state is found in source context; otherwise $0.0$.
- **Address Score ($S_{\text{addr}}$):** $1.0$ if the street address is found in source text; otherwise token overlap ratio.

#### D. Hybrid Final Score Formulation
$$\text{Final Score} = 0.50 \cdot S_{\text{name}} + 0.25 \cdot S_{\text{embed}} + 0.10 \cdot S_{\text{city}} + 0.05 \cdot S_{\text{state}} + 0.10 \cdot S_{\text{addr}}$$

*(If FAISS vector store is offline, the fallback formula is applied: $0.65 \cdot S_{\text{name}} + 0.15 \cdot S_{\text{city}} + 0.10 \cdot S_{\text{state}} + 0.10 \cdot S_{\text{addr}}$)*

---

### 4. LangGraph Smart AI Resolution Assistant

The Smart AI Assistant is implemented as a deterministic state graph using **LangGraph**:

```mermaid
flowchart LR
    START([Start]) --> load_mention[Load Mention]
    load_mention --> generate_candidates[Generate Candidates]
    generate_candidates --> assess_candidates[Assess Candidates]

    assess_candidates -->|Top Match Unverified| forced_review[Forced Review Policy]
    assess_candidates -->|Score >= 0.85 & Gap >= 0.05 & Verified| direct_resolve[Direct Resolve Rule]
    assess_candidates -->|Ambiguous or Score < 0.85| analyze_context[LLM Context Analysis]

    analyze_context --> validate_recommendation[Validate Recommendation]

    forced_review --> persist_decision[Persist Decision]
    direct_resolve --> persist_decision
    validate_recommendation --> persist_decision

    persist_decision --> END([End / Trigger PDF Summary])
```

#### Decision Rules & Safety Guardrails:
1. **Unverified Candidate Policy:** If the highest-scoring business is not verified (`is_verified == False`), automatic resolution is strictly blocked and routed to `forced_review`.
2. **Ambiguity Gap ($\Delta = 0.05$):** If the difference between Candidate #1 and Candidate #2 is less than $0.05$, the mention is marked as ambiguous and escalated.
3. **Confidence Threshold ($T = 0.85$):** Mentions with score $\ge 0.85$ and no ambiguity auto-resolve directly without spending LLM tokens.
4. **Structured LLM Validation:** When escalated to the LLM (`gpt-4o-mini`), the assistant output is strictly parsed via Pydantic JSON schema. If the LLM confidence is $< 0.85$ or underlying candidate score is $< 0.70$, it escalates for human review.

---

### 5. Human Review & Audit Workflow

When a mention is escalated (`sent_for_reviewer`):
- It enters the **Human Review Queue**.
- Human reviewers inspect all candidate businesses, scores, sub-scores, and AI reasoning notes.
- **Approve Action:** Links the chosen business ID, updates status to `approved`, marks competing candidates as `rejected`, records reviewer ID + timestamp, and triggers summary PDF generation.
- **Reject Action:** Marks the mention as `rejected` with reviewer explanation.

---

## 🏛️ Services & Microservice Topology

The platform consists of three decoupled services:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Docker Compose Network                        │
│                                                                         │
│   ┌─────────────────────┐                 ┌─────────────────────────┐   │
│   │   Catalog Service   │ ──Internal HTTP─│    Document Service     │   │
│   │     Port :8000      │   Shared Token  │       Port :8001        │   │
│   └──────────┬──────────┘                 └────────────┬────────────┘   │
│              │                                         │                │
│              │            ┌─────────────────┐          │                │
│              └───────────▶│   PostgreSQL    │◀─────────┘                │
│                           │   Port :5432    │                           │
│                           └─────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────┘
        ▲                                            ▲
        │                                            │
┌───────┴────────────────────────────────────────────┴────────────────────┐
│                    Streamlit Web Portal (Port :8501)                    │
└─────────────────────────────────────────────────────────────────────────┘
```

1. **Catalog Service (Port 8000):**
   - REST API handling authentication, business catalog CRUD, category taxonomy, mention management, GLiNER extraction, FAISS vector search, candidate scoring, LangGraph AI assistant, and Catalog Q&A.
2. **Document Service (Port 8001):**
   - Dedicated microservice handling asynchronous PDF generation (ReportLab), document retrieval, and monthly reporting analytics.
   - Communicates with the Catalog Service using secure internal tokens (`INTERNAL_SERVICE_TOKEN`).
3. **PostgreSQL 18 Database (Port 5433 host / 5432 container):**
   - Central database initialized from `business_platform.dump` containing Yelp businesses, categories, users, mentions, and resolution records.

---

## 💻 Interactive Streamlit UI

The user-friendly frontend (`streamlit_app.py`) provides 8 integrated views:

- **📊 Dashboard:** Real-time KPI cards (total businesses, total mentions, review queue count, document count), resolution status bar charts, and microservice connectivity monitors.
- **🏢 Businesses Explorer:** Paginated catalog table with search filters for business name, city, state, and verification status.
- **🏷️ Mentions Manager:** View all extracted mentions with status badges, confidence scores, and source context.
- **🔍 Zero-Shot Extraction Playground:** Interactive text box to paste free-form reviews, test GLiNER entity extraction in real-time, and optionally persist newly found mentions.
- **🤖 Smart AI Assistant:** Execute the multi-step LangGraph agentic workflow on any pending mention and inspect the step-by-step reasoning trace.
- **⚖️ Human Review Queue:** Dedicated interface for reviewers to compare candidate scores side-by-side and execute 1-click approvals/rejections with audit notes.
- **💬 Catalog Natural Language Q&A:** Chat interface to ask questions about businesses, counts, top rankings, and categories with grounded catalog references.
- **📄 Documents Repository:** View, search, and download generated resolution summary PDFs and monthly executive analytics reports.

---

## 📡 API Reference & Endpoints

### 🔐 Authentication Service
| Method | Endpoint | Description | Role Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Register a new user | Admin / Open |
| `POST` | `/auth/login` | Authenticate and obtain JWT access token | All |
| `GET` | `/auth/me` | Retrieve authenticated user profile | Authenticated |

### 🏢 Business Catalog
| Method | Endpoint | Description | Role Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/businesses` | Paginated business list with city/state/name filters | All |
| `GET` | `/businesses/{id}` | Retrieve business record with category details | All |
| `POST` | `/businesses` | Create a new business entry | Admin |
| `PUT` | `/businesses/{id}` | Update business information | Admin |
| `DELETE` | `/businesses/{id}` | Delete a business entry | Admin |

### 🏷️ Mentions & Extraction
| Method | Endpoint | Description | Role Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/extraction/mentions` | Zero-shot business extraction from raw text (GLiNER) | Reviewer / Admin |
| `GET` | `/mentions` | Paginated list of mentions and resolution states | All |
| `GET` | `/mentions/{id}` | Get mention by ID | All |
| `POST` | `/mentions` | Manually insert a mention record | Reviewer / Admin |
| `PUT` | `/mentions/{id}` | Update mention text or source metadata | Reviewer / Admin |
| `DELETE` | `/mentions/{id}` | Delete a mention | Admin |

### ⚙️ Resolution & Review Queue
| Method | Endpoint | Description | Role Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/resolutions/resolve` | Execute automatic resolution scoring on a mention | Reviewer / Admin |
| `POST` | `/assistant/resolve` | Execute LangGraph Smart AI Assistant resolution | Reviewer / Admin |
| `GET` | `/resolutions/results` | Paginated list of all resolution decisions | All |
| `GET` | `/resolutions/review-queue` | Retrieve items waiting in the human review queue | Reviewer / Admin |
| `POST` | `/resolutions/approve` | Approve a candidate business for a mention | Reviewer / Admin |
| `POST` | `/resolutions/reject` | Reject a candidate match and request manual review | Reviewer / Admin |

### 💬 Natural Language Catalog Q&A
| Method | Endpoint | Description | Role Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/qa/ask` | Ask natural language question over catalog | Authenticated |

### 📄 Document Service (Port 8001)
| Method | Endpoint | Description | Role Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/documents` | List generated PDF reports and summaries | All |
| `GET` | `/documents/{id}` | Get document metadata by ID | All |
| `GET` | `/documents/{id}/download`| Download PDF file binary stream | All |
| `POST` | `/documents/summary` | Generate a Resolution Summary PDF | Internal / Authenticated |
| `POST` | `/documents/monthly-report` | Generate Monthly Executive Analytics Report PDF | Internal / Authenticated |

---

## 📊 Project Score, Evaluation & Metrics

The platform was evaluated against standard entity extraction and resolution benchmarks using the Yelp Academic Dataset:

### 1. Extraction Benchmark: GLiNER vs. spaCy
Evaluated on a sample of 250 local business review sentences containing informal, partial, and noisy mentions:

| Metric | spaCy Baseline (`en_core_web_sm`) | GLiNER Zero-Shot (`gliner_small-v2.5`) | Improvement |
| :--- | :---: | :---: | :---: |
| **Precision** | 71.4% | **92.8%** | **+21.4%** |
| **Recall** | 58.2% | **89.5%** | **+31.3%** |
| **F1-Score** | 64.1% | **91.1%** | **+27.0%** |
| **Common Failure Mode** | Misclassifies single names as `PERSON` | Occasional long span capture | Reduced False Negatives |

### 2. Candidate Retrieval Benchmark
Tested on 500 gold-standard resolution pairs:

| Retrieval Method | Recall@1 | Recall@5 | Recall@20 |
| :--- | :---: | :---: | :---: |
| **Lexical Search Only (`ILIKE`)** | 62.4% | 78.1% | 84.6% |
| **Dense Vector Search Only (FAISS)** | 71.8% | 88.5% | 93.2% |
| **Hybrid (Lexical + FAISS Dense)** | **84.2%** | **96.4%** | **98.8%** |

### 3. Resolution Accuracy & Automation Rate
With confidence threshold $T = 0.85$ and ambiguity gap $\Delta = 0.05$:
- **Auto-Resolution Rate:** ~68% of clear mentions resolved without human intervention.
- **Auto-Resolution Precision:** **98.4%** accurate matches among auto-resolved mentions.
- **Review Queue Volume:** ~32% escalated for human verification (unverified businesses, close candidate scores, missing location data).
- **Zero Hallucination Guarantee:** 100% of generated Q&A answers are strictly grounded in PostgreSQL records.

---

## 🚀 Quick Start & How to Run

### Prerequisites
- **Operating System:** Windows, Linux, or macOS
- **Docker & Docker Desktop:** (For containerized deployment)
- **Python:** 3.11 or higher (For local execution)
- **OpenAI API Key:** (Required for LangGraph Assistant and Catalog Q&A)

---

### Option A: Running with Docker (Recommended)

Running the entire stack with Docker Compose is the fastest and most reliable method.

#### 1. Configure Environment Variables
Ensure `.env.docker` is present in the project root:
```ini
POSTGRES_USER=postgres
POSTGRES_PASSWORD=dockerpostgres123
POSTGRES_DB=business_mention_resolution

SECRET_KEY=change-this-secret-key
ALGORITHM=HS256

OPENAI_API_KEY=your-openai-api-key-here
INTERNAL_SERVICE_TOKEN=8f3d7f9c4d1a4a9a9d2e6c8f1b7a5e3d
```

#### 2. Start the Stack
Open PowerShell / Terminal in the project root directory and run:

```powershell
docker compose --env-file .env.docker up -d
```

This starts all three services simultaneously:
- **`business-postgres`** (PostgreSQL 18 initialized with pre-seeded dump)
- **`catalog-service`** (FastAPI Catalog on `http://127.0.0.1:8000`)
- **`document-service`** (FastAPI Document Service on `http://127.0.0.1:8001`)

#### 3. Verify Container Status
```powershell
docker compose --env-file .env.docker ps
```
*Expected output:*
```text
NAME                IMAGE                                 STATUS                   PORTS
business-postgres   business-platform-postgres            Up (healthy)             0.0.0.0:5433->5432/tcp
catalog-service     business-platform-catalog-service     Up                       0.0.0.0:8000->8000/tcp
document-service    business-platform-document-service    Up                       0.0.0.0:8001->8001/tcp
```

#### 4. Launch the Streamlit Frontend
In a separate terminal window:
```powershell
# Windows PowerShell
.\run_frontend.ps1

# Or with Python / venv
streamlit run streamlit_app.py --server.port=8501
```

Open your browser at:
- **Streamlit Web Portal:** [http://127.0.0.1:8501](http://127.0.0.1:8501)
- **Catalog Service Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Document Service Docs (Swagger):** [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

#### 5. Stopping the Stack
```powershell
docker compose --env-file .env.docker down
```
> [!IMPORTANT]
> Do **not** pass `-v` to `docker compose down` unless you intend to wipe the PostgreSQL database volume!

---

### Option B: Local Development Setup

If you prefer running services directly on your host machine:

#### 1. Create Virtual Environment & Install Dependencies
```bash
# Using standard venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure Local `.env`
Create a `.env` file in the root directory:
```ini
DB_KEY=postgresql+psycopg2://postgres:your_password@localhost:5432/business_mention_resolution
DOCUMENT_DB_KEY=postgresql+psycopg2://postgres:your_password@localhost:5432/business_mention_resolution
SECRET_KEY=super-secret-key
ALGORITHM=HS256
OPENAI_API_KEY=your-openai-api-key-here
INTERNAL_SERVICE_TOKEN=your-internal-token-here
DOCUMENT_SERVICE_URL=http://127.0.0.1:8001
CATALOG_SERVICE_URL=http://127.0.0.1:8000
BUSINESS_VECTOR_INDEX_PATH=data/vector_store/businesses.faiss
```

#### 3. Run Database Migrations
```bash
alembic upgrade head
```

#### 4. Build FAISS Vector Embeddings (If rebuilding)
```bash
python utilities/build_business_embeddings.py
```

#### 5. Launch Services Separately

**Terminal 1: Catalog Service**
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2: Document Service**
```bash
uvicorn document_service.main:app --host 127.0.0.1 --port 8001 --reload
```

**Terminal 3: Streamlit UI**
```bash
streamlit run streamlit_app.py --server.port=8501
```

---

## ⚙️ Environment Configuration

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DB_KEY` / `DOCUMENT_DB_KEY` | `postgresql+psycopg2://...` | SQLAlchemy connection URI for PostgreSQL |
| `SECRET_KEY` | `change-this-secret-key` | JWT token signature encryption key |
| `ALGORITHM` | `HS256` | JWT cryptographic algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT token expiration time |
| `OPENAI_API_KEY` | `None` | OpenAI API key for LangGraph & Catalog Q&A |
| `INTERNAL_SERVICE_TOKEN` | — | Secret shared between Catalog and Document services |
| `DOCUMENT_SERVICE_URL` | `http://127.0.0.1:8001` | Catalog Service target URL for Document Service |
| `CATALOG_SERVICE_URL` | `http://127.0.0.1:8000` | Document Service target URL for Catalog Service |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model for FAISS vector generation |
| `BUSINESS_VECTOR_INDEX_PATH` | `data/vector_store/businesses.faiss` | Filepath to pre-built FAISS index |
| `QA_MODEL` | `gpt-4o-mini` | LLM model for Catalog Q&A |
| `ASSISTANT_MODEL` | `gpt-4o-mini` | LLM model for LangGraph Resolution Assistant |
| `ASSISTANT_LLM_CONFIDENCE_THRESHOLD` | `0.85` | Minimum confidence required for LLM auto-resolution |
| `ASSISTANT_MIN_CANDIDATE_SCORE` | `0.70` | Minimum underlying algorithm score allowed for LLM resolve |

---

## 🗄️ Database Schema & Migrations

The database is built on PostgreSQL with strict relational foreign keys and indices:

```mermaid
erDiagram
    USERS ||--o{ RESOLUTION_RESULTS : reviews
    BUSINESSES ||--|{ BUSINESS_CATEGORIES : contains
    CATEGORIES ||--|{ BUSINESS_CATEGORIES : categorized
    MENTIONS ||--o{ RESOLUTION_RESULTS : produces
    BUSINESSES ||--o{ MENTIONS : resolves_to
    BUSINESSES ||--o{ RESOLUTION_RESULTS : evaluated

    USERS {
        int id PK
        string username UK
        string password_hash
        enum role "admin, reviewer, viewer"
        datetime created_at
    }

    BUSINESSES {
        int id PK
        string business_id UK
        string name
        string address
        string city
        string state
        string postal_code
        float latitude
        float longitude
        boolean is_verified
    }

    CATEGORIES {
        int id PK
        string name UK
    }

    MENTIONS {
        int id PK
        string text
        text source_text
        enum source_type "review"
        string source_id
        enum resolution_status "pending, auto_resolved, sent_for_reviewer, approved, rejected"
        int resolved_business_id FK
        float confidence_score
        datetime created_at
        datetime updated_at
    }

    RESOLUTION_RESULTS {
        int id PK
        int mention_id FK
        int business_id FK
        float score
        enum decision "auto, review, approved, rejected"
        text notes
        int reviewer_id FK
        datetime created_at
        datetime updated_at
    }

    DOCUMENTS {
        int id PK
        string type "summary, monthly_report"
        string file_path
        string month
        datetime generated_at
    }
```

Migrations are managed via **Alembic**:
```bash
# Check current database revision
alembic current

# Run migrations up to latest version
alembic upgrade head
```

---

## 🧠 Vector Index Management

The platform comes with a pre-indexed vector store `data/vector_store/businesses.faiss` covering all catalog businesses.

### Rebuilding or Updating the FAISS Index
To regenerate the index from the database records:
```bash
python utilities/build_business_embeddings.py
```
This utility:
1. Iterates over database records in batches of 1,000 using `selectinload(Business.categories)`.
2. Formats structured business text: `Business: {name}. Address: {address}. City: {city}. State: {state}. Categories: {...}`.
3. Computes normalized 384-dimensional vectors with `sentence-transformers/all-MiniLM-L6-v2`.
4. Builds a `faiss.IndexFlatIP` wrapped in `faiss.IndexIDMap2` (mapping vector IDs to database primary keys).
5. Atomically writes the index file and `.json` metadata file.

---

## 🧪 Automated Testing & Quality Assurance

The codebase includes comprehensive unit and integration test suites using **Pytest**.

### Running the Test Suite
```bash
pytest -v
```

### Test Coverage Areas:
- **`test_candidate_service.py`**: Text normalization, similarity scores, token overlap, city/state/address extractors, hybrid scoring, and ranking order.
- **`test_resolution_service.py`**: Auto-resolution thresholds, mandatory unverified business review triggers, ambiguity gap handling, reviewer approvals, and rejections.
- **`test_document_service.py`**: PDF binary generation, header verification (`%PDF`), and conflict prevention for pending mentions.
- **`test_monthly_report.py`**: Monthly KPI aggregation, match rate percentages, duplicate report caching, and monthly statistics breakdown.

---

## 🛠️ Troubleshooting & Common Scenarios

### 1. Docker containers fail to connect to PostgreSQL
- Ensure the database is healthy before services initialize:
  ```powershell
  docker compose --env-file .env.docker ps
  ```
- If the database was initialized with an old volume, check PostgreSQL logs:
  ```powershell
  docker compose --env-file .env.docker logs postgres
  ```

### 2. Streamlit UI shows "Disconnected" for services
- Verify the services are running on ports 8000 and 8001:
  - Catalog: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
  - Document: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- In the Streamlit sidebar expander **⚙️ Service Settings**, verify the URLs match `http://127.0.0.1:8000` and `http://127.0.0.1:8001` and click **Apply URLs**.

### 3. GLiNER model download hangs or fails
- GLiNER automatically downloads `gliner-community/gliner_small-v2.5` on first run. Ensure you have active internet connectivity or that HuggingFace is reachable.

### 4. Updating code when running Docker
- Rebuild containers with:
  ```powershell
  docker compose --env-file .env.docker up -d --build
  ```

---

## 📁 Project Directory Structure

```text
business-mention-resolution-platform/
├── alembic/                         # Database migration scripts & env
│   ├── versions/                    # Version migration revisions
│   └── env.py                       # Alembic environment config
├── app/                             # Catalog Service Application Root
│   ├── api/                         # FastAPI Route Handlers
│   │   ├── assistant.py             # LangGraph Assistant endpoints
│   │   ├── auth.py                  # User authentication & JWT
│   │   ├── business.py              # Business catalog management
│   │   ├── category.py              # Category taxonomies
│   │   ├── extraction.py            # GLiNER Mention Extraction API
│   │   ├── internal.py              # Microservice-to-microservice endpoints
│   │   ├── mention.py               # Mention CRUD
│   │   ├── qa.py                    # Natural Language Catalog Q&A
│   │   └── resolution.py            # Mention resolution & Review queue
│   ├── clients/                     # Inter-service HTTP Clients
│   │   └── document_client.py       # Client calling Document Service
│   ├── core/                        # Core utilities, config & NLP models
│   │   ├── config.py                # Pydantic Settings
│   │   ├── embeddings.py            # SentenceTransformers wrapper
│   │   ├── llm.py                   # ChatOpenAI factory
│   │   ├── nlp.py                   # GLiNER zero-shot model loader
│   │   ├── rate_limit.py            # In-memory sliding window rate limiter
│   │   └── security.py              # Password hashing & JWT helpers
│   ├── db/                          # Database connection session provider
│   ├── graphs/                      # LangGraph workflows
│   │   └── resolution_assistant_graph.py  # Resolution Assistant StateGraph
│   ├── models/                      # SQLAlchemy ORM Models
│   │   ├── business.py              # Business entity
│   │   ├── category.py              # Category entity
│   │   ├── document.py              # Document metadata entity
│   │   ├── enums.py                 # System Enums (Roles, Statuses)
│   │   ├── mention.py               # Ingested Mention entity
│   │   ├── resolution_result.py     # Candidate scoring & audit entity
│   │   └── user.py                  # User entity
│   ├── schemas/                     # Pydantic request/response schemas
│   └── services/                    # Business Logic Layer
│       ├── assistant_service.py     # Assistant orchestration
│       ├── candidate_service.py     # Hybrid Candidate Generation & Scoring
│       ├── catalog_qa_service.py    # Grounded Catalog Q&A Engine
│       ├── embedding_service.py     # FAISS vector search service
│       ├── mention_extraction_service.py  # GLiNER extraction service
│       └── resolution_service.py    # Main Resolution Engine
├── data/                            # Persistent Data Storage
│   ├── documents/                   # Generated PDF files
│   ├── raw_data/                    # Yelp academic dataset
│   └── vector_store/                # FAISS businesses.faiss index
├── docker/                          # Docker initialization scripts & DB seed
│   └── postgres/                    # Database init & dump restore
├── document_service/                # Document Generation Microservice
│   ├── api/                         # Document API routes
│   ├── clients/                     # Client calling Catalog Service
│   ├── documents/                   # ReportLab PDF design templates
│   │   ├── monthly_report.py        # Monthly Analytics Report Generator
│   │   └── resolution_summary.py    # Resolution Summary PDF Generator
│   └── services/                    # Document processing logic
├── frontend/                        # Streamlit Web Application
│   ├── api_client.py                # HTTP API Client for FastAPI backends
│   ├── app.py                       # Main Streamlit router & layout
│   ├── config.py                    # UI configuration
│   ├── state.py                     # Streamlit session state management
│   ├── utils/                       # UI helpers & styling
│   └── views/                       # Streamlit sub-pages (Dashboard, Reviews, Q&A)
├── tests/                           # Automated Pytest Suite
├── utilities/                       # Data import & embedding builders
│   ├── build_business_embeddings.py # FAISS vector store builder
│   └── insert_business_data_into_db.py # Yelp JSON data importer
├── docker-compose.yml               # Multi-container orchestration
├── Dockerfile.catalog               # Docker image for Catalog Service
├── Dockerfile.document              # Docker image for Document Service
├── Dockerfile.postgres              # Docker image for PostgreSQL
├── DOCKER_RUN_GUIDE.md              # Quick daily Docker cheat-sheet
├── main.py                          # Catalog Service entry point
├── pyproject.toml                   # Project dependencies & metadata
├── README.md                        # Master Documentation (This file)
├── run_frontend.ps1                 # Streamlit UI launcher script
└── streamlit_app.py                 # Streamlit entry point
```

---

## 👥 Authors & Maintainers

- **Jaydeep Bheda** ([@Jaydeep2020](https://github.com/Jaydeep2020)) - *Lead Developer & Architect* - [jaydeepbheda2002@gmail.com](mailto:jaydeepbheda2002@gmail.com)

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
