"""O365 tasks sensors."""
import logging
from datetime import datetime, timedelta

import voluptuous as vol
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_ENABLED
from homeassistant.util import dt

from ..const import (
    ATTR_ALL_TASKS,
    ATTR_COMPLETED,
    ATTR_CREATED,
    ATTR_DESCRIPTION,
    ATTR_DUE,
    ATTR_OVERDUE_TASKS,
    ATTR_REMINDER,
    ATTR_SUBJECT,
    ATTR_TASK_ID,
    ATTR_TASKS,
    CONF_ACCOUNT,
    CONF_SHOW_COMPLETED,
    CONF_TODO_SENSORS,
    CONF_TRACK_NEW,
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
from ..utils.filemgmt import update_task_list_file
from .sensorentity import O365Sensor

_LOGGER = logging.getLogger(__name__)


class O365TasksSensor(O365Sensor, SensorEntity):
    """O365 Tasks sensor processing."""

    def __init__(self, coordinator, todo, name, task, config, entity_id, unique_id):
        """Initialise the Tasks Sensor."""
        super().__init__(coordinator, config, name, entity_id, SENSOR_TODO, unique_id)
        self.todo = todo
        self._show_completed = task.get(CONF_SHOW_COMPLETED)

        self.task_last_created = dt.utcnow() - timedelta(minutes=5)
        self.task_last_completed = dt.utcnow() - timedelta(minutes=5)
        self._zero_date = datetime(1, 1, 1, 0, 0, 0, tzinfo=dt.DEFAULT_TIME_ZONE)

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

    def _handle_coordinator_update(self) -> None:
        tasks = self.coordinator.data[self.entity_key][ATTR_TASKS]
        task_last_completed = self._zero_date
        task_last_created = self._zero_date
        for task in tasks:
            if task.completed and task.completed > self.task_last_completed:
                self._raise_event_external(
                    EVENT_COMPLETED_TASK,
                    task.task_id,
                    ATTR_COMPLETED,
                    task.completed,
                )
                if task.completed > task_last_completed:
                    task_last_completed = task.completed
            if task.created and task.created > self.task_last_created:
                self._raise_event_external(
                    EVENT_NEW_TASK, task.task_id, ATTR_CREATED, task.created
                )
                if task.created > task_last_created:
                    task_last_created = task.created

        if task_last_completed > self._zero_date:
            self.task_last_completed = task_last_completed
        if task_last_created > self._zero_date:
            self.task_last_created = task_last_created

        self.async_write_ha_state()

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

    def _raise_event_external(self, event_type, task_id, time_type, task_datetime):
        self.hass.bus.fire(
            f"{DOMAIN}_{event_type}",
            {ATTR_TASK_ID: task_id, time_type: task_datetime, EVENT_HA_EVENT: False},
        )
        _LOGGER.debug("%s - %s - %s", event_type, task_id, task_datetime)

    def _validate_task_permissions(self):
        return self._validate_permissions(
            PERM_MINIMUM_TASKS_WRITE,
            f"Not authorised to create new task - requires permission: {PERM_TASKS_READWRITE}",
        )


class O365TasksSensorSensorServices:
    """Sensor Services."""

    def __init__(self, hass):
        """Initialise the sensor services."""
        self._hass = hass

    async def async_scan_for_task_lists(self, call):  # pylint: disable=unused-argument
        """Scan for new task lists."""
        for config in self._hass.data[DOMAIN]:
            config = self._hass.data[DOMAIN][config]
            todo_sensor = config.get(CONF_TODO_SENSORS)
            if todo_sensor and CONF_ACCOUNT in config and todo_sensor.get(CONF_ENABLED):
                todos = config[CONF_ACCOUNT].tasks()

                todolists = await self._hass.async_add_executor_job(todos.list_folders)
                track = todo_sensor.get(CONF_TRACK_NEW)
                for todo in todolists:
                    update_task_list_file(
                        config,
                        todo,
                        self._hass,
                        track,
                    )
