import typing
from importlib import import_module

from celery.contrib.django.task import DjangoTask
from django.db import connection

if typing.TYPE_CHECKING:
    from celery.result import AsyncResult


class TaskQueuingException(Exception):
    """
    Exception raised while queuing a task
    """

    pass


def import_task(task_path: str) -> DjangoTask:
    """
    Import a task based on task_name passed. Task naming convention:

    >>> "apps.crm.tasks.sync_customer_data"

    Args:
        task_path (str): Fully Qualified python path to the task.
    Returns:
        Imported task
    """
    try:
        path, task_name = task_path.rsplit(".", 1)
        task = import_module(path).__getattribute__(task_name)
    except Exception as e:
        raise ImportError("Error Getting Celery Task instance") from e

    return task


def queue_task(
    task: typing.Union[str, "DjangoTask"],
    on_commit: bool = True,
    ignore_result: bool = True,
    idempotency_key: str = None,
    task_args=None,
    task_kwargs=None,
    *args,
    **kwargs,
) -> typing.Optional["AsyncResult"]:
    """
    A wrapper over celery's `task.delay`/`task.apply_async` to standardize task queuing.
    This wrapper make's it easier to modify task queuing behaviour

    Args:
        task (str, DjangoTask): Task name as a strigified path to task, or the task function itself
        on_commit (bool): Whether to queue task after current db-transaction commit or not.
            defaults to True.
        ignore_result (bool): Whether to save the results of django tasks to result backend or not.
            default to False.
        task_args (tuple, optional): Set of argument's to be passed to the task directly.
            Defaults to None.
        task_kwargs (dict, optional): Set of keyword arguments to be passed to the task directly.
            Defaults to None.
        idempotency_key (str): Some string, to ensure idempotency (i.e. one task run's only once even if queued multiple times).
            default's to None
            NOTE: Ensure the string generated passed remains constant as this will trigger celery retries.

    Kwargs:
        queue_name (str, optional): Task queue name, in which the task is to be pushed.
            default's to None

    Returns:
        (AsyncResult, None): Instance of celery's AsyncResult
            NOTE: Before using AsyncResult always check if result is available i.e. `AsyncResult.ready()`
    """
    task_args = task_args or tuple()
    task_kwargs = task_kwargs or {}

    if isinstance(task, str):
        task = import_task(task)

    if not isinstance(task, DjangoTask):
        raise TaskQueuingException("Invalid argument type for task!")

    task: DjangoTask

    kwargs["ignore_result"] = ignore_result
    if idempotency_key:
        kwargs["task_id"] = (
            f"{connection.schema_name}:{task.__name__}-{idempotency_key}"
        )

    if on_commit:
        task.apply_async_on_commit(args=task_args, kwargs=task_kwargs, *args, **kwargs)
    else:
        return task.apply_async(args=task_args, kwargs=task_kwargs, *args, **kwargs)

    return None
