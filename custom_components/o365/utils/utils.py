"""Utilities processes."""

import logging

from bs4 import BeautifulSoup

from ..const import (
    CONF_ACCOUNT,
    CONF_ACCOUNT_NAME,
    CONF_AUTO_REPLY_SENSORS,
    CONF_CHAT_SENSORS,
    CONF_CLIENT_ID,
    CONF_CONFIG_TYPE,
    CONF_EMAIL_SENSORS,
    CONF_ENABLE_CALENDAR,
    CONF_ENABLE_UPDATE,
    CONF_IS_AUTHENTICATED,
    CONF_PERMISSIONS,
    CONF_QUERY_SENSORS,
    CONF_STATUS_SENSORS,
    CONF_TODO_SENSORS,
    CONF_TRACK_NEW_CALENDAR,
    DATETIME_FORMAT,
)

_LOGGER = logging.getLogger(__name__)


def clean_html(html):
    """Clean the HTML."""
    soup = BeautifulSoup(html, features="html.parser")
    if body := soup.find("body"):
        # get text
        text = body.get_text()

        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = "\n".join(chunk for chunk in chunks if chunk)
        return text.replace("\xa0", " ")

    return html


def _safe_html(html):
    """Make the HTML safe."""
    soup = BeautifulSoup(html, features="html.parser")
    if soup.find("body"):
        blacklist = ["script", "style"]
        for tag in soup.findAll():
            if tag.name.lower() in blacklist:
                # blacklisted tags are removed in their entirety
                tag.extract()
        return str(soup.find("body"))
    return html


def get_email_attributes(mail, download_attachments, html_body, show_body):
    """Get the email attributes."""
    data = {
        "subject": mail.subject,
        "received": mail.received.strftime(DATETIME_FORMAT),
        "to": [x.address for x in mail.to],
        "cc": [x.address for x in mail.cc],
        "sender": mail.sender.address,
        "has_attachments": mail.has_attachments,
        "importance": mail.importance.value,
        "is_read": mail.is_read,
        "flag": {
            "is_flagged": mail.flag.is_flagged,
            "is_completed": mail.flag.is_completed,
            "due_date": mail.flag.due_date,
            "completion_date": mail.flag.completition_date,
        },
    }

    if show_body or html_body:
        data["body"] = _safe_html(mail.body) if html_body else clean_html(mail.body)
    if download_attachments:
        data["attachments"] = [x.name for x in mail.attachments]

    return data


def build_account_config(config, account, is_authenticated, conf_type, perms):
    """Build the account config."""
    email_sensors = config.get(CONF_EMAIL_SENSORS, [])
    query_sensors = config.get(CONF_QUERY_SENSORS, [])
    status_sensors = config.get(CONF_STATUS_SENSORS, [])
    chat_sensors = config.get(CONF_CHAT_SENSORS, [])
    todo_sensors = config.get(CONF_TODO_SENSORS, [])
    auto_reply_sensors = config.get(CONF_AUTO_REPLY_SENSORS, [])
    enable_update = config.get(CONF_ENABLE_UPDATE, False)
    enable_calendar = config.get(CONF_ENABLE_CALENDAR, True)

    return {
        CONF_CLIENT_ID: config.get(CONF_CLIENT_ID),
        CONF_ACCOUNT: account,
        CONF_IS_AUTHENTICATED: is_authenticated,
        CONF_EMAIL_SENSORS: email_sensors,
        CONF_QUERY_SENSORS: query_sensors,
        CONF_STATUS_SENSORS: status_sensors,
        CONF_CHAT_SENSORS: chat_sensors,
        CONF_TODO_SENSORS: todo_sensors,
        CONF_AUTO_REPLY_SENSORS: auto_reply_sensors,
        CONF_ENABLE_UPDATE: enable_update,
        CONF_ENABLE_CALENDAR: enable_calendar,
        CONF_TRACK_NEW_CALENDAR: config.get(CONF_TRACK_NEW_CALENDAR, True),
        CONF_ACCOUNT_NAME: config.get(CONF_ACCOUNT_NAME, ""),
        CONF_CONFIG_TYPE: conf_type,
        CONF_PERMISSIONS: perms,
    }
