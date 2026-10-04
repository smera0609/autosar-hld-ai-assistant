from typing import Any
from pydantic import BaseModel, Field


class PageContent(BaseModel):
    page_number: int
    text: str
    character_count: int = 0


class DocumentData(BaseModel):
    filename: str
    file_path: str
    page_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    pages: list[PageContent] = Field(default_factory=list)
    full_text: str = ""
    extraction_method: str = "pymupdf"


class DocumentChunk(BaseModel):
    chunk_id: str
    filename: str
    page_number: int
    text: str
    section: str | None = None
    start_char: int = 0
    end_char: int = 0