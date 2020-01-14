[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
# Office 365 sensor for Home Assistant
The sensor will give you todays events in your Office 365 calendar and add the data to an entity called *sensor.o365_calendar*  
This entity will have a current state of either True or False depending on whether the current time is inside an event.  
The entity attributes contains raw event information in json format.

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
* Calendars.Read - *Read user calendars*
* Calendars.Read.Shared - *Read user and shared calendars*
* offline_access - *Maintain access to data you have given it access to*
* Users.Read - *Sign in and read user profile*

## Adding to Home Assistant

### Manual installation
1. Install this component by copying these files to custom_components/office365calendar/.
2. Add the code to your configuration.yaml using the config options below.
3. Restart your Home Assistant instance.

_**Please note, it home assistants give the error "module not found", please try restarting home assistant once more, this should fix that**_

### Using Home Assistant Community Store (HACS)
1. Find the *Office 365 calendar sensor* on the integrations tab and install it.
2. Add the code to your configuration.yaml using the config options below.
3. Restart your Home Assistant instance.

_**Please note, it home assistants give the error "module not found", please try restarting home assistant once more, this should fix that**_

# Configuration

```yaml
# Example configuration.yaml entry
sensor:
  - platform: office365calendar
    client_id: YOUR_CLIENT_ID
    client_secret: YOUR_CLIENT_SECRET
    scan_interval: 300
```

## Configuration variables

Key | Type | Required | Description
-- | -- | -- | --
`client_id` | `string` | `True` | Client ID from your O365 application.
`client_secret` | `string` | `True` | Client Secret from your O365 application.
`name` | `string` | `False` | The name of the sensor.
`calendar_name` | `string` | `False` | Name of the calendar to retrieve, if not set, the default calendar will be used.
`start_offset` | `integer` | `False` | Number of hours to offset the start time to search for events for (negative numbers to offset into the past).
`end_offset` | `integer` | `False` | Number of hours to offset the end time to search for events for (negative numbers to offset into the past).
`scan_interval` | `integer` | `False` | The number of seconds between updates of todays calendar events.
`alt_auth_flow` | `boolean` | `False` | If True, an alternative auth flow will be provided which is not reliant on the redirect uri being reachable. [See alt-auth-flow](#alt-auth-flow)

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
