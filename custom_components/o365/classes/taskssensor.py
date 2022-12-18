"""O365 tasks sensors."""
import voluptuous as vol
from homeassistant.components.sensor import SensorEntity
from homeassistant.util import dt

from ..const import (
    ATTR_ALL_TASKS,
    ATTR_DESCRIPTION,
    ATTR_DUE,
    ATTR_OVERDUE_TASKS,
    ATTR_REMINDER,
    ATTR_SUBJECT,
    ATTR_TASK_ID,
    ATTR_TASKS,
    CONF_CONFIG_TYPE,
    PERM_MINIMUM_TASKS_WRITE,
    PERM_TASKS_READWRITE,
    SENSOR_TODO,
)
from ..utils import build_token_filename, get_permissions, validate_minimum_permission
from .sensorentity import O365Sensor


class O365TasksSensor(O365Sensor, SensorEntity):
    """O365 Tasks sensor processing."""

    def __init__(self, coordinator, todo, name, entity_id, config, unqique_id):
        """Initialise the Tasks Sensor."""
        super().__init__(coordinator, name, entity_id, SENSOR_TODO, unqique_id)
        self.todo = todo
        self.query = self.todo.new_query("status").unequal("completed")
        self._config = config

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
        if not self._validate_permissions():
            return False

        new_task = self.todo.new_task()
        self._save_task(new_task, subject, description, due, reminder)
        return True

    def update_task(
        self, task_id, subject=None, description=None, due=None, reminder=None
    ):
        """Update a task for this task list."""
        if not self._validate_permissions():
            return False

        task = self.todo.get_task(task_id)
        self._save_task(task, subject, description, due, reminder)
        return True

    def delete_task(self, task_id):
        """Delete task for this task list."""
        if not self._validate_permissions():
            return False

        task = self.todo.get_task(task_id)
        task.delete()
        return True

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

    def _validate_permissions(self):
        permissions = get_permissions(
            self.hass,
            filename=build_token_filename(
                self._config, self._config.get(CONF_CONFIG_TYPE)
            ),
        )
        if not validate_minimum_permission(PERM_MINIMUM_TASKS_WRITE, permissions):
            raise vol.Invalid(
                f"Not authorisied to create new task - requires permission: {PERM_TASKS_READWRITE}"
            )

        return True
