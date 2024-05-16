---
title: Installation and Configuration
nav_order: 4
---

# Installation and Configuration
## Installation
1. Ensure you have followed the [prerequisites instructions](./prerequisites.md)
    * Ensure you have a copy of the Client ID and the Client Secret **Value** (not the ID)
1. Optionally you can set up the [permissions](./permissions.md), alternatively you will be requested to approve permissions when you authenticate to MS 365.
1. Install this integration:
    * Recommended - [Home Assistant Community Store (HACS)](https://hacs.xyz/) or
    * Manually - Copy [these files](https://github.com/RogerSelwyn/O365-HomeAssistant/tree/master/custom_components/o365) to custom_components/o365/.
1. Restart your Home Assistant instance to enable the integration
1. Add o365 configuration to configuration.yaml using the [Configuration example](#configuration-examples) below.
1. Restart your Home Assistant instance again to enable your configuration.
1. A notification will be shown in the Repairs dialogue of your HA instance. Follow the instructions on this notification (or see [Authentication](./authentication.md)) to establish the link between this integration and the Azure app
    * A persistent token will be created in the hidden directory config/o365_storage/.O365-token-cache
    * The `o365_calendars_<account_name>.yaml` will be created under the config directory in the `o365_storage` directory.
    * If todo_sensors is enabled then `o365_tasks_<account_name>.yaml` will be created under the config directory in the `o365_storage` directory.
1. [Configure Calendars](./calendar_configuration.md)
1. [Configure To-Dos](./todos_configuration.md) (if required)
1. Restart your Home Assistant instance.

**Note** If your installation does not complete authentication, or the sensors are not created, please go back and ensure you have accurately followed the steps detailed, also look in the logs to see if there are any errors. You can also look at the [errors page](./errors.md) for some other possibilities.

## Configuration examples

### Configuration format 
```yaml
o365:
  accounts:
    - account_name: Account1 # Do not use email address or spaces
      client_id: "xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"
      client_secret: "xx.xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      alt_auth_method: False
      enable_update: False
      email_sensor:
        - name: inbox
          max_items: 2
          is_unread: True
          download_attachments: False
      query_sensors:
        - name: "Example"
          folder: "Inbox/Test_Inbox" #Default is Inbox
          from: "mail@example.com"
          subject_contains: "Example subject"
          has_attachment: True
          max_items: 2
          is_unread: True
      status_sensors: # Cannot be used for personal accounts
        - name: "User Teams Status"
      chat_sensors: # Cannot be used for personal accounts
        - name: "User Chat"
      todo_sensors:
        enabled: False
        enable_update: False # set this to true if you want to be able to create new todos
    - account_name: Account2
      client_secret: "xx.xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      client_id: "xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"
```

### Configuration variables

Key | Type | Required | Description
-- | -- | -- | --
`account_name` | `string` | `True` | Uniquely identifying name for the account. Calendars entity names will be suffixed with this. `calendar.calendar_account1`. Do not use email address or spaces.
`client_id` | `string` | `True` | Client ID from your O365 application.
`client_secret` | `string` | `True` | Client Secret from your O365 application.
`alt_auth_method` | `boolean` | `False` | If False (default), authentication is not dependent on internet access to your HA instance. [See Authentication](./authentication.md)
`enable_update` | `boolean` | `False` | If True (**default is False**), this will enable the various services that allow the sending of emails and updates to calendars
`basic_calendar` | `boolean` | `False` | If True (**default is False**), the permission requested will be `calendar.ReadBasic`. `enable_update: true` = true cannot be used if `basic_calendar: true`
`groups` | `boolean` | `False` | If True (**default is False**), will enable support for group calendars. No discovery is performed. You will need to know how to get the group ID from the MS Graph API. *Not for use on shared mailboxes*
`track_new_calendar` | `boolean` | `False` | If True (default), will automatically generate a calendar_entity when a new calendar is detected. The system scans for new calendars only on startup.
`email_sensors` | `list<email_sensors>` | `False` | List of email_sensor config entries
`query_sensors` | `list<query_sensors>` | `False` | List of query_sensor config entries
`status_sensors` | `list<status_sensors>` | `False` | List of status_sensor config entries. *Not for use on personal accounts or shared mailboxes*
`chat_sensors` | `list<chat_sensors>` | `False` | List of chat_sensor config entries. *Not for use on personal accounts or shared mailboxes*
`todo_sensors` | `object<todo_sensors>` | `False` | To-Do List options *Not for use on shared mailboxes*
`auto_reply_sensors` | `object<auto_reply_sensors>` | `False` | Auto-reply sensor options *Not for use on shared mailboxes*
`shared_mailbox` | `string` | `False` | Email address or ID of shared mailbox *Only available for calendar and email sensors*


#### email_sensors

Key | Type | Required | Description
-- | -- | -- | --
`name` | `string` | `True` | The name of the sensor.
`folder` | `string` | `False` | Mail folder to monitor, for nested calendars separate with '/' ex. "Inbox/SubFolder/FinalFolder" Default is Inbox
`max_items` | `integer` | `False` | Max number of items to retrieve (default 5)
`is_unread` | `boolean` | `False` | True=Only get unread, False=Only get read, Not set=Get all
`download_attachments` | `boolean` | `False` | **True**=Download attachments, False=Don't download attachments
`html_body` | `boolean` | `False` | True=Output HTML body, **False**=Output plain text body

#### query_sensors

Key | Type | Required | Description
-- | -- | -- | --
`name` | `string` | `True` | The name of the sensor.
`folder` | `string` | `False` | Mail folder to monitor, for nested calendars separate with '/' ex. "Inbox/SubFolder/FinalFolder" Default is Inbox
`max_items` | `integer` | `False` | Max number of items to retrieve (default 5)
`is_unread` | `boolean` | `False` | True=Only get unread, False=Only get read, Not set=Get all
`from` | `string` | `False` | Only retrieve emails from this email address
`has_attachment` | `boolean` | `False` | True=Only get emails with attachments, False=Only get emails without attachments, Not set=Get all
`importance` | `string` | `False` | Only get items with 'low'/'normal'/'high' importance
`subject_contains` | `string` | `False` | Only get emails where the subject contains this string (Mutually exclusive with `subject_is`)
`subject_is` | `string` | `False` | Only get emails where the subject equals exactly this string (Mutually exclusive with `subject_contains`)
`download_attachments` | `boolean` | `False` | **True**=Download attachments, False=Don't download attachments
`html_body` | `boolean` | `False` | True=Output HTML body, **False**=Output plain text body
`body_contains` | `string` | `False` | Only get emails where the body contains this string

#### status_sensors (not for personal accounts)

Key | Type | Required | Description
-- | -- | -- | --
`name` | `string` | `True` | The name of the sensor.
`enable_update` | `boolean` | `False` | If True (**default is False**), this will enable the services to update user status. `email address` key must not be present.
`email` | `string` | `False` | Enter email address to monitor status for. `enable_update` key must not be present.

#### chat_sensors (not for personal accounts)

Key | Type | Required | Description
-- | -- | -- | --
`name` | `string` | `True` | The name of the sensor.
`enable_update` | `boolean` | `False` | If True (**default is False**), this will enable the services to send messages to a chat

#### todo_sensors

Key | Type | Required | Description
-- | -- | -- | --
`enabled` | `boolean` | `True` | True=Enables To-Do Lists, **False**=Disables To-Do Lists.
`enable_update` | `boolean` | `False` | If True (**default is False**), this will enable the services to create/update/delete to-dos
`track_new` | `boolean` | `False` | If True (default), will automatically generate a todo_entity when a new to-do list is detected. The system scans for new to-do lists only on startup.

#### auto_reply_sensors 

Key | Type | Required | Description
-- | -- | -- | --
`name` | `string` | `True` | The name of the sensor.
