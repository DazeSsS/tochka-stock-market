from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    success: bool = True

class ErrorResponse(BaseModel):
    detail: str

class NotFoundResponse(ErrorResponse):
    detail: str = Field(..., examples=['Object does not exist'])
