"""Todo processing."""

import logging
from datetime import datetime, timedelta

from homeassistant.components.todo import TodoItem, TodoListEntity
from homeassistant.components.todo.const import TodoItemStatus, TodoListEntityFeature
from homeassistant.const import CONF_ENABLED, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_platform
from homeassistant.util import dt as dt_util

from O365.utils.query import (  # pylint: disable=no-name-in-module, import-error
    QueryBuilder,
)

from .classes.entity import O365Entity
from .const import (
    ATTR_ALL_TODOS,
    ATTR_COMPLETED,
    ATTR_CREATED,
    ATTR_DATA,
    ATTR_DESCRIPTION,
    ATTR_DUE,
    ATTR_OVERDUE_TODOS,
    ATTR_REMINDER,
    ATTR_STATUS,
    ATTR_SUBJECT,
    ATTR_TODO_ID,
    CONF_ACCOUNT,
    CONF_ACCOUNT_NAME,
    CONF_COORDINATOR_SENSORS,
    CONF_DUE_HOURS_BACKWARD_TO_GET,
    CONF_DUE_HOURS_FORWARD_TO_GET,
    CONF_ENABLE_UPDATE,
    CONF_ENTITY_KEY,
    CONF_ENTITY_TYPE,
    CONF_IS_AUTHENTICATED,
    CONF_KEYS_SENSORS,
    CONF_O365_TASK_FOLDER,
    CONF_PERMISSIONS,
    CONF_SHOW_COMPLETED,
    CONF_TODO_SENSORS,
    CONF_TRACK_NEW,
    CONF_YAML_TASK_LIST,
    DATETIME_FORMAT,
    DOMAIN,
    EVENT_COMPLETED_TODO,
    EVENT_DELETE_TODO,
    EVENT_HA_EVENT,
    EVENT_NEW_TODO,
    EVENT_UNCOMPLETED_TODO,
    EVENT_UPDATE_TODO,
    PERM_TASKS_READWRITE,
    TODO_TODO,
)
from .schema import (
    TODO_SERVICE_COMPLETE_SCHEMA,
    TODO_SERVICE_DELETE_SCHEMA,
    TODO_SERVICE_NEW_SCHEMA,
    TODO_SERVICE_UPDATE_SCHEMA,
)
from .utils.filemgmt import async_update_task_list_file

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):  # pylint: disable=unused-argument
    """O365 platform definition."""
    if discovery_info is None:
        return None

    account_name = discovery_info[CONF_ACCOUNT_NAME]
    conf = hass.data[DOMAIN][account_name]

    is_authenticated = conf[CONF_IS_AUTHENTICATED]
    if not is_authenticated:
        return False

    coordinator = conf[CONF_COORDINATOR_SENSORS]
    todoentities = [
        O365TodoList(
            hass,
            coordinator,
            key[CONF_O365_TASK_FOLDER],
            key[CONF_NAME],
            key[CONF_YAML_TASK_LIST],
            conf,
            key[CONF_ENTITY_KEY],
            key[CONF_UNIQUE_ID],
        )
        for key in conf[CONF_KEYS_SENSORS]
        if key[CONF_ENTITY_TYPE] == TODO_TODO
    ]
    async_add_entities(todoentities, False)
    await _async_setup_register_services(hass, conf)

    _LOGGER.warning(
        "The O365 Todo sensors are now deprecated - please migrate to MS365 To Do "
        + "- for more details on how to do this see "
        + "https://rogerselwyn.github.io/O365-HomeAssistant/migration.html"
    )
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
        DOMAIN, "scan_for_todo_lists", sensor_services.async_scan_for_todo_lists
    )

    platform = entity_platform.async_get_current_platform()
    if perms.validate_authorization(PERM_TASKS_READWRITE):
        platform.async_register_entity_service(
            "new_todo",
            TODO_SERVICE_NEW_SCHEMA,
            "async_new_todo",
        )
        platform.async_register_entity_service(
            "update_todo",
            TODO_SERVICE_UPDATE_SCHEMA,
            "async_update_todo",
        )
        platform.async_register_entity_service(
            "delete_todo",
            TODO_SERVICE_DELETE_SCHEMA,
            "async_delete_todo",
        )
        platform.async_register_entity_service(
            "complete_todo",
            TODO_SERVICE_COMPLETE_SCHEMA,
            "async_complete_todo",
        )


class O365TodoList(O365Entity, TodoListEntity):  # pylint: disable=abstract-method
    """O365 ToDo processing."""

    def __init__(
        self,
        hass,
        coordinator,
        o365_task_folder,
        name,
        yaml_task_list,
        config,
        entity_id,
        unique_id,
    ):
        """Initialise the ToDo List."""
        super().__init__(coordinator, config, name, entity_id, TODO_TODO, unique_id)
        self.todolist = o365_task_folder
        self._show_completed = yaml_task_list.get(CONF_SHOW_COMPLETED)

        self.todo_last_created = dt_util.utcnow() - timedelta(minutes=5)
        self.todo_last_completed = dt_util.utcnow() - timedelta(minutes=5)
        self._zero_date = datetime(
            1, 1, 1, 0, 0, 0, tzinfo=dt_util.get_default_time_zone()
        )
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
        todos = self.coordinator.data[self.entity_key][ATTR_DATA]
        self._state = sum(not task.completed for task in todos)
        self._todo_items = []
        for todo in todos:
            completed = (
                TodoItemStatus.COMPLETED
                if todo.completed
                else TodoItemStatus.NEEDS_ACTION
            )
            self._todo_items.append(
                TodoItem(
                    uid=todo.task_id,
                    summary=todo.subject,
                    status=completed,
                    description=todo.body,
                    due=todo.due.date() if todo.due else None,
                )
            )

            self._extra_attributes = self._update_extra_state_attributes(todos)

        todo_last_completed = self._zero_date
        todo_last_created = self._zero_date
        for todo in todos:
            if todo.completed and todo.completed > self.todo_last_completed:
                _raise_event_external(
                    hass,
                    EVENT_COMPLETED_TODO,
                    todo.task_id,
                    ATTR_COMPLETED,
                    todo.completed,
                )
                if todo.completed > todo_last_completed:
                    todo_last_completed = todo.completed
            if todo.created and todo.created > self.todo_last_created:
                _raise_event_external(
                    hass, EVENT_NEW_TODO, todo.task_id, ATTR_CREATED, todo.created
                )
                if todo.created > todo_last_created:
                    todo_last_created = todo.created

        if todo_last_completed > self._zero_date:
            self.todo_last_completed = todo_last_completed
        if todo_last_created > self._zero_date:
            self.todo_last_created = todo_last_created

    def _update_extra_state_attributes(self, todos):
        """Extra state attributes."""
        all_todos = []
        overdue_todos = []
        for item in todos:
            todo = {
                ATTR_SUBJECT: item.subject,
                ATTR_TODO_ID: item.task_id,
                ATTR_STATUS: item.status,
            }
            if item.body:
                todo[ATTR_DESCRIPTION] = item.body
            if self._show_completed:
                todo[ATTR_COMPLETED] = (
                    item.completed.strftime(DATETIME_FORMAT)
                    if item.completed
                    else False
                )
            if item.due:
                due = item.due.date()
                todo[ATTR_DUE] = due
                if due < dt_util.utcnow().date():
                    overdue_todo = {
                        ATTR_SUBJECT: item.subject,
                        ATTR_TODO_ID: item.task_id,
                        ATTR_DUE: due,
                    }
                    if item.is_reminder_on:
                        overdue_todo[ATTR_REMINDER] = item.reminder
                    overdue_todos.append(overdue_todo)

            if item.is_reminder_on:
                todo[ATTR_REMINDER] = item.reminder

            all_todos.append(todo)

        extra_attributes = {ATTR_ALL_TODOS: all_todos}
        if overdue_todos:
            extra_attributes[ATTR_OVERDUE_TODOS] = overdue_todos
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

        new_o365_task = await self.hass.async_add_executor_job(self.todolist.new_task)
        await self._async_save_task(new_o365_task, subject, description, due, reminder)
        self._raise_event(EVENT_NEW_TODO, new_o365_task.task_id)
        self.todo_last_created = new_o365_task.created
        await self.coordinator.async_refresh()
        return True

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Add an item to the To-do list."""
        o365_task = await self.hass.async_add_executor_job(
            self.todolist.get_task, item.uid
        )
        if item.status:
            completed = None
            if item.status == TodoItemStatus.COMPLETED and not o365_task.completed:
                completed = True
            elif item.status == TodoItemStatus.NEEDS_ACTION and o365_task.completed:
                completed = False
            if completed is not None:
                await self.async_complete_todo(item.uid, completed, o365_task=o365_task)
                return

        if (
            item.summary != o365_task.subject
            or item.description != o365_task.body
            or (item.due and item.due != o365_task.due)
        ):
            await self.async_update_todo(
                todo_id=item.uid,
                subject=item.summary,
                description=item.description,
                due=item.due,
                o365_task=o365_task,
                hatodo=True,
            )

    async def async_update_todo(
        self,
        todo_id,
        subject=None,
        description=None,
        due=None,
        reminder=None,
        o365_task=None,
        hatodo=False,
    ):
        """Update a task for this task list."""
        if not self._validate_task_permissions():
            return False

        if not o365_task:
            o365_task = await self.hass.async_add_executor_job(
                self.todolist.get_task, todo_id
            )
        await self._async_save_task(
            o365_task, subject, description, due, reminder, hatodo
        )
        self._raise_event(EVENT_UPDATE_TODO, todo_id)
        await self.coordinator.async_refresh()
        return True

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        """Delete items from the To-do list."""
        for todo_id in uids:
            await self.async_delete_todo(todo_id)

    async def async_delete_todo(self, todo_id):
        """Delete task for this task list."""
        if not self._validate_task_permissions():
            return False

        o365_task = await self.hass.async_add_executor_job(
            self.todolist.get_task, todo_id
        )
        await self.hass.async_add_executor_job(o365_task.delete)
        self._raise_event(EVENT_DELETE_TODO, todo_id)
        await self.coordinator.async_refresh()
        return True

    async def async_complete_todo(self, todo_id, completed, o365_task=None):
        """Complete task for this task list."""
        if not self._validate_task_permissions():
            return False

        if not o365_task:
            o365_task = await self.hass.async_add_executor_job(
                self.todolist.get_task, todo_id
            )
        if completed:
            await self._async_complete_task(o365_task, todo_id)
        else:
            await self._async_uncomplete_task(o365_task, todo_id)

        await self.coordinator.async_refresh()
        return True

    async def _async_complete_task(self, o365_task, todo_id):
        if o365_task.completed:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="todo_completed",
            )
        await self.hass.async_add_executor_job(o365_task.mark_completed)
        await self.hass.async_add_executor_job(o365_task.save)
        self._raise_event(EVENT_COMPLETED_TODO, todo_id)
        self.todo_last_completed = dt_util.utcnow()

    async def _async_uncomplete_task(self, o365_task, todo_id):
        if not o365_task.completed:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="todo_not_completed",
            )
        await self.hass.async_add_executor_job(o365_task.mark_uncompleted)
        await self.hass.async_add_executor_job(o365_task.save)
        self._raise_event(EVENT_UNCOMPLETED_TODO, todo_id)

    async def _async_save_task(
        self, o365_task, subject, description, due, reminder, hatodo=False
    ):
        # sourcery skip: raise-from-previous-error
        if subject or hatodo:
            o365_task.subject = subject
        if description or hatodo:
            o365_task.body = description

        if due:
            if isinstance(due, str):
                try:
                    if len(due) > 10:
                        o365_task.due = dt_util.parse_datetime(due).date()
                    else:
                        o365_task.due = dt_util.parse_date(due)
                except ValueError:
                    raise ServiceValidationError(  # pylint: disable=raise-missing-from
                        translation_domain=DOMAIN,
                        translation_key="due_date_invalid",
                        translation_placeholders={
                            "due": due,
                        },
                    )
            else:
                o365_task.due = due

        if reminder:
            o365_task.reminder = reminder

        await self.hass.async_add_executor_job(o365_task.save)

    def _raise_event(self, event_type, todo_id):
        self.hass.bus.fire(
            f"{DOMAIN}_{event_type}",
            {ATTR_TODO_ID: todo_id, EVENT_HA_EVENT: True},
        )
        _LOGGER.debug("%s - %s", event_type, todo_id)

    def _validate_task_permissions(self):
        return self._validate_permissions(
            PERM_TASKS_READWRITE,
            f"Not authorised to create new ToDo - requires permission: {PERM_TASKS_READWRITE}",
        )


def _raise_event_external(hass, event_type, todo_id, time_type, task_datetime):
    hass.bus.fire(
        f"{DOMAIN}_{event_type}",
        {ATTR_TODO_ID: todo_id, time_type: task_datetime, EVENT_HA_EVENT: False},
    )
    _LOGGER.debug("%s - %s - %s", event_type, todo_id, task_datetime)


async def async_build_todo_query(builder: QueryBuilder, key):
    """Build query for ToDo."""
    o365_task = key[CONF_YAML_TASK_LIST]
    show_completed = o365_task[CONF_SHOW_COMPLETED]
    query = builder.select()
    if not show_completed:
        query = query & builder.unequal("status", "completed")
    start_offset = o365_task.get(CONF_DUE_HOURS_BACKWARD_TO_GET)
    end_offset = o365_task.get(CONF_DUE_HOURS_FORWARD_TO_GET)
    if start_offset:
        start = dt_util.utcnow() + timedelta(hours=start_offset)
        query = query & builder.greater_equal(
            "due", start.strftime("%Y-%m-%dT%H:%M:%S")
        )
    if end_offset:
        end = dt_util.utcnow() + timedelta(hours=end_offset)
        query = query & builder.less_equal("due", end.strftime("%Y-%m-%dT%H:%M:%S"))
    return query


class O365TodoEntityServices:
    """Sensor Services."""

    def __init__(self, hass):
        """Initialise the sensor services."""
        self._hass = hass

    async def async_scan_for_todo_lists(self, call):  # pylint: disable=unused-argument
        """Scan for new task lists."""
        for config in self._hass.data[DOMAIN]:
            config = self._hass.data[DOMAIN][config]
            todo_sensor = config.get(CONF_TODO_SENSORS)
            if todo_sensor and CONF_ACCOUNT in config and todo_sensor.get(CONF_ENABLED):
                todos = await self._hass.async_add_executor_job(
                    config[CONF_ACCOUNT].tasks
                )

                todolists = await self._hass.async_add_executor_job(todos.list_folders)
                track = todo_sensor.get(CONF_TRACK_NEW)
                for todo in todolists:
                    await async_update_task_list_file(
                        config,
                        todo,
                        self._hass,
                        track,
                    )
