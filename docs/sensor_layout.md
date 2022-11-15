---
title: Sensor Layout
nav_order: 6
---

# Sensor layout
The status of the calendar sensor indicates (on/off) whether there is an event on at the current time. The `message`, `all_day`, `start_time`, `end_time`, `location`, `description` and `offset_reached` attributes provide details of the current of next event. A non all-day event is favoured over all_day events.

The `data` attribute provides an array of events for the period defined by the `start_offset` and `end_offset` in `o365_calendars_<account_name>.yaml`. Individual array elements can be accessed using the template notation `states.calendar.calendar_<account_name>.attributes.data[0...n]`.

## Task/ToDo Sensor

One sensor is created for each task list on the user account. Each sensor shows the number of incomplete tasks as the status of the sensor. The `all_tasks` attribute is an array of incomplete tasks. The `'overdue_tasks` attribute shows any tasks which have a due date and are overdue as an array.
