---
title: Tasks Configuration
nav_order: 7
---

# Calendar configuration
The integration uses an external `o365_tasks_<account_name>.yaml` file which is stored in the `o365_storage` directory.
## Example Tasks yaml:
```yaml

- name: Tasks
  task_list_id: xxxx
  track: false

- name: HASS
  task_list_id: xxxx
  track: true
```

### Tasks yaml configuration variables

Key | Type | Required | Description
-- | -- | -- | --
`task_list_id` | `string` | `True` | O365 generated unique ID, DO NOT CHANGE
`name` | `string` | `True` | The name of your sensor that you’ll see in the frontend.
`track` | `boolean` | `False` | **True**=Create sensor entity. False=Don't create entity
`show_completed` | `boolean` | `False` | **False**=Don't show completed items. True=Show completed items
