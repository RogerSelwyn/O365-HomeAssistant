[![Validate with hassfest](https://github.com/RogerSelwyn/O365-HomeAssistant/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/RogerSelwyn/O365-HomeAssistant/actions/workflows/hassfest.yaml) [![HACS Validate](https://github.com/RogerSelwyn/O365-HomeAssistant/actions/workflows/hacs.yaml/badge.svg)](https://github.com/RogerSelwyn/O365-HomeAssistant/actions/workflows/hacs.yaml) [![CodeFactor](https://www.codefactor.io/repository/github/rogerselwyn/o365-homeassistant/badge)](https://www.codefactor.io/repository/github/rogerselwyn/o365-homeassistant) [![Downloads for latest release](https://img.shields.io/github/downloads/RogerSelwyn/O365-HomeAssistant/latest/total.svg)](https://github.com/RogerSelwyn/O365-HomeAssistant/releases/latest)

![GitHub release](https://img.shields.io/github/v/release/RogerSelwyn/O365-HomeAssistant) [![maintained](https://img.shields.io/maintenance/yes/2021.svg)](#) [![maintainer](https://img.shields.io/badge/maintainer-%20%40RogerSelwyn-blue.svg)](https://github.com/RogerSelwyn) [![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs) [![Community Forum](https://img.shields.io/badge/community-forum-brightgreen.svg)](https://community.home-assistant.io/t/custom-component-office-365-calendar-sensor)

# Office 365 Integration for Home Assistant

This is a fork of the original integration by @PTST which has now been archived. Primarily this is to enable it to still run on Home Assistant for my own usage, but I have also added a Logo and link to this github for the HACS required wheel in the core brand and wheel repositories. 

If issues are identified I will endeavour to fix, but I do not plan to add extra functionality. If someone wishes to take on full support, then they would be welcome to change the references within core Home Assistant.

This integration enables 
1. Getting calendar events from O365.
2. Sending emails via the notify.o365_email service.
3. Getting emails from your inbox. 

This project would not be possible without the wonderful [python-o365 project](https://github.com/O365/python-o365).

# Installation

## Getting the client id and client secret
To allow authentication you first need to register your application at Azure App Registrations.

Login at [Azure Portal (App Registrations)](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)

Create an app. Set a name.

In Supported account types choose "Accounts in any organizational directory and personal Microsoft accounts (e.g. Skype, Xbox, Outlook.com)", if you are using a personal account.

Set the redirect uri (Web) to: `https://<your_home_assistant_url_or_local_ip>/api/o365` and click register.  


Write down the Application (client) ID. You will need this value.

Under "Certificates & secrets", generate a new client secret. Set the expiration preferably to never. Write down the value of the client secret created now. It will be hidden later on.

Under "Api Permissions" add the following delegated permission from the Microsoft Graph API collection
* Calendars.ReadWrite - *Read and write user calendars*
* Calendars.ReadWrite.Shared - *Read and write user and shared calendars*
* offline_access - *Maintain access to data you have given it access to*
* Users.Read - *Sign in and read user profile*
* email - *View users' email address*
* Mail.ReadWrite - *Read and write access to user mail*
* Mail.ReadWrite.Shared - *Read and write user and shared mail*
* Mail.Send - *Send mail as a user*
* Mail.Send.Shared - *Send mail on behalf of others*

## Adding to Home Assistant

### Manual installation
1. Install this component by copying these files to custom_components/o365/.
2. Add the code to your configuration.yaml using the config options below.
3. Restart your Home Assistant instance.

_**Please note, it home assistants give the error "module not found", please try restarting home assistant once more, this should fix that**_

### Using Home Assistant Community Store (HACS)
1. Find the *Office 365 Integration* on the integrations tab and install it.
2. Add the code to your configuration.yaml using the config options below.
3. Restart your Home Assistant instance.

_**Please note, it home assistants give the error "module not found", please try restarting home assistant once more, this should fix that**_

# Configuration

```yaml
# Example configuration.yaml entry
o365:
  client_secret: "xx.xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  client_id: "xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"
  email_sensor:
    - name: inbox
      max_items: 2
      is_unread: True
  query_sensors:
    - name: "HA Notifications"
      folder: "Inbox/Test_Inbox"
      from: "mail@example.com"
      subject_contains: "Notifcation from home assistant"
      has_attachment: True
      max_items: 2
      is_unread: True
```

## notify.o365_email service data
Key | Type | Required | Description
-- | -- | -- | --
`message` | `string` | `True` | The email body
`title` | `string` | `False` | The email subject
`data` | `dict<data>` | `False` | addional attributes
`track_new_calendar` | `boolean` | `False` | Will automatically generate a calendar_entity when a new calendar is detected. The system scans for new calendars only on startup.

### data
Key | Type | Required | Description
-- | -- | -- | --
`target` | `string` | `False` | recipient of the email, if not set will use the configured account's email address
`message_is_html` | `boolean` | `False` | Is the message formatted as html
`photos` | `list<string>` | `False` | Filepaths or urls of pictures to embed into the email body
`attachments` | `list<string>` | `False` | Filepaths to attach to email
`zip_attachments` | `boolean` | `False` | Zip files from attachments into a zip file before sending
`zip_name` | `string` | `False` | Name of the generated zip file



## Configuration variables

Key | Type | Required | Description
-- | -- | -- | --
`client_id` | `string` | `True` | Client ID from your O365 application.
`client_secret` | `string` | `True` | Client Secret from your O365 application.
`alt_auth_flow` | `boolean` | `False` | If True, an alternative auth flow will be provided which is not reliant on the redirect uri being reachable. [See alt-auth-flow](#alt-auth-flow)
`calendars` | `list<calendars>` | `False` | List of calendar config entries
`email_sensors` | `list<email_sensors>` | `False` | List of email_sensor config entries
`query_sensors` | `list<query_sensors>` | `False` | List of query_sensor config entries

### email_sensors
Key | Type | Required | Description
-- | -- | -- | --
`name` | `string` | `True` | The name of the sensor.
`folder` | `string` | `False` | Mail folder to monitor, for nested calendars seperate with '/' ex. "Inbox/SubFolder/FinalFolder"
`max_items` | `integer` | `False` | Max number of items to retrieve (default 5)
`is_unread` | `boolean` | `False` | True=Only get unread, False=Only get read, Not set=Get all


### query_sensors
Key | Type | Required | Description
-- | -- | -- | --
`name` | `string` | `True` | The name of the sensor.
`folder` | `string` | `False` | Mail folder to monitor, for nested calendars seperate with '/' ex. "Inbox/SubFolder/FinalFolder"
`max_items` | `integer` | `False` | Max number of items to retrieve (default 5)
`is_unread` | `boolean` | `False` | True=Only get unread, False=Only get read, Not set=Get all
`from` | `string` | `False` | Only retrieve emails from this email address
`has_attachment` | `boolean` | `False` | True=Only get emails with attachments, False=Only get emails without attachments, Not set=Get all
`subject_contains` | `string` | `False` | Only get emails where the subject contains this string (Mutually exclusive with `subject_is`)
`subject_is` | `string` | `False` | Only get emails where the subject equals exactly this string (Mutually exclusive with `subject_contains`)

## Calendar configuration
This component has changed to now using an external o365_calendars.yaml file, this is done to align this component more with the official Google Calendar Event integration.
### example o365_calendar.yaml:
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

### o365_calendars.yaml
Key | Type | Required | Description
-- | -- | -- | --
`cal_id` | `string` | `True` | O365 generated unique ID, DO NOT CHANGE
`entities` | `list<entity>` | `True` | List of entities to generate from this calendar

### Entity configuration
Key | Type | Required | Description
-- | -- | -- | --
`device_id` | `string` | `True` | The entity_id will be "calendar.{device_id}"
`name` | `string` | `True` | What is the name of your sensor that you’ll see in the frontend.
`track` | `boolean` | `True` | Should we create a sensor true or ignore it false?
`search` | `string` | `False` | Only get events if subject contains this string
`start_offset` | `integer` | `False` | Number of hours to offset the start time to search for events for (negative numbers to offset into the past).
`end_offset` | `integer` | `False` | Number of hours to offset the end time to search for events for (negative numbers to offset into the past).

## Authentication.
### Default auth flow.
After setting up configuration.yaml and restarting home assistant a persisten notification will be created.
1. Click on this notification.
2. Click the "Link O365 account" link.
3. Login on the microsoft page.
4. Close the window when the message "Success! This window can be closed" appears.
5. That's it.

### Alt auth flow.
**NB. This requires the *alt_auth_flow* to be set to *True* and the redirect uri in your Azure app set to "https://login.microsoftonline.com/common/oauth2/nativeclient" this needs to be set as as a manual url, with type web, just checking the checkmark for it does not seem to work**  
After setting up configuration.yaml with the key set to _True_ and restarting home assistant a persisten notification will be created.
1. Click on this notification.
2. Click the "Link O365 account" link.
3. Login on the microsoft page.
4. Copy the url from the browser url bar.
5. Insert into the "Returned Url" field. and click Submit.
5. That's it.

## Errors
* **The reply URL specified in the request does not match the reply URLs configured for the application.** 
  * Please ensure that you have configured base_url in your http config https://www.home-assistant.io/integrations/http/#base_url and that you have added the correct reply url to your Azure app
* **Client is public so neither 'client_assertion' nor 'client_secret' should be presented.**
  * Please ensure that you have set "Default client type" to Yes in your Azure app under Authentication ![Default client type img](https://user-images.githubusercontent.com/17211264/72337364-ba936a80-36c2-11ea-834d-2af9b84a8bba.png)
* **Application {x} is not configured as a multi-tenant application.**
  * In your azure app go to Manifest, find the key "signInAudience", change its value to "AzureADandPersonalMicrosoftAccount"
* **Platform error sensor.office365calendar - No module named '{x}'**
  * This is a known home assistant issue, all that's needed to fix this should be another restart of your home assistant server. If this does not work, please try installing the component in this order:
  
  
    1\. Install the component.  
    2\. Restart home assistant.  
    3\. Then add the sensor to your configuration.yaml  
    4\. Restart home assistant again.  

**_Please note that any changes made to your Azure app settings takes a few minutes to propagate. Please wait around 5 minutes between changes to your settings and any auth attemps from Home Assistant_**
