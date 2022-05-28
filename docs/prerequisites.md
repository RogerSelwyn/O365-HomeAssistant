# Prerequisites

## Getting the client id and client secret
To allow authentication, you first need to register your application at Azure App Registrations:

1. Login at [Azure Portal (App Registrations)](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade). Personal accounts may receive an authentication notification that can be ignored.

2. Create a new App Registration. Give it a name. In Supported account types, choose "Accounts in any organizational directory and personal Microsoft accounts (e.g. Skype, Xbox, Outlook.com)" for greatest freedom of login account. Choose other options if you are confident it will cover the type of account you are using to login.  Click Register.

3. Click Add a Redirect URI. Click Add a platform. Select Web. Set redirect URI to: `https://login.microsoftonline.com/common/oauth2/nativeclient`, leave the other fields blank and click Configure.

   An alternate method of authentication is available which requires internet access to your HA instance if preferred. The alternate method is simpler to use when authenticating, but is more complex to setup correctly. See [Authentication](./authentication.md) section for more details.

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

   If you intend to set [enable_update](./installtion.md#configuration_variables) to True, (it defaults to False for multi-account installs and True for other installs so as not to break existing installs), then the following permissions are also required (you can always remove permissions later):
   * Calendars.ReadWrite - *Read and write user calendars*
   * Mail.ReadWrite - *Read and write access to user mail*
   * Mail.Send - *Send mail as a user*
