---
title: Authentication
nav_order: 5
---

# Authentication

The Primary method of authentication is the simplest to configure and requires no access from the internet to your HA instance, therefore is the most secure method. It has slightly more steps to follow when authenticating.

The alternate method is more complex to set up, since the Azure App that is created in the prerequisites' section must be configured to enable authentication from your HA instance whether located in your home network or utilising a cloud service such as Nabu Casa. The actual authentication is slightly simpler with fewer steps.

During setup, the difference in configuration between each method is the value of the redirect URI on your Azure App. The authentication steps for each method are shown below.

## Primary (default) authentication method
This requires *alt_auth_method* to be set to *False* or be not present and the redirect URI in your Azure app set to `https://login.microsoftonline.com/common/oauth2/nativeclient`.

After setting up configuration.yaml and restarting Home Assistant, a repair will be created.
1. Click on this repair.
2. Click the `Link O365 account` link.
3. Login on the Microsoft page; when prompted, authorize the app you created
4. Copy the URL from the browser URL bar.
5. Insert into the "Returned URL" field
6. Click `Submit`.

## Alternate authentication method
This requires the *alt_auth_method* to be set to *True* and the redirect URI in your Azure app set to `https://<your_home_assistant_url_or_local_ip>/api/o365` (Nabu Casa users should use `https://<NabuCasaBaseAddress>/api/o365` instead).

After setting up configuration.yaml with the key set to _True_ and restarting Home Assistant a repair will be created.
1. Click on this repair.
2. Click the `Link O365 account` link.
3. Login on the Microsoft page; when prompted, authorize the app you created
4. If required, close the window when the message "This window can be closed" appears.
5. Click `I authorized successfully`

## Multi-Factor Authentication (MFA)
If you are using Multi-factor Authentication (MFA), you may find you also need to add `https://login.microsoftonline.com/organizations/oauth2/v2.0/authorize` to your redirect URIs.

## Re-authentication
If you need to re-authenticate for any reason, for instance if you have changed features (such as enabling update) and haven't had the repair notification, you should delete the token as described on the [token page](./token.md).