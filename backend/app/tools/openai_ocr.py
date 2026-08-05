from base64 import b64encode
import os
from typing import Protocol

from openai import OpenAI


DEFAULT_OCR_MODEL = "gpt-5.6-luna"
OCR_PROMPT = (
    "이 공공문서 이미지에서 보이는 한국어와 영어 텍스트를 빠짐없이 그대로 "
    "추출하세요. 요약하거나 추론하지 말고 추출한 텍스트만 반환하세요."
)


class ResponsesApi(Protocol):
    def create(self, **kwargs: object) -> object:
        """Create one OpenAI Responses API request."""


class OpenAIClient(Protocol):
    responses: ResponsesApi


class OpenAIImageOcr:
    def __init__(
        self,
        client: OpenAIClient | None = None,
        model: str | None = None,
    ) -> None:
        self._client = client or OpenAI()
        self._model = model or os.getenv("OPENAI_OCR_MODEL", DEFAULT_OCR_MODEL)

    def __call__(self, image_content: bytes) -> str:
        media_type = _image_media_type(image_content)
        encoded_image = b64encode(image_content).decode("ascii")
        response = self._client.responses.create(
            model=self._model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": OCR_PROMPT},
                        {
                            "type": "input_image",
                            "image_url": (f"data:{media_type};base64,{encoded_image}"),
                            "detail": "high",
                        },
                    ],
                }
            ],
        )
        output_text = str(getattr(response, "output_text", "")).strip()
        if not output_text:
            raise ValueError("OpenAI OCR returned no text")
        return output_text


def _image_media_type(content: bytes) -> str:
    if content.startswith(b"\x89PNG"):
        return "image/png"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"GIF8"):
        return "image/gif"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError("Unsupported image format for OpenAI OCR")
