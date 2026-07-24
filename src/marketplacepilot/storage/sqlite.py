from __future__ import annotations

import json
from asyncio import to_thread
from collections.abc import Iterable
from pathlib import Path

import aiosqlite

from marketplacepilot.models import Priority, Product, Task, TaskKind, TaskStatus


class TaskNotFoundError(LookupError):
    pass


class SqliteRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    async def initialize(self) -> None:
        await to_thread(self._database_path.parent.mkdir, parents=True, exist_ok=True)
        async with aiosqlite.connect(self._database_path) as connection:
            await connection.executescript(
                """
                PRAGMA foreign_keys = ON;
                CREATE TABLE IF NOT EXISTS demo_sessions (
                    user_id INTEGER PRIMARY KEY,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    user_id INTEGER NOT NULL,
                    id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    product_category TEXT NOT NULL,
                    product_facts TEXT NOT NULL,
                    buyer_label TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    message TEXT NOT NULL,
                    history_json TEXT NOT NULL,
                    scenario TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    priority_reason TEXT NOT NULL,
                    draft TEXT NOT NULL,
                    proposed_action TEXT NOT NULL,
                    risks_json TEXT NOT NULL,
                    needs_human INTEGER NOT NULL,
                    requires_confirmation INTEGER NOT NULL,
                    return_confirmed INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, id),
                    FOREIGN KEY (user_id) REFERENCES demo_sessions(user_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS confirmed_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    task_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id, task_id) REFERENCES tasks(user_id, id) ON DELETE CASCADE
                );
                """
            )
            await connection.commit()

    async def ensure_session(self, user_id: int, tasks: Iterable[Task]) -> bool:
        async with aiosqlite.connect(self._database_path) as connection:
            await connection.execute("PRAGMA foreign_keys = ON")
            cursor = await connection.execute("INSERT OR IGNORE INTO demo_sessions (user_id) VALUES (?)", (user_id,))
            created = cursor.rowcount == 1
            if created:
                await self._insert_tasks(connection, user_id, tasks)
            await connection.commit()
        return created

    async def reset_session(self, user_id: int, tasks: Iterable[Task]) -> None:
        async with aiosqlite.connect(self._database_path) as connection:
            await connection.execute("PRAGMA foreign_keys = ON")
            await connection.execute("INSERT OR IGNORE INTO demo_sessions (user_id) VALUES (?)", (user_id,))
            await connection.execute("DELETE FROM confirmed_actions WHERE user_id = ?", (user_id,))
            await connection.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
            await self._insert_tasks(connection, user_id, tasks)
            await connection.commit()

    async def list_tasks(self, user_id: int, include_completed: bool = True) -> list[Task]:
        query = "SELECT * FROM tasks WHERE user_id = ?"
        parameters: tuple[object, ...] = (user_id,)
        if not include_completed:
            query += " AND status != ?"
            parameters += (TaskStatus.COMPLETED.value,)
        query += " ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'normal' THEN 3 ELSE 4 END, id"
        async with aiosqlite.connect(self._database_path) as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute(query, parameters)
            rows = await cursor.fetchall()
        return [self._row_to_task(row) for row in rows]

    async def get_task(self, user_id: int, task_id: str) -> Task:
        async with aiosqlite.connect(self._database_path) as connection:
            connection.row_factory = aiosqlite.Row
            cursor = await connection.execute("SELECT * FROM tasks WHERE user_id = ? AND id = ?", (user_id, task_id))
            row = await cursor.fetchone()
        if row is None:
            raise TaskNotFoundError(task_id)
        return self._row_to_task(row)

    async def update_draft(self, user_id: int, task_id: str, draft: str) -> None:
        await self._update_task(user_id, task_id, "draft = ?, updated_at = CURRENT_TIMESTAMP", (draft,))

    async def apply_action(
        self,
        user_id: int,
        task_id: str,
        status: TaskStatus,
        action_type: str,
        details: str,
        *,
        return_confirmed: bool = False,
    ) -> None:
        async with aiosqlite.connect(self._database_path) as connection:
            cursor = await connection.execute(
                "UPDATE tasks SET status = ?, return_confirmed = ?, updated_at = CURRENT_TIMESTAMP "
                "WHERE user_id = ? AND id = ?",
                (status.value, int(return_confirmed), user_id, task_id),
            )
            if cursor.rowcount != 1:
                raise TaskNotFoundError(task_id)
            await connection.execute(
                "INSERT INTO confirmed_actions (user_id, task_id, action_type, details) VALUES (?, ?, ?, ?)",
                (user_id, task_id, action_type, details),
            )
            await connection.commit()

    async def action_count(self, user_id: int) -> int:
        async with aiosqlite.connect(self._database_path) as connection:
            cursor = await connection.execute("SELECT COUNT(*) FROM confirmed_actions WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
        return int(row[0])

    async def _update_task(self, user_id: int, task_id: str, assignments: str, values: tuple[object, ...]) -> None:
        async with aiosqlite.connect(self._database_path) as connection:
            cursor = await connection.execute(
                f"UPDATE tasks SET {assignments} WHERE user_id = ? AND id = ?",
                (*values, user_id, task_id),
            )
            if cursor.rowcount != 1:
                raise TaskNotFoundError(task_id)
            await connection.commit()

    @staticmethod
    async def _insert_tasks(connection: aiosqlite.Connection, user_id: int, tasks: Iterable[Task]) -> None:
        rows = [
            (
                user_id,
                task.id,
                task.kind.value,
                task.status.value,
                task.product.id,
                task.product.name,
                task.product.category,
                task.product.facts,
                task.buyer_label,
                task.subject,
                task.message,
                json.dumps(task.history, ensure_ascii=False),
                task.scenario,
                task.priority.value,
                task.priority_reason,
                task.draft,
                task.proposed_action,
                json.dumps(task.risks, ensure_ascii=False),
                int(task.needs_human),
                int(task.requires_confirmation),
                int(task.return_confirmed),
            )
            for task in tasks
        ]
        await connection.executemany(
            """
            INSERT INTO tasks (
                user_id, id, kind, status, product_id, product_name, product_category, product_facts,
                buyer_label, subject, message, history_json, scenario, priority, priority_reason, draft,
                proposed_action, risks_json, needs_human,
                requires_confirmation, return_confirmed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

    @staticmethod
    def _row_to_task(row: aiosqlite.Row) -> Task:
        return Task(
            id=row["id"],
            kind=TaskKind(row["kind"]),
            status=TaskStatus(row["status"]),
            product=Product(row["product_id"], row["product_name"], row["product_category"], row["product_facts"]),
            buyer_label=row["buyer_label"],
            subject=row["subject"],
            message=row["message"],
            history=_json_text_tuple(row["history_json"]),
            scenario=row["scenario"],
            priority=Priority(row["priority"]),
            priority_reason=row["priority_reason"],
            draft=row["draft"],
            proposed_action=row["proposed_action"],
            risks=_json_text_tuple(row["risks_json"]),
            needs_human=bool(row["needs_human"]),
            requires_confirmation=bool(row["requires_confirmation"]),
            return_confirmed=bool(row["return_confirmed"]),
        )


def _json_text_tuple(raw_value: str) -> tuple[str, ...]:
    """Accept data from current lists and legacy sessions that stored one text value."""
    value = json.loads(raw_value)
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)
