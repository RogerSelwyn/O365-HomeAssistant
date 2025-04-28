---
title: Migration
nav_order: 19
---

# Migration

##  Migration Service

The `o365.migrate_config` service enables the migration from the Office 365 Integration for Home Assistant to the new Microsoft 365 suite of integrations. The new suite is made up of:
* [MS365 Calendar](https://github.com/RogerSelwyn/MS365-Calendar)
* [MS365 Mail](https://github.com/RogerSelwyn/MS365-Mail)
* [MS365-Teams](https://github.com/RogerSelwyn/MS365-Teams)
* [MS365-ToDo](https://github.com/RogerSelwyn/MS365-ToDo)

For the service to function fully it requires the relevant MS365 integrations to have been installed on the Home Assistant server. Currently, they will need to be installed HACS custom integrations. Requests have been raised to add them to the Default integration list, but they may not make it there until some time into the new year.

### Note
You will need to be on consitent versions of the integrations in order to minimise errors:
* O365 <  5.0.0 - Needs MS365 <  1.3.0
* O365 >= 5.0.0 - Needs MS365 >= 1.3.0

### o365.migrate_config
The service will attempt to create config entries for any sensors that would have been created via the O365 YAML based configuration. You will see repair requests for them to be re-configured to authenticate to Microsoft. To do this:
* Select the config item in `Devices & Services`
* Click on the 3 vertical dots
* Select `Reconfigure`

You should see that all your configuration has been retained. You should only need to click Next/Submit to reach the dialogue where you can request Microsoft authentication. When successfully authenticated, your entities will be created and enabled. *Note* your entities will have new names, but can be renamed to replace existing O365 entities if needed, so that automations/etc don't need to be modified.

* Calendars - One entry for each O365 account
* Mail
  * One entry for each Inbox/Query O365 sensor. They are now treated equally. 
  * AutoReply - This will be associated with one of your mail entries
* Teams
  * A combined entry for O365 chat/status which do not an alternate email to monitor for status. 
  * A separate entry for each O365 status sensor that has an alternate email to monitor
* To Dos - One entry for each O365 account

The calendars.yaml, tasks.yaml (now named todos.yaml) and token files will be in the new `ms365_storage` folder in your configuration. 

### Post migration
When you have migrated over the following can be removed:
* O365 can be removed from configuration.yaml
* O365 can be uninstalled from HACS
* The o365_storage folder can be deleted.

If you did not use the migration service and created a new Entra App, you can delete the O365 application from Azure by clicking on `App registrations` or `Applications from personal account` [here](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade).
