---
title: Home
nav_order: 1
---

# Office 365 Integration for Home Assistant

## Deprecation Notice:
The Calendar, Mail Notification and To Do entities and services are now deprecated in the O365 integration. Teams will also be deprecated in the near future at which point all development on O365 will stop unless it is required to support migration to the MS365 integrations.

Details on how to migration to the new MS365 integrations can be found here - [Migration](https://rogerselwyn.github.io/O365-HomeAssistant/migration.html)

This integration enables:
1. Getting and creating calendar events
2. Getting emails from your inbox using one of two available sensor types (e-mail and query)
3. Sending emails via the notify.o365_email service
4. Getting presence from Teams (not for personal accounts)
5. Getting the latest chat message from Teams (not for personal accounts)
6. Getting and creating To-Dos
7. Setting Auto Reply/Out of Office response

This project would not be possible without the wonderful [python-o365 project](https://github.com/O365/python-o365).

Details on how to migration to the new `MS365` integrations can be found here - [Migration](migration.md)