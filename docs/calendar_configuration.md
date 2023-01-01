---
title: Calendar Configuration
nav_order: 6
---

# Calendar configuration
The integration uses an external `o365_calendars_<account_name>.yaml` file (or `o365_calendars.yaml` for the secondary (deprecated) configuration format) which is stored in the `o365_storage` directory.
## Example Calendar yaml:
```yaml
- cal_id: xxxx
  entities:
  - device_id: work_calendar
    end_offset: 24
    name: My Work Calendar
    start_offset: 0
    track: true

- cal_id: xxxx
  entities:
  - device_id: birthdays
    end_offset: 24
    name: Birthdays
    start_offset: 0
    track: true
```

### Calendar yaml configuration variables

Key | Type | Required | Description
-- | -- | -- | --
`cal_id` | `string` | `True` | O365 generated unique ID, DO NOT CHANGE
`entities` | `list<entity>` | `True` | List of entities (see below) to generate from this calendar

### Entity configuration

Key | Type | Required | Description
-- | -- | -- | --
`device_id` | `string` | `True` | The entity_id will be "calendar.{device_id}"
`name` | `string` | `True` | The name of your sensor that you’ll see in the frontend.
`track` | `boolean` | `True` | **True**=Create calendar entity. False=Don't create entity
`search` | `string` | `False` | Only get events if subject contains this string
`start_offset` | `integer` | `False` | Number of hours to offset the start time to search for events for (negative numbers to offset into the past).
`end_offset` | `integer` | `False` | Number of hours to offset the end time to search for events for (negative numbers to offset into the past).

## Group calendars

The integration supports Group calendars in a fairly simple form. The below are the constraints.
* This gets the default calendar for the group.
* There is no discovery. You will need to find them in the MS Graph api. Using the MS Graph API you can call https://graph.microsoft.com/v1.0/me/transitiveMemberOf/microsoft.graph.group to get the groups. You will need the relevant group's `id` for configuration purposes, see below
* You can create events using the standard service, but you cannot modify/delete/respond to them.

To configure a Group Calendar, add an extra section to `o365_calendars_<account_name>.yaml`. Set `cal_id` to `group:xxxxxxxxxxxxxxx` using the ID you found via the api above. Make sure to set the `device_id` to something unique.

```yaml
  - cal_id: group:xxxx
    entities:
    - device_id: group_calendar
      end_offset: 24
      name: Group Calendar
      start_offset: 0
      track: true
  ```
