"""File management processes."""
import logging
import os
import shutil
import zipfile
from pathlib import Path

import yaml
from homeassistant.const import CONF_NAME
from voluptuous.error import Error as VoluptuousError

from ..const import (
    CONF_ACCOUNT_NAME,
    CONF_CAL_ID,
    CONF_CONFIG_TYPE,
    CONF_DEVICE_ID,
    CONF_ENTITIES,
    CONF_TASK_LIST_ID,
    CONF_TRACK,
    CONST_CONFIG_TYPE_LIST,
    DOMAIN,
    O365_STORAGE,
    TOKEN_FILENAME,
)
from ..schema import CALENDAR_DEVICE_SCHEMA, TASK_LIST_SCHEMA

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


def get_calendar_info(calendar, track_new_devices):
    """Convert data from O365 into DEVICE_SCHEMA."""
    return CALENDAR_DEVICE_SCHEMA(
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


def update_calendar_file(path, calendar, hass, track_new_devices):
    """Update the calendar file."""
    yaml_filepath = build_config_file_path(hass, path)
    existing_calendars = load_yaml_file(
        yaml_filepath, CONF_CAL_ID, CALENDAR_DEVICE_SCHEMA
    )
    cal = get_calendar_info(calendar, track_new_devices)
    if cal[CONF_CAL_ID] in existing_calendars:
        return
    with open(yaml_filepath, "a", encoding="UTF8") as out:
        out.write("\n")
        yaml.dump([cal], out, default_flow_style=False, encoding="UTF8")
        out.close()


def get_task_list_info(task_list, track_new_devices):
    """Convert data from O365 into DEVICE_SCHEMA."""
    return TASK_LIST_SCHEMA(
        {
            CONF_TASK_LIST_ID: task_list.folder_id,
            CONF_NAME: task_list.name,
            CONF_TRACK: track_new_devices,
        }
    )


def update_task_list_file(path, task_list, hass, track_new_devices):
    """Update the calendar file."""
    yaml_filepath = build_config_file_path(hass, path)
    existing_task_lists = load_yaml_file(
        yaml_filepath, CONF_TASK_LIST_ID, TASK_LIST_SCHEMA
    )
    task_list = get_task_list_info(task_list, track_new_devices)
    if task_list[CONF_TASK_LIST_ID] in existing_task_lists:
        return
    with open(yaml_filepath, "a", encoding="UTF8") as out:
        out.write("\n")
        yaml.dump([task_list], out, default_flow_style=False, encoding="UTF8")
        out.close()


def build_config_file_path(hass, filepath):
    """Create config path."""
    root = hass.config.config_dir

    return os.path.join(root, O365_STORAGE, filepath)


def build_token_filename(conf, conf_type):
    """Create the token file name."""
    config_file = (
        f"_{conf.get(CONF_ACCOUNT_NAME)}" if conf_type == CONST_CONFIG_TYPE_LIST else ""
    )
    return TOKEN_FILENAME.format(config_file)


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


def check_file_location(hass, filepath, newpath):
    """Check if file has been moved. If not move it. This function to be removed 2023/05/30."""
    root = hass.config.config_dir
    oldpath = os.path.join(
        root,
        filepath,
    )
    if os.path.exists(oldpath):
        shutil.move(oldpath, newpath)


def get_ha_filepath(hass, filepath):
    """Get the file path."""
    _filepath = Path(filepath)
    if _filepath.parts[0] == "/" and _filepath.parts[1] == "config":
        _filepath = os.path.join(hass.config.config_dir, *_filepath.parts[2:])

    if not os.path.isfile(_filepath):
        if not os.path.isfile(filepath):
            raise ValueError(f"Could not access file {filepath} at {_filepath}")
        return filepath
    return _filepath


def zip_files(filespaths, zip_name):
    """Zip the files."""
    if not zip_name:
        zip_name = "archive.zip"
    if Path(zip_name).suffix != ".zip":
        zip_name += ".zip"

    with zipfile.ZipFile(zip_name, mode="w") as zip_file:
        for file_path in filespaths:
            zip_file.write(file_path, os.path.basename(file_path))
    return zip_name
