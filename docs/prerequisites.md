---
title: Prerequisites
nav_order: 2
---

# Prerequisites

## Getting the client ID and client secret
To allow authentication, you first need to register your application at Azure App Registrations:

1. Login at [Azure Portal (App Registrations)](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade). Personal accounts may receive an authentication notification that can be ignored.

2. Create a new App Registration. Give it a name. In Supported account types, choose one of the following as needed by your setup:
   * `Accounts in any organizational directory (Any Azure AD directory - Multitenant) and personal Microsoft accounts (e.g. Skype, Xbox)`.   
   * `Accounts in any organizational directory (Any Azure AD directory - Multitenant)` 

   **Do not use the following:** 
   * `Accounts in this organizational directory only (xxxxx only - Single tenant)` 
   * `Personal Microsoft accounts only`

3. Click Add a Redirect URI. Click Add a platform. Select Web. Set redirect URI to `https://login.microsoftonline.com/common/oauth2/nativeclient`. Leave the other fields blank and click Configure.

   An alternate method of authentication is available which requires internet access to your HA instance if preferred. The alternate method is simpler to use when authenticating, but is more complex to set up correctly. See [Authentication](./authentication.md) section for more details.

   _**NOTE:** As of version 3.2.0, the primary (default) and alternate authentication methods have essentially reversed. The primary (default) method now DOES NOT require direct access to your HA instance from the internet while the alternate method DOES require direct access. If you previously did NOT set 'alt_auth_flow' or had it set to False, please set 'alt_auth_method' to True and remove 'alt_auth_flow' from your config. This will only be necessary upon re-authentication._

4. From the Overview page, copy the Application (client) ID.

5. Under "Certificates & secrets", generate a new client secret. Set the expiration as desired.  This appears to be limited to 2 years. Copy the Value of the client secret now. It will be hidden later on.  If you lose track of the secret, return here to generate a new one.

6. Under "API Permissions" click Add a permission, then Microsoft Graph, then Delegated permission, and add the permissions as detailed in the list and table below:
  * Calendar - The core permissions required for calendars to work
  * Email - For an email_sensor or a query_sensor
  * Status - For a status_sensor
  * Chat - For a chat_sensor
  * ToDo - For a todo_sensor
  * Group Calendar - For a manually added Group calendar
  * AutoReply - For Auto reply/Out of Office message configuration

  If you intend to use update functionality, then set [enable_update](./installation_and_configuration.md#configuration_variables) to `true`. Then for any sensor type, add the relevant `ReadWrite` permission as denoted by a `Y` in the update column.
   

   | Feature  | Permissions           | Update | O365 Description                      | Notes |
   |----------|-----------------------|:------:|---------------------------------------|-------|
   | Calendar | offline_access        |   | *Maintain access to data you have given it access to* |       |
   | Calendar | Calendars.Read        |   | *Read user calendars*  |       |
   | Calendar | Calendars.ReadWrite   | Y | *Read and write user calendars* |       |
   | Calendar | Users.Read            |   | *Sign in and read user profile* |       |
   | Email    | Mail.Read             |   | *Read access to user mail* |       |
   | Email    | Mail.ReadWrite        | Y | *Read and write access to user mail* |       |
   | Email    | Mail.Send             | Y | *Send mail as a user* |       |
   | Status   | Presence.Read         |   | *Read user's presence information* | Not for personal accounts |
   | Chat     | Chat.Read             |   | *Read user chat messages* | Not for personal accounts |
   | ToDo     | Tasks.Read            |   | *Read user's tasks and task lists* |       |
   | ToDo     | Tasks.ReadWrite       | Y | *Create, read, update, and delete user’s tasks and task lists* |   |
   | Group Calendar | Group.Read.All  |   | *Read all groups* | Not supported in legacy installs |
   | Group Calendar | Group.ReadWrite.All | Y | *Read and write all groups* | Not supported in legacy installs |
   | AutoReply | MailboxSettings.ReadWrite | Y | *Read and write user mailbox settings* |       |
   
**Note** It should be noted that these are the permissions that are requested at authentication time (as appropriate for each sensor configured). When `enable_update` is configured to `true` all the associated `ReadWrite` permissions are requested as well, however you do not need to add `ReadWrite` for any sensor type where you do not what update permissions, it will still act as a Read Only sensor. This excludes the AutoReply option which is only `ReadWrite` at this time since there is no associated sensor.

For example, permissions as below (and with `enable_update` set to `true`) will create calendar sensors but not enable create/modify/remove/respond services, create chat sensors, and create auto reply enable/disable services:
```json
 "scope": [
  "Calendars.Read",
  "Chat.Read",
  "MailboxSettings.ReadWrite",
  "User.Read",
 ]
```

See also [Changing Features and Permissions](./authentication.md#changing_features_and_permissions) should you decide to change your needs after initial setup.