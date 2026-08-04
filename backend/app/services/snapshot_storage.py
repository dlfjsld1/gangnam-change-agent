import hashlib
from pathlib import Path


class SnapshotStorage:
    def __init__(self, root: Path) -> None:
        self._root = root

    def store(self, category: str, filename: str, content: bytes) -> tuple[Path, str]:
        content_hash = hashlib.sha256(content).hexdigest()
        destination = self._root / category / f"{content_hash}-{filename}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return destination, content_hash
