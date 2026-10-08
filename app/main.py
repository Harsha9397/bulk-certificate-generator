from pathlib import Path
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from .database import Base, engine, get_db, SessionLocal
from .models import Certificate, GenerationJob
from .schemas import JobCreate, JobOut
from .certificate_service import generate_certificate

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Bulk Certificate Generator", version="1.0.0")


def process_job(job_id: int):
    db = SessionLocal()
    try:
        job = db.get(GenerationJob, job_id)
        if not job:
            return
        job.status = "processing"
        db.commit()
        for cert in db.query(Certificate).filter(Certificate.job_id == job_id).all():
            try:
                # Allows one recipient to fail without stopping the batch.
                if not cert.recipient_name.strip():
                    raise ValueError("recipient name cannot be blank")
                cert.file_path = generate_certificate(job.id, cert.id, cert.recipient_name, job.course_name, job.event_date)
                cert.status = "completed"
                job.successful += 1
            except Exception as exc:
                cert.status = "failed"
                cert.error = str(exc)
                job.failed += 1
            db.commit()
        job.status = "completed" if job.failed == 0 else "completed_with_errors"
        db.commit()
    finally:
        db.close()

@app.post("/jobs", response_model=JobOut, status_code=202)
def create_job(payload: JobCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = GenerationJob(course_name=payload.course_name.strip(), event_date=payload.event_date.strip(), total=len(payload.recipients))
    db.add(job)
    db.flush()
    for recipient in payload.recipients:
        db.add(Certificate(job_id=job.id, recipient_name=recipient.name, recipient_email=str(recipient.email)))
    db.commit()
    db.refresh(job)
    background_tasks.add_task(process_job, job.id)
    return job_response(job)

@app.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(404, "Generation job not found")
    return job_response(job)

@app.get("/jobs/{job_id}/certificates/{certificate_id}")
def download_certificate(job_id: int, certificate_id: int, db: Session = Depends(get_db)):
    cert = db.get(Certificate, certificate_id)
    if not cert or cert.job_id != job_id:
        raise HTTPException(404, "Certificate not found")
    if cert.status != "completed" or not cert.file_path:
        raise HTTPException(409, "Certificate is not available")
    path = Path(cert.file_path)
    if not path.exists():
        raise HTTPException(404, "Certificate file not found")
    return FileResponse(path, media_type="application/pdf", filename=path.name)

def job_response(job: GenerationJob):
    return {
        "id": job.id,
        "status": job.status,
        "total": job.total,
        "successful": job.successful,
        "failed": job.failed,
        "course_name": job.course_name,
        "event_date": job.event_date,
        "certificates": job.recipients,
    }
