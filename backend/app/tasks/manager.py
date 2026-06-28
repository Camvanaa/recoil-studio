from datetime import UTC, datetime

from .schemas import Task, TaskCreateRequest


class TaskManager:
    def __init__(self):
        self._tasks: dict[str, Task] = {}

    def create(self, request: TaskCreateRequest) -> Task:
        task = Task(type=request.type, payload=request.payload)
        self._tasks[task.id] = task
        return task

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def cancel(self, task_id: str) -> Task | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        if task.status in {"succeeded", "failed", "cancelled"}:
            return task
        task.status = "cancelled"
        task.message = "cancelled"
        task.updated_at = datetime.now(UTC)
        return task

    def list(self) -> list[Task]:
        return list(self._tasks.values())
