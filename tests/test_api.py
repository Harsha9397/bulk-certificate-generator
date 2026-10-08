import time
from app.database import SessionLocal
from app.models import GenerationJob

def wait_for_completion(client, job_id):
    for _ in range(50):
        response = client.get(f"/jobs/{job_id}")
        data = response.json()
        if data["status"] in {"completed", "completed_with_errors"}:
            return data
        time.sleep(0.02)
    raise AssertionError("job did not complete")

def test_create_job_and_status(client):
    payload = {"course_name":"Python Course","event_date":"2026-10-08","recipients":[{"name":"Alice Smith","email":"alice@example.com"},{"name":"Bob Jones","email":"bob@example.com"}]}
    r = client.post("/jobs", json=payload)
    assert r.status_code == 202
    data = wait_for_completion(client, r.json()["id"])
    assert data["total"] == 2
    assert data["successful"] == 2
    assert data["failed"] == 0
    assert all(c["status"] == "completed" for c in data["certificates"])

def test_input_validation(client):
    r = client.post("/jobs", json={"course_name":"Python","event_date":"2026","recipients":[{"name":"A","email":"not-email"}]})
    assert r.status_code == 422

def test_certificate_retrieval(client):
    r = client.post("/jobs", json={"course_name":"Python","event_date":"2026-10-08","recipients":[{"name":"Alice Smith","email":"alice@example.com"}]})
    data = wait_for_completion(client, r.json()["id"])
    cert_id = data["certificates"][0]["id"]
    download = client.get(f"/jobs/{data['id']}/certificates/{cert_id}")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"


def test_individual_failure_does_not_stop_batch(client, monkeypatch):
    from app import main
    original = main.generate_certificate
    calls = {"n": 0}
    def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("simulated PDF failure")
        return original(*args, **kwargs)
    monkeypatch.setattr(main, "generate_certificate", flaky)
    r = client.post("/jobs", json={"course_name":"Python","event_date":"2026-10-08","recipients":[{"name":"First User","email":"first@example.com"},{"name":"Second User","email":"second@example.com"}]})
    data = wait_for_completion(client, r.json()["id"])
    assert data["status"] == "completed_with_errors"
    assert data["successful"] == 1
    assert data["failed"] == 1
    assert {c["status"] for c in data["certificates"]} == {"completed", "failed"}
