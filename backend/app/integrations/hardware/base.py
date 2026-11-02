from abc import ABC, abstractmethod
from typing import Any


class HardwareAdapter(ABC):
    @abstractmethod
    async def initialize_cabinet(
        self,
        cabinet_id: int,
        status: str = "OFFLINE",
        positions: list[int] | None = None,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def set_online(self, cabinet_id: int) -> dict[str, Any]:
        ...

    @abstractmethod
    async def set_offline(self, cabinet_id: int) -> dict[str, Any]:
        ...

    @abstractmethod
    async def open_compartment(
        self,
        cabinet_id: int,
        position: int,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def close_compartment(
        self,
        cabinet_id: int,
        position: int,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_state(self, cabinet_id: int) -> dict[str, Any]:
        ...

