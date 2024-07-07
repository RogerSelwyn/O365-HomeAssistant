"""File management processes."""

import logging
import os

import yaml
from homeassistant.const import CONF_NAME
from voluptuous.error import Error as VoluptuousError

from ..const import (
    CONF_ACCOUNT_NAME,
    CONF_CAL_ID,
    CONF_CONFIG_TYPE,
    CONF_DEVICE_ID,
    CONF_ENTITIES,
    CONF_TRACK,
    CONF_YAML_TASK_LIST_ID,
    CONST_CONFIG_TYPE_LIST,
    DOMAIN,
    O365_STORAGE,
    YAML_CALENDARS_FILENAME,
    YAML_TASK_LISTS_FILENAME,
)
from ..schema import YAML_CALENDAR_DEVICE_SCHEMA, YAML_TASK_LIST_SCHEMA

_LOGGER = logging.getLogger(__name__)


def load_yaml_file(path, item_id, item_schema):
    """Load the o365 yaml file."""
    items = {}
    try:
        with open(path, encoding="utf8") as file:
            data = yaml.safe_load(file)
            if data is None:
                return {}
            for item in data:
                try:
                    items[item[item_id]] = item_schema(item)
                except VoluptuousError as exception:
                    # keep going
                    _LOGGER.warning("Invalid Data: %s", exception)
    except FileNotFoundError:
        # When YAML file could not be loaded/did not contain a dict
        return {}

    return items


def _write_yaml_file(yaml_filepath, yaml_list):
    with open(yaml_filepath, "a", encoding="UTF8") as out:
        out.write("\n")
        yaml.dump([yaml_list], out, default_flow_style=False, encoding="UTF8")
        out.close()


def _get_calendar_info(calendar, track_new_devices):
    """Convert data from O365 into DEVICE_SCHEMA."""
    return YAML_CALENDAR_DEVICE_SCHEMA(
        {
            CONF_CAL_ID: calendar.calendar_id,
            CONF_ENTITIES: [
                {
                    CONF_TRACK: track_new_devices,
                    CONF_NAME: calendar.name,
                    CONF_DEVICE_ID: calendar.name,
                }
            ],
        }
    )


async def async_update_calendar_file(config, calendar, hass, track_new_devices):
    """Update the calendar file."""
    path = build_yaml_filename(config, YAML_CALENDARS_FILENAME)
    yaml_filepath = build_config_file_path(hass, path)
    existing_calendars = await hass.async_add_executor_job(
        load_yaml_file, yaml_filepath, CONF_CAL_ID, YAML_CALENDAR_DEVICE_SCHEMA
    )
    cal = _get_calendar_info(calendar, track_new_devices)
    if cal[CONF_CAL_ID] in existing_calendars:
        return
    await hass.async_add_executor_job(_write_yaml_file, yaml_filepath, cal)


def _get_task_list_info(yaml_task_list, track_new_devices):
    """Convert data from O365 into DEVICE_SCHEMA."""
    return YAML_TASK_LIST_SCHEMA(
        {
            CONF_YAML_TASK_LIST_ID: yaml_task_list.folder_id,
            CONF_NAME: yaml_task_list.name,
            CONF_TRACK: track_new_devices,
        }
    )


async def async_update_task_list_file(config, yaml_task_list, hass, track_new_devices):
    """Update the calendar file."""
    path = build_yaml_filename(config, YAML_TASK_LISTS_FILENAME)
    yaml_filepath = build_config_file_path(hass, path)
    existing_task_lists = await hass.async_add_executor_job(
        load_yaml_file, yaml_filepath, CONF_YAML_TASK_LIST_ID, YAML_TASK_LIST_SCHEMA
    )
    yaml_task_list = _get_task_list_info(yaml_task_list, track_new_devices)
    if yaml_task_list[CONF_YAML_TASK_LIST_ID] in existing_task_lists:
        return
    await hass.async_add_executor_job(_write_yaml_file, yaml_filepath, yaml_task_list)


def build_config_file_path(hass, filepath):
    """Create config path."""
    root = hass.config.config_dir

    return os.path.join(root, O365_STORAGE, filepath)


def build_yaml_filename(conf, filename, conf_type=None):
    """Create the token file name."""
    if conf_type:
        config_file = f"_{conf.get(CONF_ACCOUNT_NAME)}"
    else:
        config_file = (
            f"_{conf.get(CONF_ACCOUNT_NAME)}"
            if conf.get(CONF_CONFIG_TYPE) == CONST_CONFIG_TYPE_LIST
            else ""
        )
    return filename.format(DOMAIN, config_file)
