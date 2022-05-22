[![Validate with hassfest](https://github.com/RogerSelwyn/O365-HomeAssistant/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/RogerSelwyn/O365-HomeAssistant/actions/workflows/hassfest.yaml) [![HACS Validate](https://github.com/RogerSelwyn/O365-HomeAssistant/actions/workflows/hacs.yaml/badge.svg)](https://github.com/RogerSelwyn/O365-HomeAssistant/actions/workflows/hacs.yaml) [![CodeFactor](https://www.codefactor.io/repository/github/rogerselwyn/o365-homeassistant/badge)](https://www.codefactor.io/repository/github/rogerselwyn/o365-homeassistant) [![Downloads for latest release](https://img.shields.io/github/downloads/RogerSelwyn/O365-HomeAssistant/latest/total.svg)](https://github.com/RogerSelwyn/O365-HomeAssistant/releases/latest)

![GitHub release](https://img.shields.io/github/v/release/RogerSelwyn/O365-HomeAssistant) [![maintained](https://img.shields.io/maintenance/yes/2022.svg)](#) [![maintainer](https://img.shields.io/badge/maintainer-%20%40RogerSelwyn-blue.svg)](https://github.com/RogerSelwyn) [![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration) [![Community Forum](https://img.shields.io/badge/community-forum-brightgreen.svg)](https://community.home-assistant.io/t/office-365-calendar-access)

# Office 365 Integration for Home Assistant

*This is a fork of the original integration by @PTST which has now been archived.*

This integration enables:
1. Getting and creating calendar events from O365.
2. Getting emails from your inbox using one of two available sensor types (e-mail and query).
3. Sending emails via the notify.o365_email service.
4. Getting presence from Teams (not for personal accounts)
5. Getting the latest chat message from Teams (not for personal accounts)

This project would not be possible without the wonderful [python-o365 project](https://github.com/O365/python-o365).

### [Buy Me A ~~Coffee~~ Beer 🍻](https://buymeacoffee.com/rogtp)
I work on this integration because I like things to work well for myself and others. Whilst I have now made significant changes to the integration, it would not be as it stands today without the major work to create it put in by @PTST. Please don't feel you are obligated to donate, but of course it is appreciated.

# Prerequisites

## Getting the client id and client secret
To allow authentication, you first need to register your application at Azure App Registrations:

1. Login at [Azure Portal (App Registrations)](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade). Personal accounts may receive an authentication notification that can be ignored.

2. Create a new App Registration. Give it a name. In Supported account types, choose "Accounts in any organizational directory and personal Microsoft accounts (e.g. Skype, Xbox, Outlook.com)" for greatest freedom of login account. Choose other options if you are confident it will cover the type of account you are using to login.  Click Register.

3. Click Add a Redirect URI. Click Add a platform. Select Web. Set redirect URI to: `https://login.microsoftonline.com/common/oauth2/nativeclient`, leave the other fields blank and click Configure.

   An alternate method of authentication is available which requires internet access to your HA instance if preferred. The alternate method is simpler to use when authenticating, but is more complex to setup correctly. See [Authentication](#authentication) section for more details.

   _**NOTE:** As of version 3.2.0, the primary (default) and alternate authentication methods have essentially reversed. The primary (default) method now DOES NOT require direct access to your HA instance from the internet while the alternate method DOES require direct access. If you previously did NOT set 'alt_auth_flow' or had it set to False, please set 'alt_auth_method' to True and remove 'alt_auth_flow' from your config. This will only be necessary upon re-authentication._

4. From the Overview page, copy the Application (client) ID.

5. Under "Certificates & secrets", generate a new client secret. Set the expiration as desired.  This appears to be limited to 2 years. Copy the Value of the client secret now. It will be hidden later on.  If you lose track of the secret, return here to generate a new one.

6. Under "API Permissions" click Add a permission, then Microsoft Graph, then Delegated permission, and add the following permissions:
   * offline_access - *Maintain access to data you have given it access to*
   * Calendars.Read - *Read user calendars*
   * Users.Read - *Sign in and read user profile*

   If you are creating an email_sensor or a query_sensor you will need:
   * Mail.Read - *Read access to user mail*

   If you are creating a status_sensor you will need:
   * Presence.Read - *Read user's presence information* (**Not for personal accounts**)

   If you are creating a chat_sensor you will need:
   * Chat.Read - *Read user chat messages* (**Not for personal accounts**)

   If you intend to set [enable_update](#primary-method) to True, (it defaults to False for multi-account installs and True for other installs so as not to break existing installs), then the following permissions are also required (you can always remove permissions later):
   * Calendars.ReadWrite - *Read and write user calendars*
   * Mail.ReadWrite - *Read and write access to user mail*
   * Mail.Send - *Send mail as a user*

# Installation and Configuration
1. Install this integration:
    * Recommended - Home Assistant Community Store (HACS) or
    * Manually - Copy [these files](https://github.com/RogerSelwyn/O365-HomeAssistant/tree/master/custom_components/o365) to custom_components/o365/.
2. Add o365 configuration to configuration.yaml using the [Configuration example](#configuration-example) below.
3. Restart your Home Assistant instance.
   **Note:** if Home Assistant gives the error "module not found", try restarting Home Assistant once more.
4. A persistent notification will be shown in the Notifications panel of your HA instance. Follow the instructions on this notification (or see [Authentication](#authentication)) to establish the link between this integration and the Azure app
    * A persistent token will be created in the hidden directory config/.O365-token-cache
    * The o365_calendars_<account_name>.yaml (or o365_calendars.yaml for secondary configuration method) will be created under the config directory
5. [Configure Calendars](#calendar-configuration)
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
`alt_auth_method` | `boolean` | `False` | If False (default), authentication is not dependent on internet access to your HA instance. [See Authentication](#authentication)
`enable_update` | `boolean` | `False` | If True (**default is False**), this will enable the various services that allow the sending of emails and updates to calendars
`track_new_calendar` | `boolean` | `False` | If True (default), will automatically generate a calendar_entity when a new calendar is detected. The system scans for new calendars only on startup.
`email_sensors` | `list<email_sensors>` | `False` | List of email_sensor config entries
`query_sensors` | `list<query_sensors>` | `False` | List of query_sensor config entries
`status_sensors` | `list<status_sensors>` | `False` | List of status_sensor config entries. *Not for use on personal accounts*

#### Secondary format

Key | Type | Required | Description
-- | -- | -- | --
`client_id` | `string` | `True` | Client ID from your O365 application.
`client_secret` | `string` | `True` | Client Secret from your O365 application.
`alt_auth_method` | `boolean` | `False` | If False (default), authentication is not dependent on internet access to your HA instance. [See Authentication](#authentication)
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

#### status_sensors (not for personal accounts)
Key | Type | Required | Description
-- | -- | -- | --
`name` | `string` | `True` | The name of the sensor.

#### chat_sensors (not for personal accounts)
Key | Type | Required | Description
-- | -- | -- | --
`name` | `string` | `True` | The name of the sensor.

## Authentication
 _**NOTE:** As of version 3.2.0, the primary (default) and alternate authentication methods have essentially reversed. The primary (default) method now DOES NOT require direct access to your HA instance from the internet while the alternate method DOES require direct access. If you previously did NOT set 'alt_auth_flow' or had it set to False, please set 'alt_auth_method' to True and remove 'alt_auth_flow' from your config. This will only be necessary upon re-authentication._

The Primary method of authentication is the simplest to configure and requires no access from the internet to your HA instance, therefore is the most secure method. It has slightly more steps to follow when authenticating.

The alternate method is more complex to setup, since the Azure App that is created in the prerequisites section must be configured to enable authentication from your HA instance whether located in your home network or utilising a cloud service such as Nabu Casa. The actual authentication is slightly simpler with fewer steps.

During setup, the difference in configuration between each methid is the value of the redirect URI on your Azure App. The authentication steps for each method are shown below.

### Primary (default) authentication method
This requires *alt_auth_method* to be set to *False* or be not present and the redirect URI in your Azure app set to `https://login.microsoftonline.com/common/oauth2/nativeclient`.

After setting up configuration.yaml and restarting Home Assistant, a persistent notification will be created.
1. Click on this notification.
2. Click the "Link O365 account" link.
3. Login on the Microsoft page.
4. Copy the URL from the browser URL bar.
5. Insert into the "Returned URL" field
6. Click Submit.

### Alternate authentication method
This requires the *alt_auth_method* to be set to *True* and the redirect URI in your Azure app set to `https://<your_home_assistant_url_or_local_ip>/api/o365` (Nabu Casa users should use `https://<NabuCasaBaseAddress>/api/o365` instead).

After setting up configuration.yaml with the key set to _True_ and restarting Home Assistant a persistent notification will be created.
1. Click on this notification.
2. Click the "Link O365 account" link.
3. Login on the Microsoft page; when prompted, authorize the app you created
4. Close the window when the message "Success! This window can be closed" appears.

### Multi-Factor Authentication (MFA)
If you are using Multi-factor Authentication (MFA), you may find you also need to add `https://login.microsoftonline.com/organizations/oauth2/v2.0/authorize` to your redirect URIs.

## Calendar configuration
The integration uses an external o365_calendars_<account_name>.yaml file (or o365_calendars.yaml for the secondary configuration format).
### example o365_calendar_<account_name>.yaml:
```yaml
- cal_id: xxxx
  entities:
  - device_id: work_calendar
    end_offset: 24
    name: My Work Calendar
    start_offset: 0
    track: true

- cal_id: xxxx
  entities:
  - device_id: birthdays
    end_offset: 24
    name: Birthdays
    start_offset: 0
    track: true
```

#### o365_calendars_<account_name>.yaml
Key | Type | Required | Description
-- | -- | -- | --
`cal_id` | `string` | `True` | O365 generated unique ID, DO NOT CHANGE
`entities` | `list<entity>` | `True` | List of entities (see below) to generate from this calendar

#### Entity configuration
Key | Type | Required | Description
-- | -- | -- | --
`device_id` | `string` | `True` | The entity_id will be "calendar.{device_id}"
`name` | `string` | `True` | The name of your sensor that you’ll see in the frontend.
`track` | `boolean` | `True` | **True**=Create calendar entity. False=Don't create entity
`search` | `string` | `False` | Only get events if subject contains this string
`start_offset` | `integer` | `False` | Number of hours to offset the start time to search for events for (negative numbers to offset into the past).
`end_offset` | `integer` | `False` | Number of hours to offset the end time to search for events for (negative numbers to offset into the past).

## Services
### notify.o365_email

#### Service data
Key | Type | Required | Description
-- | -- | -- | --
`message` | `string` | `True` | The email body
`title` | `string` | `False` | The email subject
`data` | `dict<data>` | `False` | Addional attributes - see table below

#### Extended data
Key | Type | Required | Description
-- | -- | -- | --
`target` | `string` | `False` | recipient of the email, if not set will use the configured account's email address
`message_is_html` | `boolean` | `False` | Is the message formatted as html
`photos` | `list<string>` | `False` | Filepaths or urls of pictures to embed into the email body
`attachments` | `list<string>` | `False` | Filepaths to attach to email
`zip_attachments` | `boolean` | `False` | Zip files from attachments into a zip file before sending
`zip_name` | `string` | `False` | Name of the generated zip file

#### Example notify service call

```
service: notify.o365_email
data:
  message: The garage door has been open for 10 minutes.
  title: Your Garage Door Friend
  data:
    message_is_html: true
    attachments:
      - "/config/documents/sendfile.txt"
    zip_attachments: true
    zip_name: "zipfile.zip"
    photos:
      - "/config/documents/image.jpg"
```
### o365.create_calendar_event
Create an event in the specified calendar - All paremeters are shown in the available parameter list on the Developer Tools/Services tab.
### o365.modify_calendar_event
Modify an event in the specified calendar - All paremeters are shown in the available parameter list on the Developer Tools/Services tab.
### o365.remove_calendar_event
Remove an event in the specified calendar - All paremeters are shown in the available parameter list on the Developer Tools/Services tab.
### o365.respond_calendar_event
Respond to an event in the specified calendar - All paremeters are shown in the available parameter list on the Developer Tools/Services tab.
### o365.scan_for_calendars
Scan for new calendars and add to o365_calendars.yaml - No parameters.

## Calendar Sensor layout
The status of the calendar sensor indicates (on/off) whether there is an event on at the current time. The `message`, `all_day`, `start_time`, `end_time`, `location`, `description` and `offset_reached` attributes provide details of the current of next event. A non all-day event is favoured over all_day events.

The `data` attribute provides an array of events for the period defined by the `start_offset` and `end_offset` in o365_calendars_<account_name>.yaml. Individual array elements can be accessed using the notation `{{ states.calendar.calendar_<account_name>.attributes.data[0...n] }}`

## Errors
* **The reply URL specified in the request does not match the reply URLs configured for the application.**
  * Please ensure that you have configured the internet url on your Home Assistant network settings config and that you have added the correct redirect uri to your Azure app
* **Client is public so neither 'client_assertion' nor 'client_secret' should be presented.**
  * Please ensure that you have set "Default client type" to Yes in your Azure app under Authentication ![Default client type img](https://user-images.githubusercontent.com/17211264/72337364-ba936a80-36c2-11ea-834d-2af9b84a8bba.png)
* **Application {x} is not configured as a multi-tenant application.**
  * In your azure app go to Manifest, find the key "signInAudience", change its value to "AzureADandPersonalMicrosoftAccount"
* **Platform error sensor.office365calendar - No module named '{x}'**
  * This is a known Home Assistant issue, all that's needed to fix this should be another restart of your Home Assistant server. If this does not work, please try installing the component in this order:


      1. Install the component.
      2. Restart Home Assistant.
      3. Add the sensor to your configuration.yaml
      4. Restart Home Assistant again.

**_Please note that any changes made to your Azure app settings takes a few minutes to propagate. Please wait around 5 minutes between changes to your settings and any auth attempts from Home Assistant._**
