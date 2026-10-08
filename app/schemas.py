from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class RecipientIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("name cannot be blank")
        return value

class JobCreate(BaseModel):
    course_name: str = Field(min_length=1, max_length=255)
    event_date: str = Field(min_length=1, max_length=50)
    recipients: list[RecipientIn] = Field(min_length=1, max_length=10000)

class CertificateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    recipient_name: str
    recipient_email: str
    status: str
    file_path: str | None = None
    error: str | None = None

class JobOut(BaseModel):
    id: int
    status: str
    total: int
    successful: int
    failed: int
    course_name: str
    event_date: str
    certificates: list[CertificateOut]
