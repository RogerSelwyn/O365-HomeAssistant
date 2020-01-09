[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
# Office 365 sensor for Home Assistant
The sensor will give you todays events in your Office 365 calendar and add the data to an entity called *sensor.o365_calendar*  
This entity will have a current state of either True or False depending on whether the current time is inside an event.  
The entity attributes contains raw event information in json format.

## Installation

### Getting the client id and client secret
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

## Configuration

```yaml
# Example configuration.yaml entry
sensor:
  - platform: office365calendar
    client_id: YOUR_CLIENT_ID
    client_secret: YOUR_CLIENT_SECRET
    scan_interval: 300
```

### Configuration variables
**client_id**  
  (string)(Required)  
  Client ID from your O365 application.

**client_secret**  
  (string)(Required)  
  Client Secret from your O365 application.
  
**scan_interval**  
  (integer)(Optional)  
  The number of seconds between updates of todays calendar events
