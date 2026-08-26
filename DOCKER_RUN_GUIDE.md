# Business Mention Resolution Platform — Docker Run Guide

Use this file whenever you restart your laptop and want to run the project with Docker.

## 1. Start Docker Desktop

Open **Docker Desktop** and wait until Docker is fully running.

## 2. Open the project folder

Open PowerShell in:

```powershell
D:\Sculptsoft\business-mention-resolution-platform
```

Or run:

```powershell
cd D:\Sculptsoft\business-mention-resolution-platform
```

## 3. Start the complete project

Run:

```powershell
docker compose --env-file .env.docker up -d
```

This starts all three services:

- PostgreSQL
- Catalog Service
- Document Service

You do **not** need to start each service separately.

## 4. Check that everything is running

Run:

```powershell
docker compose --env-file .env.docker ps
```

Expected:

```text
business-postgres    Up (healthy)
catalog-service      Up
document-service     Up
```

## 5. Open the APIs

### Catalog Service

```text
http://127.0.0.1:8000/docs
```

### Document Service

```text
http://127.0.0.1:8001/docs
```

## Normal Daily Commands

### Start project

```powershell
docker compose --env-file .env.docker up -d
```

### Stop project

```powershell
docker compose --env-file .env.docker down
```

### Check status

```powershell
docker compose --env-file .env.docker ps
```

### View all logs

```powershell
docker compose --env-file .env.docker logs --tail=100
```

### Catalog logs

```powershell
docker compose --env-file .env.docker logs --tail=100 catalog-service
```

### Document Service logs

```powershell
docker compose --env-file .env.docker logs --tail=100 document-service
```

### PostgreSQL logs

```powershell
docker compose --env-file .env.docker logs --tail=100 postgres
```

## When I Change Python Code

If you modify application code, rebuild the Docker images:

```powershell
docker compose --env-file .env.docker up -d --build
```

Then check:

```powershell
docker compose --env-file .env.docker ps
```

## When I Change Only `.env.docker`

Recreate the containers so the new environment variables are loaded:

```powershell
docker compose --env-file .env.docker up -d --force-recreate
```

## Important Data

### PostgreSQL

PostgreSQL uses the Docker named volume:

```text
postgres_data
```

So this command is safe:

```powershell
docker compose --env-file .env.docker down
```

Your database remains saved.

### FAISS index

The existing FAISS index is mounted from:

```text
data/vector_store/
```

The project uses the existing index instead of rebuilding embeddings every time.

### Generated documents

Generated PDFs/documents are persisted in:

```text
data/documents/
```

## VERY IMPORTANT

Normally **DO NOT run**:

```powershell
docker compose --env-file .env.docker down -v
```

`-v` removes Docker volumes and can delete the PostgreSQL database volume.

Use this instead:

```powershell
docker compose --env-file .env.docker down
```

## If Something Is Not Working

First check:

```powershell
docker compose --env-file .env.docker ps
```

Then check the failing service logs.

Catalog:

```powershell
docker compose --env-file .env.docker logs --tail=100 catalog-service
```

Document Service:

```powershell
docker compose --env-file .env.docker logs --tail=100 document-service
```

PostgreSQL:

```powershell
docker compose --env-file .env.docker logs --tail=100 postgres
```

## Quickest Reminder

Every normal day:

```powershell
cd D:\Sculptsoft\business-mention-resolution-platform
docker compose --env-file .env.docker up -d
```

Then open:

```text
Catalog:  http://127.0.0.1:8000/docs
Document: http://127.0.0.1:8001/docs
```

When finished:

```powershell
docker compose --env-file .env.docker down
```

## Architecture

```text
Docker Compose
│
├── PostgreSQL
│   └── persistent Docker volume
│
├── Catalog Service
│   └── http://127.0.0.1:8000
│
└── Document Service
    └── http://127.0.0.1:8001

Host persistent folders
├── data/vector_store/
│   └── FAISS business index
│
└── data/documents/
    └── generated documents
```

## One-Line Rule

**Laptop restart → Start Docker Desktop → Open project folder → Run:**

```powershell
docker compose --env-file .env.docker up -d
```
