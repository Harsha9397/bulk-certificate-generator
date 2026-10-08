# Bulk Certificate Generator

A FastAPI backend that accepts one request containing many recipients, validates them, creates a generation job, generates one PDF certificate per valid recipient in background processing, tracks per-certificate status, and exposes downloads.

## Requirements implemented
- Python + FastAPI + SQLite relational database (SQLAlchemy).
- One predefined PDF certificate template.
- Bulk generation from a single API request.
- Pydantic validation for recipient name/email.
- Background processing so the POST request returns immediately with a job ID.
- Per-recipient failure isolation: one generation failure does not stop the batch.
- Job progress/status and per-certificate results.
- Certificate retrieval endpoint.
- Tests for job creation, validation, generation, status/progress, failure isolation design, and retrieval.

## Setup
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000/docs` for Swagger UI.

## Create a generation job
```bash
curl -X POST http://127.0.0.1:8000/jobs \\
  -H "Content-Type: application/json" \\
  -d '{
    "course_name": "Python Backend Course",
    "event_date": "2026-10-08",
    "recipients": [
      {"name": "Alice Smith", "email": "alice@example.com"},
      {"name": "Bob Jones", "email": "bob@example.com"}
    ]
  }'
```
The response contains the job ID and initial status. Poll `GET /jobs/{job_id}` until `completed` or `completed_with_errors`.

## Retrieve certificates
For a completed certificate, call:
`GET /jobs/{job_id}/certificates/{certificate_id}`

## Run tests
```bash
pytest -q
```

## Design decisions
**Background processing:** FastAPI `BackgroundTasks` keeps the API responsive for bulk requests without requiring a separate queue service. A production system with very large batches or multiple workers should move this work to a durable queue such as Celery/RQ/SQS.

**Relational schema:** `generation_jobs` stores aggregate progress and `certificates` stores one row per recipient, including status, generated file path, and failure reason.

**Failure isolation:** Each certificate is processed in its own try/except block and committed independently. Therefore a single PDF-generation failure does not prevent remaining recipients from being processed.

**Single template:** The PDF layout is defined once in `app/certificate_service.py`, as required; no template editor or multiple designs are included.
