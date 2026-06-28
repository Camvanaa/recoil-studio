from fastapi import APIRouter, HTTPException

from app.tasks import Task, TaskCreateRequest, TaskManager

router = APIRouter()
tasks = TaskManager()


@router.post("", response_model=Task)
async def create_task(request: TaskCreateRequest):
    return tasks.create(request)


@router.get("", response_model=list[Task])
async def list_tasks():
    return tasks.list()


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.post("/{task_id}/cancel", response_model=Task)
async def cancel_task(task_id: str):
    task = tasks.cancel(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task
