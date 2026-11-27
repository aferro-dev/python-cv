from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Username = Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_-]{3,64}$")]


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: Username
    password: str = Field(min_length=10, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DocumentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=50_000)


class DocumentRead(DocumentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=8)
    max_output_tokens: int = Field(default=256, ge=16, le=1024)


class Source(BaseModel):
    document_id: str
    title: str
    excerpt: str
    score: float


class Answer(BaseModel):
    answer: str
    sources: list[Source]
    provider: str


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: Literal["queued", "running", "retrying", "succeeded", "failed", "cancelled"]
    attempts: int
    result: Answer | None
    error: str | None
    created_at: datetime
    updated_at: datetime
