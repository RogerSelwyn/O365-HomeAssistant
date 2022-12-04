"""Main mailbox processing."""

from homeassistant.core import HomeAssistant

import voluptuous as vol
from .const import (
    CONF_ACCOUNT,
    CONF_ACCOUNT_NAME,
    CONF_CONFIG_TYPE,
    DOMAIN,
    PERM_MAILBOX_SETTINGS,
    PERM_MINIMUM_MAILBOX,
)

from .utils import (
    build_token_filename,
    get_permissions,
    validate_minimum_permission,
)

from .schema import (
    ATTR_ACCOUNT,
    ATTR_INTERNALREPLY,
    ATTR_EXTERNALREPLY,
    ATTR_START,
    ATTR_END,
    ATTR_TIMEZONE,
)


async def async_setup_mailbox(
    hass: HomeAssistant, discovery_info=None
):  # pylint: disable=unused-argument
    """Set up the O365 mailbox."""
    if discovery_info is None:
        return None

    account_name = discovery_info[CONF_ACCOUNT_NAME]
    conf = hass.data[DOMAIN][account_name]
    account = conf[CONF_ACCOUNT]
    if not account.is_authenticated:
        return False

    def _validate_permissions(error_message, config):
        permissions = get_permissions(
            hass,
            filename=build_token_filename(config, config.get(CONF_CONFIG_TYPE)),
        )
        if not validate_minimum_permission(PERM_MINIMUM_MAILBOX, permissions):
            raise vol.Invalid(
                f"Not authorisied to {PERM_MAILBOX_SETTINGS} calendar event "
                + f"- requires permission: {error_message}"
            )
        return True

    def set_auto_reply(call):
        """Schedule the auto reply."""
        account_name = call.data.get(ATTR_ACCOUNT)
        if account_name not in hass.data[DOMAIN]:
            return
        conf = hass.data[DOMAIN][account_name]
        account = conf[CONF_ACCOUNT]
        if not _validate_permissions("MailboxSettings.ReadWrite", conf):
            return
        internalReply = call.data.get(ATTR_INTERNALREPLY)
        externalReply = call.data.get(ATTR_EXTERNALREPLY)
        start = call.data.get(ATTR_START)
        end = call.data.get(ATTR_END)
        timezone = call.data.get(ATTR_TIMEZONE)
        mailbox = account.mailbox()
        mailbox.set_automatic_reply(internalReply, externalReply, start, end, timezone)

    def disable_auto_reply(call):
        """Schedule the auto reply."""
        account_name = call.data.get(ATTR_ACCOUNT)
        if account_name not in hass.data[DOMAIN]:
            return
        conf = hass.data[DOMAIN][account_name]
        account = conf[CONF_ACCOUNT]
        if not _validate_permissions("MailboxSettings.ReadWrite", conf):
            return

        mailbox = account.mailbox()
        mailbox.set_disable_reply()

    hass.services.async_register(DOMAIN, "set_auto_reply", set_auto_reply)
    hass.services.async_register(DOMAIN, "disable_auto_reply", disable_auto_reply)
    return True
