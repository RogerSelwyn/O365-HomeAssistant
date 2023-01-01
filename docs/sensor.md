---
title: Sensors
nav_order: 8
---

# Sensors
## Calendar Sensor
The status of the calendar sensor indicates (on/off) whether there is an event on at the current time. The `message`, `all_day`, `start_time`, `end_time`, `location`, `description` and `offset_reached` attributes provide details of the current of next event. A non-all-day event is favoured over all_day events.

The `data` attribute provides an array of events for the period defined by the `start_offset` and `end_offset` in `o365_calendars_<account_name>.yaml`. Individual array elements can be accessed using the template notation `states.calendar.calendar_<account_name>.attributes.data[0...n]`.

## Teams Status Sensor
The Teams Status sensor shows whether the user is online or offline on Teams.

## Teams Chat Sensor
Shows the latest chat found on MS Teams. Shows the date and time as the status of the sensor, plus content, ID and importance of the chat item.

## Task/To-Do Sensor

One sensor is created for each task list on the user account. Each sensor shows the number of incomplete tasks as the status of the sensor. The `all_tasks` attribute is an array of incomplete tasks. The `'overdue_tasks` attribute shows any tasks which have a due date and are overdue as an array.

### Display
In order to show the tasks in the front end, a markdown card can be used. The following is an example that allows you to display a bulleted list subject from the `all_tasks` array of tasks.

```yaml
type: markdown
title: Tasks
content: |-
  {% for task in state_attr('sensor.tasks_sc_personal', 'all_tasks') -%}
  - {{ task['subject'] }}
  {% endfor %}
```