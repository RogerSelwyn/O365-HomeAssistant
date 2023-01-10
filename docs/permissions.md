---
title: Permissions
nav_order: 3
---

# Permissions

Under "API Permissions" click Add a permission, then Microsoft Graph, then Delegated permission, and add the permissions as detailed in the list and table below:
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
   | AutoReply | MailboxSettings.ReadWrite |   | *Read and write user mailbox settings* |       |
   
**Note** It should be noted that these are the permissions that are requested at authentication time (as appropriate for each sensor configured). When `enable_update` is configured to `true` all the associated `ReadWrite` permissions are requested as well, however you do not need to add `ReadWrite` for any sensor type where you do not what update permissions, it will still act as a Read Only sensor. This excludes the AutoReply option which is only `ReadWrite`.

For example, permissions as below (and with `enable_update` set to `true`) will create calendar sensors, create chat sensors, and create auto reply enable/disable services but will not enable create/modify/remove/respond services:
```json
 "scope": [
  "Calendars.Read",
  "Chat.Read",
  "MailboxSettings.ReadWrite",
  "User.Read",
 ]
```

## Changing Features and Permissions
If you decide to enable new features in the integration, or decide to change from read only to read/write, you will very likely get a warning message similar to the following in your logs.

`Minimum required permissions not granted: ['Tasks.Read', ['Tasks.ReadWrite']]`

You will need to delete the relevant token from the `<config>/o365_storage/.O365-token-cache` directory. When you restart HA, you will then be prompted to re-authenticate with O365 which will store a new token with the new permission