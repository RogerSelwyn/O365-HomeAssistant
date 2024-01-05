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

4. From the Overview page, copy the Application (client) ID.

5. Under "Certificates & secrets", generate a new client secret. Set the expiration as desired.  This appears to be limited to 2 years. Copy the **Value** of the client secret now (not the ID), it will be hidden later on.  If you lose track of the secret, return here to generate a new one.

6. Under "API Permissions" click Add a permission, then Microsoft Graph, then Delegated permission, and add the permissions as detailed on the [permissions page](./permissions.md).