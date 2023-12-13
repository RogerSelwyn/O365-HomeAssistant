"""Todo processing."""

import logging
from datetime import datetime, timedelta

from homeassistant.components.todo import TodoItem, TodoListEntity
from homeassistant.components.todo.const import TodoItemStatus, TodoListEntityFeature
from homeassistant.const import CONF_ENABLED, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_platform
from homeassistant.util import dt

from .classes.entity import O365Entity
from .const import (
    ATTR_ALL_TASKS,
    ATTR_COMPLETED,
    ATTR_CREATED,
    ATTR_DATA,
    ATTR_DESCRIPTION,
    ATTR_DUE,
    ATTR_OVERDUE_TASKS,
    ATTR_REMINDER,
    ATTR_SUBJECT,
    ATTR_TASK_ID,
    CONF_ACCOUNT,
    CONF_ACCOUNT_NAME,
    CONF_COORDINATOR_SENSORS,
    CONF_DUE_HOURS_BACKWARD_TO_GET,
    CONF_DUE_HOURS_FORWARD_TO_GET,
    CONF_ENABLE_UPDATE,
    CONF_ENTITY_KEY,
    CONF_ENTITY_TYPE,
    CONF_KEYS_SENSORS,
    CONF_PERMISSIONS,
    CONF_SHOW_COMPLETED,
    CONF_TASK_LIST,
    CONF_TODO,
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
    TODO_TODO,
)
from .schema import (
    TASK_SERVICE_COMPLETE_SCHEMA,
    TASK_SERVICE_DELETE_SCHEMA,
    TASK_SERVICE_NEW_SCHEMA,
    TASK_SERVICE_UPDATE_SCHEMA,
)
from .utils.filemgmt import update_task_list_file

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):  # pylint: disable=unused-argument
    """O365 platform definition."""
    if discovery_info is None:
        return None

    account_name = discovery_info[CONF_ACCOUNT_NAME]
    conf = hass.data[DOMAIN][account_name]
    account = conf[CONF_ACCOUNT]

    is_authenticated = account.is_authenticated
    if not is_authenticated:
        return False

    coordinator = conf[CONF_COORDINATOR_SENSORS]
    todoentities = [
        O365TodoList(
            hass,
            coordinator,
            key[CONF_TODO],
            key[CONF_NAME],
            key[CONF_TASK_LIST],
            conf,
            key[CONF_ENTITY_KEY],
            key[CONF_UNIQUE_ID],
        )
        for key in conf[CONF_KEYS_SENSORS]
        if key[CONF_ENTITY_TYPE] == TODO_TODO
    ]
    async_add_entities(todoentities, False)
    await _async_setup_register_services(hass, conf)

    return True


async def _async_setup_register_services(hass, config):
    perms = config[CONF_PERMISSIONS]
    await _async_setup_task_services(hass, config, perms)


async def _async_setup_task_services(hass, config, perms):
    todo_sensors = config.get(CONF_TODO_SENSORS)
    if (
        not todo_sensors
        or not todo_sensors.get(CONF_ENABLED)
        or not todo_sensors.get(CONF_ENABLE_UPDATE)
    ):
        return

    sensor_services = O365TodoEntityServices(hass)
    hass.services.async_register(
        DOMAIN, "scan_for_todo_lists", sensor_services.async_scan_for_task_lists
    )

    platform = entity_platform.async_get_current_platform()
    if perms.validate_minimum_permission(PERM_MINIMUM_TASKS_WRITE):
        platform.async_register_entity_service(
            "new_todo",
            TASK_SERVICE_NEW_SCHEMA,
            "async_new_todo",
        )
        platform.async_register_entity_service(
            "update_todo",
            TASK_SERVICE_UPDATE_SCHEMA,
            "async_update_todo",
        )
        platform.async_register_entity_service(
            "delete_todo",
            TASK_SERVICE_DELETE_SCHEMA,
            "async_delete_todo",
        )
        platform.async_register_entity_service(
            "complete_todo",
            TASK_SERVICE_COMPLETE_SCHEMA,
            "async_complete_todo",
        )


class O365TodoList(O365Entity, TodoListEntity):
    """O365 ToDo processing."""

    def __init__(
        self, hass, coordinator, todolist, name, task, config, entity_id, unique_id
    ):
        """Initialise the ToDo List."""
        super().__init__(coordinator, config, name, entity_id, TODO_TODO, unique_id)
        self.todolist = todolist
        self._show_completed = task.get(CONF_SHOW_COMPLETED)

        self.task_last_created = dt.utcnow() - timedelta(minutes=5)
        self.task_last_completed = dt.utcnow() - timedelta(minutes=5)
        self._zero_date = datetime(1, 1, 1, 0, 0, 0, tzinfo=dt.DEFAULT_TIME_ZONE)
        self._state = None
        self._todo_items = None
        self._extra_attributes = None
        self._update_status(hass)
        if config.get(CONF_TODO_SENSORS).get(CONF_ENABLE_UPDATE):
            self._attr_supported_features = (
                TodoListEntityFeature.CREATE_TODO_ITEM
                | TodoListEntityFeature.UPDATE_TODO_ITEM
                | TodoListEntityFeature.DELETE_TODO_ITEM
                | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
                | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
            )

    @property
    def state(self):
        """Todo state."""
        return self._state

    @property
    def todo_items(self):
        """List of Todos."""
        return self._todo_items

    @property
    def extra_state_attributes(self):
        """Device state attributes."""
        return self._extra_attributes

    def _handle_coordinator_update(self) -> None:
        self._update_status(self.hass)
        self.async_write_ha_state()

    def _update_status(self, hass):
        tasks = self.coordinator.data[self.entity_key][ATTR_DATA]
        self._state = sum(not task.completed for task in tasks)
        self._todo_items = []
        for task in tasks:
            completed = (
                TodoItemStatus.COMPLETED
                if task.completed
                else TodoItemStatus.NEEDS_ACTION
            )
            self._todo_items.append(
                TodoItem(uid=task.task_id, summary=task.subject, status=completed)
            )

            self._extra_attributes = self._update_extra_state_attributes(tasks)

        task_last_completed = self._zero_date
        task_last_created = self._zero_date
        for task in tasks:
            if task.completed and task.completed > self.task_last_completed:
                _raise_event_external(
                    hass,
                    EVENT_COMPLETED_TASK,
                    task.task_id,
                    ATTR_COMPLETED,
                    task.completed,
                )
                if task.completed > task_last_completed:
                    task_last_completed = task.completed
            if task.created and task.created > self.task_last_created:
                _raise_event_external(
                    hass, EVENT_NEW_TASK, task.task_id, ATTR_CREATED, task.created
                )
                if task.created > task_last_created:
                    task_last_created = task.created

        if task_last_completed > self._zero_date:
            self.task_last_completed = task_last_completed
        if task_last_created > self._zero_date:
            self.task_last_created = task_last_created

    def _update_extra_state_attributes(self, tasks):
        """Extra state attributes."""
        all_tasks = []
        overdue_tasks = []
        for item in tasks:
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

    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Add an item to the To-do list."""
        await self.async_new_todo(
            subject=item.summary, description=item.description, due=item.due
        )

    async def async_new_todo(self, subject, description=None, due=None, reminder=None):
        """Create a new task for this task list."""
        if not self._validate_task_permissions():
            return False

        new_task = self.todolist.new_task()
        await self._async_save_task(new_task, subject, description, due, reminder)
        self._raise_event(EVENT_NEW_TASK, new_task.task_id)
        self.task_last_created = new_task.created
        await self.coordinator.async_refresh()
        return True

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Add an item to the To-do list."""
        task = await self.hass.async_add_executor_job(self.todolist.get_task, item.uid)
        if item.summary and item.summary != task.subject:
            await self.async_update_todo(
                task_id=item.uid, subject=item.summary, task=task
            )
        if item.status:
            completed = None
            if item.status == TodoItemStatus.COMPLETED and not task.completed:
                completed = True
            elif item.status == TodoItemStatus.NEEDS_ACTION and task.completed:
                completed = False
            if completed is not None:
                await self.async_complete_todo(item.uid, completed, task=task)

    async def async_update_todo(
        self,
        task_id,
        subject=None,
        description=None,
        due=None,
        reminder=None,
        task=None,
    ):
        """Update a task for this task list."""
        if not self._validate_task_permissions():
            return False

        if not task:
            task = await self.hass.async_add_executor_job(
                self.todolist.get_task, task_id
            )
        await self._async_save_task(task, subject, description, due, reminder)
        self._raise_event(EVENT_UPDATE_TASK, task_id)
        await self.coordinator.async_refresh()
        return True

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete items from the To-do list."""
        for task_id in uids:
            await self.async_delete_todo(task_id)

    async def async_delete_todo(self, task_id):
        """Delete task for this task list."""
        if not self._validate_task_permissions():
            return False

        task = await self.hass.async_add_executor_job(self.todolist.get_task, task_id)
        await self.hass.async_add_executor_job(task.delete)
        self._raise_event(EVENT_DELETE_TASK, task_id)
        await self.coordinator.async_refresh()
        return True

    async def async_complete_todo(self, task_id, completed, task=None):
        """Complete task for this task list."""
        if not self._validate_task_permissions():
            return False

        if not task:
            task = await self.hass.async_add_executor_job(
                self.todolist.get_task, task_id
            )
        if completed:
            await self._async_complete_task(task, task_id)
        else:
            await self._async_uncomplete_task(task, task_id)

        await self.coordinator.async_refresh()
        return True

    async def _async_complete_task(self, task, task_id):
        if task.completed:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="todo_completed",
            )
        task.mark_completed()
        self.hass.async_add_executor_job(task.save)
        self._raise_event(EVENT_COMPLETED_TASK, task_id)
        self.task_last_completed = dt.utcnow()

    async def _async_uncomplete_task(self, task, task_id):
        if not task.completed:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="todo_not_completed",
            )
        task.mark_uncompleted()
        self.hass.async_add_executor_job(task.save)
        self._raise_event(EVENT_UNCOMPLETED_TASK, task_id)

    async def _async_save_task(self, task, subject, description, due, reminder):
        # sourcery skip: raise-from-previous-error
        if subject:
            task.subject = subject
        if description:
            task.body = description

        if due:
            if isinstance(due, str):
                try:
                    if len(due) > 10:
                        task.due = dt.parse_datetime(due).date()
                    else:
                        task.due = dt.parse_date(due)
                except ValueError:
                    raise ServiceValidationError(  # pylint: disable=raise-missing-from
                        translation_domain=DOMAIN,
                        translation_key="due_date_invalid",
                        translation_placeholders={
                            "due": due,
                        },
                    )
            else:
                task.due = due

        if reminder:
            task.reminder = reminder

        await self.hass.async_add_executor_job(task.save)

    def _raise_event(self, event_type, task_id):
        self.hass.bus.fire(
            f"{DOMAIN}_{event_type}",
            {ATTR_TASK_ID: task_id, EVENT_HA_EVENT: True},
        )
        _LOGGER.debug("%s - %s", event_type, task_id)

    def _validate_task_permissions(self):
        return self._validate_permissions(
            PERM_MINIMUM_TASKS_WRITE,
            f"Not authorised to create new ToDo - requires permission: {PERM_TASKS_READWRITE}",
        )


def _raise_event_external(hass, event_type, task_id, time_type, task_datetime):
    hass.bus.fire(
        f"{DOMAIN}_{event_type}",
        {ATTR_TASK_ID: task_id, time_type: task_datetime, EVENT_HA_EVENT: False},
    )
    _LOGGER.debug("%s - %s - %s", event_type, task_id, task_datetime)


def build_todo_query(key, todo):
    """Build query for ToDo."""
    task = key[CONF_TASK_LIST]
    show_completed = task[CONF_SHOW_COMPLETED]
    query = todo.new_query()
    if not show_completed:
        query = query.on_attribute("status").unequal("completed")
    start_offset = task.get(CONF_DUE_HOURS_BACKWARD_TO_GET)
    end_offset = task.get(CONF_DUE_HOURS_FORWARD_TO_GET)
    if start_offset:
        start = dt.utcnow() + timedelta(hours=start_offset)
        query.chain("and").on_attribute("due").greater_equal(
            start.strftime("%Y-%m-%dT%H:%M:%S")
        )
    if end_offset:
        end = dt.utcnow() + timedelta(hours=end_offset)
        query.chain("and").on_attribute("due").less_equal(
            end.strftime("%Y-%m-%dT%H:%M:%S")
        )
    return query


class O365TodoEntityServices:
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
