"""FailedLogEventRepository: the dead-letter persistence contract (Unit 3).
Lives in db/ alongside the other repositories per project-structure.md's
consistency rule, even though only Unit 3 reads/writes it today.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .models import FailedLogEvent


class FailedLogEventRepository(ABC):
    @abstractmethod
    async def insert(self, record: FailedLogEvent) -> None: ...
