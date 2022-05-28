---
title: Errors
nav_order: 8
---

# Errors
* **The reply URL specified in the request does not match the reply URLs configured for the application.**
  * Please ensure that you have configured the internet url on your Home Assistant network settings config and that you have added the correct redirect uri to your Azure app
* **Client is public so neither 'client_assertion' nor 'client_secret' should be presented.**
  * Please ensure that you have set "Default client type" to Yes in your Azure app under Authentication ![Default client type img](https://user-images.githubusercontent.com/17211264/72337364-ba936a80-36c2-11ea-834d-2af9b84a8bba.png)
* **Application {x} is not configured as a multi-tenant application.**
  * In your azure app go to Manifest, find the key "signInAudience", change its value to "AzureADandPersonalMicrosoftAccount"
* **Platform error sensor.office365calendar - No module named '{x}'**
  * This is a known Home Assistant issue, all that's needed to fix this should be another restart of your Home Assistant server. If this does not work, please try installing the component in this order:


      1. Install the component.
      2. Restart Home Assistant.
      3. Add the sensor to your configuration.yaml
      4. Restart Home Assistant again.

**_Please note that any changes made to your Azure app settings takes a few minutes to propagate. Please wait around 5 minutes between changes to your settings and any auth attempts from Home Assistant._**
