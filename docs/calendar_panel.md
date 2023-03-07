---
title: Calendar Panel
nav_order: 11
---

Creation and deletion of events is possible via the Calendar Panel introduced in HA 2023.1. This UI allows you to create recurring events, which is not possible via the HA services methods. However, it is not possible to delete all occurrences of a recurring event through this method due to the way recurring events are handled in O365 compared to the iCal standard (which underpins the HA calendars). Either delete individually, or via an alternate method such as Outlook.