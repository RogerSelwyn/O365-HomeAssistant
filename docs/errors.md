---
title: Errors
nav_order: 12
---

# Errors
* **The reply URL specified in the request does not match the reply URLs configured for the application.**
  * Please ensure that you have configured the internet URL on your Home Assistant network settings config and that you have added the correct redirect URI to your Azure app

* **Client is public so neither 'client_assertion' nor 'client_secret' should be presented.**
  * Please ensure that you have set "Allow public client flows" to Yes in your Azure app under Authentication ![image](https://user-images.githubusercontent.com/36969394/198787952-9f818372-7684-42e1-ac30-a8ab05a5f478.png)
 
* **Application {x} is not configured as a multi-tenant application.**
  * In your azure app go to Manifest, find the key "signInAudience", change its value to "AzureADandPersonalMicrosoftAccount"

* **The logged in user is not authorized to fetch tokens for extension 'Microsoft_AAD_RegisteredApps' because the account is not a member of tenant 'xxxx'.**
  * Please make sure you have set the Supported accounts correctly as described in the [Prerequisites](./prerequisites.md)

**_Please note that any changes made to your Azure app settings takes a few minutes to propagate. Please wait around 5 minutes between changes to your settings and any auth attempts from Home Assistant._**
