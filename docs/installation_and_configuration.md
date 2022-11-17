---
title: Installation and Configuration
nav_order: 3
---

# Installation and Configuration
## Installation
1. Install this integration:
    * Recommended - [Home Assistant Community Store (HACS)](https://hacs.xyz/) or
    * Manually - Copy [these files](https://github.com/RogerSelwyn/O365-HomeAssistant/tree/master/custom_components/o365) to custom_components/o365/.
2. Add o365 configuration to configuration.yaml using the [Configuration example](#configuration-examples) below.
3. Restart your Home Assistant instance.
   **Note:** if Home Assistant gives the error "module not found", try restarting Home Assistant once more.
4. A persistent notification will be shown in the Notifications panel of your HA instance. Follow the instructions on this notification (or see [Authentication](./authentication.md)) to establish the link between this integration and the Azure app
    * A persistent token will be created in the hidden directory config/.O365-token-cache
    * The `o365_calendars_<account_name>.yaml` (or `o365_calendars.yaml` for secondary configuration method) will be created under the config directory in the `o365_storage` directory.
5. [Configure Calendars](./calendar_configuration.md)
6. Restart your Home Assistant instance.

## Configuration examples

### Primary configuration format (as of v3.x.x) - Preferred because it provides improved security and allows for multiple accounts.
```yaml
# Example configuration.yaml entry for multiple accounts
o365:
  accounts:
    - account_name: Account1
      client_id: "xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"
      client_secret: "xx.xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      alt_auth_method: False
      enable_update: True
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
    - account_name: Account2
      client_secret: "xx.xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      client_id: "xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"
```
### Secondary configuration format - Less preferred and can only use for a single account.
```yaml
# Example configuration.yaml entry for single account
o365:
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
```

### Configuration variables

#### Primary format

Key | Type | Required | Description
-- | -- | -- | --
`account_name` | `string` | `True` | Uniquely identifying name for the account. Calendars entity names will be suffixed with this. e.g `calendar.calendar_account1`
`client_id` | `string` | `True` | Client ID from your O365 application.
`client_secret` | `string` | `True` | Client Secret from your O365 application.
`alt_auth_method` | `boolean` | `False` | If False (default), authentication is not dependent on internet access to your HA instance. [See Authentication](./authentication.md)
`enable_update` | `boolean` | `False` | If True (**default is False**), this will enable the various services that allow the sending of emails and updates to calendars
`groups` | `boolean` | `False` | If True (**default is False**), will enable support for group calendars. No discovery is performed. You will need to know how to get the group id from the MS Graph API.
`track_new_calendar` | `boolean` | `False` | If True (default), will automatically generate a calendar_entity when a new calendar is detected. The system scans for new calendars only on startup.
`email_sensors` | `list<email_sensors>` | `False` | List of email_sensor config entries
`query_sensors` | `list<query_sensors>` | `False` | List of query_sensor config entries
`status_sensors` | `list<status_sensors>` | `False` | List of status_sensor config entries. *Not for use on personal accounts*
`chat_sensors` | `list<chat_sensors>` | `False` | List of chat_sensor config entries. *Not for use on personal accounts*
`todo_sensors` | `object<query_sensors>` | `False` | ToDo sensor options 

#### Secondary format

Key | Type | Required | Description
-- | -- | -- | --
`client_id` | `string` | `True` | Client ID from your O365 application.
`client_secret` | `string` | `True` | Client Secret from your O365 application.
`alt_auth_method` | `boolean` | `False` | If False (default), authentication is not dependent on internet access to your HA instance. [See Authentication](./authentication.md)
`enable_update` | `boolean` | `False` | If True (**default is True**), this will enable the various services that allow the sending of emails and updates to calendars
`track_new_calendar` | `boolean` | `False` | If True (default), will automatically generate a calendar_entity when a new calendar is detected. The system scans for new calendars only on startup.
`email_sensors` | `list<email_sensors>` | `False` | List of email_sensor config entries
`query_sensors` | `list<query_sensors>` | `False` | List of query_sensor config entries
`status_sensors` | `list<status_sensors>` | `False` | List of status_sensor config entries. *Not for use on personal accounts*

#### email_sensors

Key | Type | Required | Description
-- | -- | -- | --
`name` | `string` | `True` | The name of the sensor.
`folder` | `string` | `False` | Mail folder to monitor, for nested calendars seperate with '/' ex. "Inbox/SubFolder/FinalFolder" Default is Inbox
`max_items` | `integer` | `False` | Max number of items to retrieve (default 5)
`is_unread` | `boolean` | `False` | True=Only get unread, False=Only get read, Not set=Get all
`download_attachments` | `boolean` | `False` | **True**=Download attachments, False=Don't download attachments

#### query_sensors

Key | Type | Required | Description
-- | -- | -- | --
`name` | `string` | `True` | The name of the sensor.
`folder` | `string` | `False` | Mail folder to monitor, for nested calendars seperate with '/' ex. "Inbox/SubFolder/FinalFolder" Default is Inbox
`max_items` | `integer` | `False` | Max number of items to retrieve (default 5)
`is_unread` | `boolean` | `False` | True=Only get unread, False=Only get read, Not set=Get all
`from` | `string` | `False` | Only retrieve emails from this email address
`has_attachment` | `boolean` | `False` | True=Only get emails with attachments, False=Only get emails without attachments, Not set=Get all
`importance` | `string` | `False` | Only get items with 'low'/'normal'/'high' importance
`subject_contains` | `string` | `False` | Only get emails where the subject contains this string (Mutually exclusive with `subject_is`)
`subject_is` | `string` | `False` | Only get emails where the subject equals exactly this string (Mutually exclusive with `subject_contains`)
`download_attachments` | `boolean` | `False` | **True**=Download attachments, False=Don't download attachments
`body_contains` | `string` | `False` | Only get emails where the body contains this string

#### status_sensors (not for personal accounts)

Key | Type | Required | Description
-- | -- | -- | --
`name` | `string` | `True` | The name of the sensor.

#### chat_sensors (not for personal accounts)

Key | Type | Required | Description
-- | -- | -- | --
`name` | `string` | `True` | The name of the sensor.

#### todo_sensors

Key | Type | Required | Description
-- | -- | -- | --
`enabled` | `boolean` | `True` | True=Enables ToDo sensors, **False**=Disables ToDo sensors.

