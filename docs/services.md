---
title: Services
nav_order: 15
---

# Services

##  Notify Services

### notify.o365_email_xxxxxxxx

#### Service data

Key | Type | Required | Description
-- | -- | -- | --
`message` | `string` | `True` | The email body
`title` | `string` | `False` | The email subject
`data` | `dict<data>` | `False` | Additional attributes - see table below

#### Extended data

Key | Type | Required | Description
-- | -- | -- | --
`target` | `string` | `False` | Recipient of the email, if not set will use the configured account's email address
`sender` | `string` | `False` | Sender of the email, if not set will use the configured account's email address - where the authenticated user has been delegated access to the mailbox
`message_is_html` | `boolean` | `False` | Is the message formatted as HTML
`importance` | `string` | `False` | Set importance to `low`, `medium` or `high`
`photos` | `list<string>` | `False` | File paths or URLs of pictures to embed into the email body
`attachments` | `list<string>` | `False` | File paths to attach to email
`zip_attachments` | `boolean` | `False` | Zip files from attachments into a zip file before sending
`zip_name` | `string` | `False` | Name of the generated zip file

#### Example notify service call

```yaml
service: notify.o365_email_xxxxxxxx
data:
  message: The garage door has been open for 10 minutes.
  title: Your Garage Door Friend
  data:
    target: joebloggs@hotmail.com
    sender: mgmt@noname.org.uk
    message_is_html: true
    attachments:
      - "/config/documents/sendfile.txt"
    zip_attachments: true
    zip_name: "zipfile.zip"
    photos:
      - "/config/documents/image.jpg"
```
##  Calendar Services
o365.create_calendar_event
Create an event in the specified calendar - All parameters are shown in the available parameter list on the Developer Tools/Services tab.
### o365.modify_calendar_event
Modify an event in the specified calendar - All parameters are shown in the available parameter list on the Developer Tools/Services tab. Not possible for group calendars.
### o365.remove_calendar_event
Remove an event in the specified calendar - All parameters are shown in the available parameter list on the Developer Tools/Services tab. Not possible for group calendars.
### o365.respond_calendar_event
Respond to an event in the specified calendar - All parameters are shown in the available parameter list on the Developer Tools/Services tab. Not possible for group calendars.
### o365.scan_for_calendars
Scan for new calendars and add to o365_calendars.yaml - No parameters. Does not scan for group calendars.

#### Example create event service call

```yaml
service: o365.create_calendar_event
target:
  entity_id:
    - calendar.user_primary
data:
  subject: Clean up the garage
  start: 2023-01-01T12:00:00+0000
  end: 2023-01-01T12:30:00+0000
  body: Remember to also clean out the gutters
  location: 1600 Pennsylvania Ave Nw, Washington, DC 20500
  sensitivity: Normal
  show_as: Busy
  attendees:
    - email: test@example.com
      type: Required
```

## To-Do Services

These O365 services must be targeted at a `todo` sensor. Alternatively the core To-Do services (e.g.`todo.add_item`) can be used. The core services do not support reminder date/time setting. 
The intention is to phase out the O365 services once the core services provide full functionality.

### o365.new_todo
Create a new To-Do - All parameters are shown in the available parameter list on the Developer Tools/Services tab.
### o365.update_todo
Update a To-Do - All parameters are shown in the available parameter list on the Developer Tools/Services tab.
### o365.delete_todo
Delete a To-Do - All parameters are shown in the available parameter list on the Developer Tools/Services tab.
### o365.complete_todo
(Un)complete a To-Do - All parameters are shown in the available parameter list on the Developer Tools/Services tab.
### o365.scan_for_todo_lists
Scan for new for to-do lists and add to o365_tasks.yaml - No parameters.

#### Example create to-do service call

```yaml
service: o365.new_todo
target:
  entity_id: todo.hass_primary
data:
  subject: Pick up the mail
  description: Walk to the post box and collect the mail
  due: 2023-01-01     # Note that due only takes a date, not a time
  reminder: 2023-01-01T12:00:00+0000
```

## Auto reply Services

These services must be targeted at `auto_reply` sensors. 

### o365.set_auto_reply
Schedule the auto reply - All parameters are shown in the available parameter list on the Developer Tools/Services tab.
### o365.disable_auto_reply
Disable the auto reply - All parameters are shown in the available parameter list on the Developer Tools/Services tab.

#### Example enable auto reply service call

```yaml
service: o365.auto_reply_enable
target:
  entity_id: sensor.inbox
data:
  external_reply: I'm currently on holliday, please email Bob for answers
  internal_reply: I'm currently on holliday
  start: 2023-01-01T12:00:00+0000
  end: 2023-01-02T12:30:00+0000
  external_audience: all
```

## Chat Services

These services must be targeted at a `chat` sensor. 

### o365.send_chat_message
Send message to specified chat - All parameters are shown in the available parameter list on the Developer Tools/Services tab.

#### Example send chat message service call

```yaml
service: o365.send_chat_message
target:
  entity_id: sensor.roger_chats
data:
  chat_id: xxxxxxxxxxxxxxxxxxxxxxxxx
  message: Hello world
```

## Status Services

These services must be targeted at a `status` sensor. They can only target the logged-in user's status.

### o365.update_user_status
Update Teams status for the logged in client. This will not override a status that is set via the MS Teams client. Allowable pairings of availability and activity are show in the [MS Graph Documentation](https://learn.microsoft.com/en-us/graph/api/presence-setpresence?view=graph-rest-1.0&tabs=http#request-body). The expiration/duration field is also documented on the same page. It defaults to 5 minutes.

#### Example update status service call

```yaml
service: o365.update_user_status
data:
  availability: Busy
  activity: InACall
  expiration_duration: PT1H
target:
  entity_id: sensor.roger_teams_status
```


https://learn.microsoft.com/en-us/graph/api/presence-setpresence?view=graph-rest-1.0&tabs=http#request-body