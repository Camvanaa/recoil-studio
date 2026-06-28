from app.tasks import TaskCreateRequest, TaskManager


def test_task_manager_creates_and_cancels_tasks():
    manager = TaskManager()

    task = manager.create(TaskCreateRequest(type="pattern-detection", payload={"file": "sample.png"}))

    assert task.status == "queued"
    assert manager.get(task.id) == task

    cancelled = manager.cancel(task.id)
    assert cancelled is not None
    assert cancelled.status == "cancelled"
    assert cancelled.message == "cancelled"
