---
title: Sensors
nav_order: 8
---

# Sensors
## Calendar Sensor
The status of the calendar sensor indicates (on/off) whether there is an event on at the current time. The `message`, `all_day`, `start_time`, `end_time`, `location`, `description` and `offset_reached` attributes provide details of the current of next event. A non-all-day event is favoured over all_day events.

The `data` attribute provides an array of events for the period defined by the `start_offset` and `end_offset` in `o365_calendars_<account_name>.yaml`. Individual array elements can be accessed using the template notation `states.calendar.calendar_<account_name>.attributes.data[0...n]`.

## Teams Status Sensor
The Teams Status sensor shows the user's current status on Teams:

* `available`
* `away`
* `beRightBack`
* `busy`
* `doNotDisturb`
* `inACall`
* `inAConferenceCall`
* `inactive`
* `inAMeeting`
* `offline`
* `offWork`
* `outOfOffice`
* `presenceUnknown`
* `presenting`
* `urgentInterruptionsOnly`

## Teams Chat Sensor
Shows the latest chat found on MS Teams. Shows the date and time as the status of the sensor, plus content, ID and importance of the chat item.

The `data` attribute provides an array of chats (max 20), including chat_id and supporting information. Individual array elements can be accessed using the template notation `states.sensor.<sensor_name>.attributes.data[0...n]`.

## Auto Reply Sensor
Shows the current auto reply settings for your account. Supports the enabling and disabling of auto reply. Note that all attributes are displayed even if auto reply is disabled for reference purposes.
