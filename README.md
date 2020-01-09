[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

# Office 365 sensor for Home Assistant

## Installation

### Getting the client id and client secret
To allow authentication you first need to register your application at Azure App Registrations.

Login at [Azure Portal (App Registrations)](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)

Create an app. Set a name.

In Supported account types choose "Accounts in any organizational directory and personal Microsoft accounts (e.g. Skype, Xbox, Outlook.com)", if you are using a personal account.

Set the redirect uri (Web) to: {your home assistant baseurl}/api/o365 and click register. 

Write down the Application (client) ID. You will need this value.

Under "Certificates & secrets", generate a new client secret. Set the expiration preferably to never. Write down the value of the client secret created now. It will be hidden later on.

Under Api Permissions:

Add the following delegated permission from the Microsoft Graph API collection
* Calendars.Read - *Read user calendars*
* Calendars.Read.Shared - *Read user and shared calendars*
* offline_access - *Maintain access to data you have given it access to*
* Users.Read - *Sign in and read user profile*
