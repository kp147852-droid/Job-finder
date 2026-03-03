from __future__ import annotations

from datetime import datetime
from threading import Thread
from uuid import uuid4

from .storage import AUTOMATION_TASKS


def enqueue(func, *args, **kwargs) -> str:
    task_id = str(uuid4())
    AUTOMATION_TASKS[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "result": None,
        "error": None,
    }

    def runner():
        AUTOMATION_TASKS[task_id]["status"] = "running"
        AUTOMATION_TASKS[task_id]["updated_at"] = datetime.utcnow().isoformat()
        try:
            result = func(*args, **kwargs)
            AUTOMATION_TASKS[task_id]["status"] = "completed"
            AUTOMATION_TASKS[task_id]["result"] = result
        except Exception as exc:  # pragma: no cover
            AUTOMATION_TASKS[task_id]["status"] = "failed"
            AUTOMATION_TASKS[task_id]["error"] = str(exc)
        finally:
            AUTOMATION_TASKS[task_id]["updated_at"] = datetime.utcnow().isoformat()

    thread = Thread(target=runner, daemon=True)
    thread.start()
    return task_id
