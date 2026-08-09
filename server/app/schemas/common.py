from pydantic import BaseModel, Field


class BulkDeleteRequest(BaseModel):
    """Delete a set of records by id, or all records when ``all`` is true."""

    ids: list[int] = Field(default_factory=list)
    all: bool = False


class BulkDeleteResponse(BaseModel):
    deleted: int
