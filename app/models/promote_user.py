from typing import Literal

from pydantic import BaseModel, Field


class PromoteUserRequest(BaseModel):
    role: Literal["therapist", "admin"] = Field(...)
