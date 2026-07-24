from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TaskKind(StrEnum):
    QUESTION = "question"
    REVIEW = "review"
    DIALOGUE = "dialogue"
    RETURN = "return"


class TaskStatus(StrEnum):
    NEW = "new"
    DEFERRED = "deferred"
    AWAITING_HUMAN = "awaiting_human"
    COMPLETED = "completed"


class Priority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass(frozen=True, slots=True)
class Product:
    id: str
    name: str
    category: str
    facts: str


@dataclass(frozen=True, slots=True)
class IncomingTask:
    id: str
    kind: TaskKind
    product_id: str
    buyer_label: str
    subject: str
    message: str
    history: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Recommendation:
    scenario: str
    priority: Priority
    priority_reason: str
    draft: str
    proposed_action: str
    risks: tuple[str, ...]
    needs_human: bool
    requires_confirmation: bool


@dataclass(frozen=True, slots=True)
class Task:
    id: str
    kind: TaskKind
    status: TaskStatus
    product: Product
    buyer_label: str
    subject: str
    message: str
    history: tuple[str, ...]
    scenario: str
    priority: Priority
    priority_reason: str
    draft: str
    proposed_action: str
    risks: tuple[str, ...]
    needs_human: bool
    requires_confirmation: bool
    return_confirmed: bool = False


@dataclass(frozen=True, slots=True)
class ShiftSummary:
    questions: int
    reviews: int
    dialogues: int
    returns: int
    urgent: int
    awaiting_human: int
    open_tasks: int
