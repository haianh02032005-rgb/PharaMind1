from abc import ABC, abstractmethod
from typing import Any


class BaseImportAdapter(ABC):
    parser_version: str = "1.0.0"

    @abstractmethod
    def extract(
        self,
        file_bytes: bytes,
        filename: str,
        *,
        default_member_name: str | None = None,
    ) -> dict[str, Any]:
        """Extract raw structured payload from uploaded file bytes."""
        raise NotImplementedError

