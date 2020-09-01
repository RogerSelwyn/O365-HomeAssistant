import logging
from datetime import datetime
from operator import itemgetter
from homeassistant.helpers.entity import Entity
from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_MAIL_FOLDER,
    CONF_MAX_ITEMS,
    CONF_HAS_ATTACHMENT,
    CONF_SUBJECT_CONTAINS,
    CONF_SUBJECT_IS,
    CONF_MAIL_FROM,
    CONF_IS_UNREAD,
    CONF_EMAIL_SENSORS,
    CONF_QUERY_SENSORS,
)
from .utils import get_email_attributes

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):
    if discovery_info is None:
        return

    account = hass.data[DOMAIN]["account"]
    is_authenticated = account.is_authenticated
    if not is_authenticated:
        return False

    unread_sensors = hass.data[DOMAIN].get(CONF_EMAIL_SENSORS, [])
    for conf in unread_sensors:
        sensor = O365InboxSensor(account, conf)
        add_devices([sensor], True)

    query_sensors = hass.data[DOMAIN].get(CONF_QUERY_SENSORS, [])
    for conf in query_sensors:
        sensor = O365QuerySensor(account, conf)
        add_devices([sensor], True)


class O365QuerySensor(Entity):
    def __init__(self, account, conf):
        self.account = account
        self.mailbox = account.mailbox()
        self.mail_folder = None
        self.query = None
        mail_folder = conf.get(CONF_MAIL_FOLDER)
        if mail_folder:
            for i, folder in enumerate(mail_folder.split("/")):
                if i == 0:
                    self.mail_folder = self.mailbox.get_folder(folder_name=folder)
                else:
                    self.mail_folder = self.mail_folder.get_folder(folder_name=folder)

        else:
            self.mail_folder = self.mailbox.inbox_folder()

        self._name = conf.get(
            CONF_NAME, f"{self.account.get_current_user().mail}-{self.mail_folder}"
        )

        self.max_items = conf.get(CONF_MAX_ITEMS, 5)
        self.subject_contains = conf.get(CONF_SUBJECT_CONTAINS)
        self.subject_is = conf.get(CONF_SUBJECT_IS)
        self.has_attachment = conf.get(CONF_HAS_ATTACHMENT)
        self.email_from = conf.get(CONF_MAIL_FROM)
        self.is_unread = conf.get(CONF_IS_UNREAD)

        if self.subject_contains is not None:
            if not self.query:
                self.query = self.mail_folder.new_query()
            else:
                self.query.chain("and")
            self.query.on_attribute("subject").contains(self.subject_contains)

        if self.subject_is is not None:
            if not self.query:
                self.query = self.mail_folder.new_query()
            else:
                self.query.chain("and")
            self.query.on_attribute("subject").equals(self.subject_is)

        if self.has_attachment is not None:
            if not self.query:
                self.query = self.mail_folder.new_query()
            else:
                self.query.chain("and")
            self.query.on_attribute("hasAttachments").equals(self.has_attachment)

        if self.email_from is not None:
            if not self.query:
                self.query = self.mail_folder.new_query()
            else:
                self.query.chain("and")
            self.query.on_attribute("from").equals(self.email_from)

        if self.is_unread is not None:
            if not self.query:
                self.query = self.mail_folder.new_query()
            else:
                self.query.chain("and")
            self.query.on_attribute("IsRead").equals(not self.is_unread)
        self.query.order_by("receivedDateTime", ascending=False)
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def device_state_attributes(self):
        return self._attributes

    def update(self):
        mails = list(
            self.mail_folder.get_messages(
                limit=self.max_items, query=self.query, download_attachments=True
            )
        )
        attrs = [get_email_attributes(x) for x in mails]
        attrs.sort(key=itemgetter("received"), reverse=True)
        self._state = len(mails)
        # self._attributes = {"data": attrs, "data_str_repr": json.dumps(attrs)}
        self._attributes = {"data": attrs}


class O365InboxSensor(Entity):
    def __init__(self, account, conf):
        self.account = account
        self.mailbox = account.mailbox()
        mail_folder = conf.get(CONF_MAIL_FOLDER)
        self.max_items = conf.get(CONF_MAX_ITEMS, 5)
        self.is_unread = conf.get(CONF_IS_UNREAD)
        if mail_folder:
            for i, folder in enumerate(mail_folder.split("/")):
                if i == 0:
                    self.mail_folder = self.mailbox.get_folder(folder_name=folder)
                else:
                    self.mail_folder = self.mail_folder.get_folder(folder_name=folder)
        else:
            self.mail_folder = self.mailbox.inbox_folder()

        self._name = conf.get(
            CONF_NAME, f"{self.account.get_current_user().mail}-{self.mail_folder}"
        )
        self._state = 0
        self._attributes = {}
        self.query = None
        if self.is_unread is not None:
            if not self.query:
                self.query = self.mail_folder.new_query()
            else:
                self.query.chain("and")
            self.query.on_attribute("IsRead").equals(not self.is_unread)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def device_state_attributes(self):
        return self._attributes

    def update(self):
        mails = list(
            self.mail_folder.get_messages(
                limit=self.max_items, query=self.query, download_attachments=True
            )
        )
        attrs = [get_email_attributes(x) for x in mails]
        attrs.sort(key=itemgetter("received"), reverse=True)
        self._state = len(mails)
        # self._attributes = {"data": attrs, "data_str_repr": json.dumps(attrs)}
        self._attributes = {"data": attrs}
