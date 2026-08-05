from types import SimpleNamespace

import pytest

from app.tools.openai_ocr import OpenAIImageOcr


class FakeResponses:
    def __init__(self) -> None:
        self.requests: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.requests.append(kwargs)
        return SimpleNamespace(output_text="공고 이미지의 추출 텍스트")


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


def test_openai_ocr_sends_base64_png_to_responses_api() -> None:
    client = FakeClient()
    ocr = OpenAIImageOcr(client=client, model="gpt-test-ocr")

    result = ocr(b"\x89PNG test image bytes")

    assert result == "공고 이미지의 추출 텍스트"
    request = client.responses.requests[0]
    assert request["model"] == "gpt-test-ocr"
    content = request["input"][0]["content"]
    assert content[1]["type"] == "input_image"
    assert content[1]["image_url"].startswith("data:image/png;base64,")
    assert content[1]["detail"] == "high"


def test_openai_ocr_rejects_unsupported_image_before_api_call() -> None:
    client = FakeClient()

    with pytest.raises(ValueError, match="Unsupported image format"):
        OpenAIImageOcr(client=client)(b"not-an-image")

    assert client.responses.requests == []
