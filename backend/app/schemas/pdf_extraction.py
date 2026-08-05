from typing import Literal

from pydantic import BaseModel, Field


PdfDocumentMode = Literal["text", "scanned", "mixed"]
PdfPageMethod = Literal["local_text", "openai_ocr"]


class PdfPageExtraction(BaseModel):
    page_number: int = Field(ge=1)
    method: PdfPageMethod
    text: str


class PdfDocumentExtraction(BaseModel):
    document_mode: PdfDocumentMode
    pages: list[PdfPageExtraction]
    text: str
