from sqlalchemy import and_
from ckan.model import task_status_table
from ..helpers import get_action_data
import logging
from domain.task_status import DomainTaskStatus

log = logging.getLogger(__name__)


# Task Handling (see also `put_on_a_queue` method):
# DEV-3293 required feedback from the workers for which the TaskStatus model is being used and the corresponding
# `task_status_show` and `task_status_update` API actions. General idea is to have for each package/plugin and
# resource/plugin combination a TaskStatus which contains information about the current task being pending or
# executed (so no trail).

# Create a TaskStatus when none exist yet with the default value properties `job_id` and `job_command`
def create_task(context, job, task_type, entity_type, res_dict, pkg_dict):
    task = DomainTaskStatus(
        entity_id=res_dict.get("id") if entity_type == 'resource' else pkg_dict.get("id"),
        entity_type=entity_type,
        task_type=task_type,
        key=job.id, action=job.func_name
    )
    created_task_dict = get_action_data("task_status_update", context, task.to_dict())
    return DomainTaskStatus.from_dict(created_task_dict)


# Update a TaskStatus identified by task_id with a state (required), value properties and error message (optional).
# The value is a JSON stored as a string, which why the json module is involved in updating that field
def update_task(context, task, state, remote_id=None, error=None):
    result = None
    if task is not None:
        task.set_state(state, remote_id, error)
        task_dict = get_action_data("task_status_update", context, task.to_dict())
        result = DomainTaskStatus.from_dict(task_dict)
    return result


def show_task(context, task_id):
    task_dict = get_action_data("task_status_show", context, {"id": task_id})
    return DomainTaskStatus.from_dict(task_dict)


def purge_task_statuses(connection, entity_id, entity_type, task_type):
    log.info("purge_task_status :: entity_id = [{}] entity_type = [{}] task_type = [{}]".format(
        entity_id, entity_type, task_type))

    # with connection.begin() as transaction:

    connection.execute(
        task_status_table.delete().where(
            and_(
                task_status_table.c.entity_id == entity_id,
                task_status_table.c.entity_type == entity_type,
                task_status_table.c.task_type == task_type
            )
        )
    )

    # log.info("purge_task_status :: delete = [{}]".format(delete))
    #
    # ex = connection.execute(delete)
    #
    # log.info("purge_task_status :: connection.execute = [{}]".format(ex))
    #
    #     # transaction.commit()
    #
    #
    # # task_statuses = model.Session.query(model.TaskStatus).\
    # #     filter(model.TaskStatus.entity_id == entity_id).\
    # #     filter(model.TaskStatus.entity_type == entity_type). \
    # #     filter(model.TaskStatus.task_type == self.name). \
    # #     all()
    # #
    # # log.info(task_statuses)
    # #
    # # if task_statuses:
    # #     for task_status in task_statuses:
    # #         log.info("connection.execute(task_status.delete()) for [{}]".format(task_status))
    # #         connection.execute(task_status.delete())
