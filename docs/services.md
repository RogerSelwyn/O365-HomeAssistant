---
title: Services
nav_order: 7
---

# Services
## notify.o365_email

### Service data

Key | Type | Required | Description
-- | -- | -- | --
`message` | `string` | `True` | The email body
`title` | `string` | `False` | The email subject
`data` | `dict<data>` | `False` | Addional attributes - see table below

### Extended data

Key | Type | Required | Description
-- | -- | -- | --
`target` | `string` | `False` | recipient of the email, if not set will use the configured account's email address
`message_is_html` | `boolean` | `False` | Is the message formatted as html
`photos` | `list<string>` | `False` | Filepaths or urls of pictures to embed into the email body
`attachments` | `list<string>` | `False` | Filepaths to attach to email
`zip_attachments` | `boolean` | `False` | Zip files from attachments into a zip file before sending
`zip_name` | `string` | `False` | Name of the generated zip file

### Example notify service call

```
service: notify.o365_email
data:
  message: The garage door has been open for 10 minutes.
  title: Your Garage Door Friend
  data:
    message_is_html: true
    attachments:
      - "/config/documents/sendfile.txt"
    zip_attachments: true
    zip_name: "zipfile.zip"
    photos:
      - "/config/documents/image.jpg"
```
## o365.create_calendar_event
Create an event in the specified calendar - All paremeters are shown in the available parameter list on the Developer Tools/Services tab.
## o365.modify_calendar_event
Modify an event in the specified calendar - All paremeters are shown in the available parameter list on the Developer Tools/Services tab.
## o365.remove_calendar_event
Remove an event in the specified calendar - All paremeters are shown in the available parameter list on the Developer Tools/Services tab.
## o365.respond_calendar_event
Respond to an event in the specified calendar - All paremeters are shown in the available parameter list on the Developer Tools/Services tab.
## o365.scan_for_calendars
Scan for new calendars and add to o365_calendars.yaml - No parameters.
