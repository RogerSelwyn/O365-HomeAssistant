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
