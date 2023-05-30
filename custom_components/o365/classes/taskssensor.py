"""O365 tasks sensors."""
import logging
from datetime import timedelta

import voluptuous as vol
from homeassistant.components.sensor import SensorEntity
from homeassistant.util import dt

from ..const import (
    ATTR_ALL_TASKS,
    ATTR_COMPLETED,
    ATTR_DESCRIPTION,
    ATTR_DUE,
    ATTR_OVERDUE_TASKS,
    ATTR_REMINDER,
    ATTR_SUBJECT,
    ATTR_TASK_ID,
    ATTR_TASKS,
    CONF_DUE_HOURS_BACKWARD_TO_GET,
    CONF_DUE_HOURS_FORWARD_TO_GET,
    CONF_SHOW_COMPLETED,
    DATETIME_FORMAT,
    DOMAIN,
    EVENT_COMPLETED_TASK,
    EVENT_DELETE_TASK,
    EVENT_HA_EVENT,
    EVENT_NEW_TASK,
    EVENT_UNCOMPLETED_TASK,
    EVENT_UPDATE_TASK,
    PERM_MINIMUM_TASKS_WRITE,
    PERM_TASKS_READWRITE,
    SENSOR_TODO,
)
from .sensorentity import O365Sensor

_LOGGER = logging.getLogger(__name__)


class O365TasksSensor(O365Sensor, SensorEntity):
    """O365 Tasks sensor processing."""

    def __init__(self, coordinator, todo, name, task, config, entity_id, unique_id):
        """Initialise the Tasks Sensor."""
        super().__init__(coordinator, config, name, entity_id, SENSOR_TODO, unique_id)
        self.todo = todo
        self._show_completed = task.get(CONF_SHOW_COMPLETED)
        self.query = self.todo.new_query()
        if not self._show_completed:
            self.query = self.query.on_attribute("status").unequal("completed")
        self.start_offset = task.get(CONF_DUE_HOURS_BACKWARD_TO_GET)
        self.end_offset = task.get(CONF_DUE_HOURS_FORWARD_TO_GET)

        self.task_last_created = dt.utcnow() - timedelta(minutes=5)
        self.task_last_completed = dt.utcnow() - timedelta(minutes=5)

    @property
    def icon(self):
        """Entity icon."""
        return "mdi:clipboard-check-outline"

    @property
    def extra_state_attributes(self):
        """Extra state attributes."""
        all_tasks = []
        overdue_tasks = []
        for item in self.coordinator.data[self.entity_key][ATTR_TASKS]:
            task = {ATTR_SUBJECT: item.subject, ATTR_TASK_ID: item.task_id}
            if item.body:
                task[ATTR_DESCRIPTION] = item.body
            if self._show_completed:
                task[ATTR_COMPLETED] = (
                    item.completed.strftime(DATETIME_FORMAT)
                    if item.completed
                    else False
                )
            if item.due:
                due = item.due.date()
                task[ATTR_DUE] = due
                if due < dt.utcnow().date():
                    overdue_task = {
                        ATTR_SUBJECT: item.subject,
                        ATTR_TASK_ID: item.task_id,
                        ATTR_DUE: due,
                    }
                    if item.is_reminder_on:
                        overdue_task[ATTR_REMINDER] = item.reminder
                    overdue_tasks.append(overdue_task)

            if item.is_reminder_on:
                task[ATTR_REMINDER] = item.reminder

            all_tasks.append(task)

        extra_attributes = {ATTR_ALL_TASKS: all_tasks}
        if overdue_tasks:
            extra_attributes[ATTR_OVERDUE_TASKS] = overdue_tasks
        return extra_attributes

    def new_task(self, subject, description=None, due=None, reminder=None):
        """Create a new task for this task list."""
        if not self._validate_task_permissions():
            return False

        new_task = self.todo.new_task()
        self._save_task(new_task, subject, description, due, reminder)
        self._raise_event(EVENT_NEW_TASK, new_task.task_id)
        self.task_last_created = new_task.created
        return True

    def update_task(
        self, task_id, subject=None, description=None, due=None, reminder=None
    ):
        """Update a task for this task list."""
        if not self._validate_task_permissions():
            return False

        task = self.todo.get_task(task_id)
        self._save_task(task, subject, description, due, reminder)
        self._raise_event(EVENT_UPDATE_TASK, task_id)
        return True

    def delete_task(self, task_id):
        """Delete task for this task list."""
        if not self._validate_task_permissions():
            return False

        task = self.todo.get_task(task_id)
        task.delete()
        self._raise_event(EVENT_DELETE_TASK, task_id)
        return True

    def complete_task(self, task_id, completed):
        """Complete task for this task list."""
        if not self._validate_task_permissions():
            return False

        task = self.todo.get_task(task_id)
        if completed:
            self._complete_task(task, task_id)
        else:
            self._uncomplete_task(task, task_id)

        return True

    def _complete_task(self, task, task_id):
        if task.completed:
            raise vol.Invalid("Task is already completed")
        task.mark_completed()
        task.save()
        self._raise_event(EVENT_COMPLETED_TASK, task_id)
        task = self.todo.get_task(task_id)
        self.task_last_completed = task.completed

    def _uncomplete_task(self, task, task_id):
        if not task.completed:
            raise vol.Invalid("Task has not been completed previously")
        task.mark_uncompleted()
        task.save()
        self._raise_event(EVENT_UNCOMPLETED_TASK, task_id)

    def _save_task(self, task, subject, description, due, reminder):
        # sourcery skip: raise-from-previous-error
        if subject:
            task.subject = subject
        if description:
            task.body = description
        if due:
            try:
                if len(due) > 10:
                    task.due = dt.parse_datetime(due).date()
                else:
                    task.due = dt.parse_date(due)
            except ValueError:
                error = f"Due date {due} is not in valid format YYYY-MM-DD"
                raise vol.Invalid(error)  # pylint: disable=raise-missing-from

        if reminder:
            task.reminder = reminder

        task.save()

    def _raise_event(self, event_type, task_id):
        self.hass.bus.fire(
            f"{DOMAIN}_{event_type}",
            {ATTR_TASK_ID: task_id, EVENT_HA_EVENT: True},
        )
        _LOGGER.debug("%s - %s", event_type, task_id)

    def _validate_task_permissions(self):
        return self._validate_permissions(
            PERM_MINIMUM_TASKS_WRITE,
            f"Not authorised to create new task - requires permission: {PERM_TASKS_READWRITE}",
        )
